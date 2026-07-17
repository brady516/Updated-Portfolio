"""Tests for the filing-text extractor — the non-XBRL sector tells.

All offline, against representative filing snippets. Verifies the extractor pulls
FFO/AFFO/PV-10/PIK/NAV with the right scale and sign, returns the source text for
audit, strips HTML, and merges into snapshots per period — and that a REIT built
from text-extracted line items then confirms through its own channels.
"""

from __future__ import annotations

import unittest

from narrative_monitor import (
    FundamentalSnapshot,
    SignalEngine,
    SignalState,
    apply_text_line_items,
    extract_line_items,
    to_text,
)
from narrative_monitor.filing_text import extract, REIT_METRICS, BDC_METRICS


REIT_TEXT = (
    "During the quarter, Funds from operations were $412.5 million, or $1.85 per "
    "diluted share. Adjusted funds from operations (AFFO) totaled $360.0 million, "
    "or $1.62 per diluted share. Same-store net operating income was $520.3 "
    "million. Portfolio occupancy was 92.4% at quarter end. Dividends declared "
    "per share were $1.90."
)
ENERGY_TEXT = (
    "The standardized measure of discounted future net cash flows (PV-10) was "
    "$3,250 million. Our reserve replacement ratio of 78% reflected fewer "
    "completions. Cash netback per boe was $18.40."
)
BDC_TEXT = (
    "Net asset value per share was $9.02, down from the prior quarter. Net "
    "investment income per share was $0.27. Payment-in-kind (PIK) income of $18.4 "
    "million rose as a share of total investment income. Non-accruals represented "
    "6.0% of the portfolio at fair value."
)


class ReitExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.items = extract_line_items("reit", REIT_TEXT)

    def test_ffo_and_affo_totals_scaled_to_dollars(self) -> None:
        self.assertAlmostEqual(self.items["ffo"], 412_500_000.0)
        self.assertAlmostEqual(self.items["affo"], 360_000_000.0)

    def test_per_share_values_not_confused_with_totals(self) -> None:
        self.assertAlmostEqual(self.items["ffo_per_share"], 1.85)
        self.assertAlmostEqual(self.items["affo_per_share"], 1.62)
        self.assertAlmostEqual(self.items["dividend_per_share"], 1.90)

    def test_occupancy_percent_to_ratio(self) -> None:
        self.assertAlmostEqual(self.items["occupancy"], 0.924)

    def test_extraction_carries_source_context(self) -> None:
        exts = {e.metric: e for e in extract(REIT_TEXT, REIT_METRICS)}
        self.assertIn("funds from operations", exts["ffo_per_share"].context.lower())


class EnergyBdcExtractionTests(unittest.TestCase):
    def test_energy_pv10_and_rrr(self) -> None:
        items = extract_line_items("energy", ENERGY_TEXT)
        self.assertAlmostEqual(items["pv10"], 3_250_000_000.0)
        self.assertAlmostEqual(items["reserve_replacement_ratio"], 0.78)

    def test_bdc_pik_and_nav(self) -> None:
        items = extract_line_items("bdc", BDC_TEXT)
        self.assertAlmostEqual(items["nav_per_share"], 9.02)
        self.assertAlmostEqual(items["pik_income"], 18_400_000.0)
        self.assertAlmostEqual(items["non_accrual_rate"], 0.06)
        exts = {e.metric: e for e in extract(BDC_TEXT, BDC_METRICS)}
        self.assertIn("pik", exts["pik_income"].context.lower())


class HtmlAndMergeTests(unittest.TestCase):
    def test_to_text_strips_html(self) -> None:
        html = "<html><body><p>NAV per share was <b>$9.02</b>.</p>" \
               "<script>ignore()</script></body></html>"
        text = to_text(html)
        self.assertIn("NAV per share was $9.02", text)
        self.assertNotIn("ignore", text)

    def test_apply_merges_per_period_preserving_xbrl(self) -> None:
        snap = FundamentalSnapshot(
            ticker="R", period="2026-Q1", revenue=0.0, free_cash_flow=0.0,
            operating_cash_flow=0.0, capex=0.0, sector="reit",
            line_items={"affo_per_share": 9.99},  # pretend from XBRL: must win
        )
        out = apply_text_line_items([snap], {"2026-Q1": REIT_TEXT})[0]
        self.assertAlmostEqual(out.line_items["ffo"], 412_500_000.0)   # from text
        self.assertAlmostEqual(out.line_items["affo_per_share"], 9.99)  # xbrl preserved


class ReitFromTextConfirmsTests(unittest.TestCase):
    def test_text_extracted_reit_drives_channels(self) -> None:
        # A minimal AFFO-declining series assembled from per-quarter text, then
        # scored by the REIT channels — proving text -> line_items -> signal.
        texts = {}
        snaps = []
        affo = [1.9, 1.9, 1.8, 2.1, 1.4, 1.4, 1.3, 1.5, 1.1]
        ffo = [2.2, 2.2, 2.1, 2.4, 2.2, 2.2, 2.1, 2.4, 2.2]
        periods = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
                   "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1"]
        for i, p in enumerate(periods):
            texts[p] = (f"Funds from operations were ${ffo[i]} million. "
                        f"Adjusted funds from operations were ${affo[i]} million.")
            snaps.append(FundamentalSnapshot(
                ticker="RT", period=p, revenue=0.0, free_cash_flow=0.0,
                operating_cash_flow=0.0, capex=0.0, sector="reit"))
        enriched = apply_text_line_items(snaps, texts)
        sig = SignalEngine().evaluate(enriched, claims=[])
        self.assertEqual(sig.metrics["sector"], "reit")
        self.assertIn("affo_wedge_widening", sig.confirmed_criteria)


if __name__ == "__main__":
    unittest.main()
