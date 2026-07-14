"""Tests for the sector ChannelSets — banks and REITs.

    python3 -m unittest discover -s tests

Proves the same engine reads each sector's microstructure: a benign narrative
over a breaking bank/REIT filing confirms through the right channels, healthy
credit does NOT fire (no false positives), and sector selection is by field.
"""

from __future__ import annotations

import unittest

from narrative_monitor import (
    FundamentalSnapshot,
    SignalEngine,
    SignalState,
)
from narrative_monitor.channels import channel_set_for

QUARTERS = [
    ("2024-Q1", "2024-04-22"), ("2024-Q2", "2024-07-22"),
    ("2024-Q3", "2024-10-22"), ("2024-Q4", "2025-01-27"),
    ("2025-Q1", "2025-04-21"), ("2025-Q2", "2025-07-21"),
    ("2025-Q3", "2025-10-20"), ("2025-Q4", "2026-01-26"),
    ("2026-Q1", "2026-04-20"),
]


def _panel(sector: str, series: dict, guidance_key=None, guidance=None) -> list:
    guidance = guidance or {}
    out = []
    for i, (period, rep) in enumerate(QUARTERS):
        items = {k: v[i] for k, v in series.items()}
        if guidance_key and period in guidance:
            items[guidance_key] = guidance[period]
        out.append(FundamentalSnapshot(
            ticker="T", period=period, revenue=0.0, free_cash_flow=0.0,
            operating_cash_flow=0.0, capex=0.0, reported_at=rep,
            sector=sector, line_items=items,
        ))
    return out


def _broken_bank() -> list:
    return _panel("financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.22,.22,.35,.40,.50,.55,.60],
        "provision_for_credit_losses":[.25,.25,.25,.25,.30,.32,.35,.40,.35],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.4,1.35,1.3,1.25,1.2],
        "nonperforming_assets":       [1.0,1.0,1.1,1.1,1.5,1.7,1.9,2.1,2.3],
        "net_interest_margin":        [.035,.035,.0348,.0348,.0335,.033,.0325,.032,.031],
        "tangible_book_value_per_share":[50,50,50,50,49,48,47,46,45],
        "net_income":                 [3.0,3.0,3.1,3.2,2.5,2.3,2.1,1.9,1.6],
    }, "fy_nii_guidance",
       {"2025-Q2":25.0,"2025-Q3":24.0,"2025-Q4":23.0,"2026-Q1":22.0})


def _healthy_bank() -> list:
    return _panel("financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.20,.20,.19,.19,.18,.18,.17],
        "provision_for_credit_losses":[.25,.25,.25,.25,.25,.25,.25,.25,.25],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.55,1.57,1.6,1.62,1.65],
        "nonperforming_assets":       [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
        "net_interest_margin":        [.035,.035,.035,.035,.035,.035,.035,.035,.035],
        "tangible_book_value_per_share":[50,50,51,51,52,53,54,55,56],
        "net_income":                 [3.0,3.0,3.1,3.2,3.3,3.4,3.5,3.6,3.7],
    })


def _broken_reit() -> list:
    return _panel("reit", {
        "ffo":                        [2.0,2.1,2.0,2.3,2.0,2.1,2.0,2.3,2.0],
        "affo":                       [1.6,1.7,1.6,1.9,1.3,1.3,1.2,1.4,1.1],
        "same_store_noi":             [10,10.2,10.1,10.3,9.9,9.8,9.9,9.9,9.2],
        "straight_line_rent_receivable":[5,5,5,5,5.5,5.8,6.0,6.3,6.8],
        "capitalized_interest":       [.3,.3,.3,.3,.4,.45,.5,.55,.6],
        "dividend_per_share":         [.4]*9,
        "affo_per_share":             [.55,.58,.55,.62,.45,.44,.42,.46,.35],
    }, "fy_affo_guidance",
       {"2025-Q2":1.6,"2025-Q3":1.5,"2025-Q4":1.4,"2026-Q1":1.3})


class SectorSelectionTests(unittest.TestCase):
    def test_registry_routes_by_sector(self) -> None:
        self.assertEqual(channel_set_for("financial").sector, "financial")
        self.assertEqual(channel_set_for("reit").sector, "reit")
        self.assertEqual(channel_set_for("unknown").sector, "industrial")

    def test_signal_reports_its_sector(self) -> None:
        sig = SignalEngine().evaluate(_broken_bank(), claims=[])
        self.assertEqual(sig.metrics["sector"], "financial")


class BankChannelTests(unittest.TestCase):
    def test_reserve_inadequacy_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_bank(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("reserve_release_below_chargeoffs", "allowance_coverage_decline",
                    "npa_outrun_loans", "nim_two_period_compression"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_aoci_buildup_raises_reporting_entropy(self) -> None:
        panel = _broken_bank()
        # add growing unrealized securities losses vs equity (the SVB tell)
        aoci = [1, 1, 1, 1, 3, 4, 5, 6, 7]
        panel = [FundamentalSnapshot(**{**s.__dict__,
                 "line_items": {**s.line_items, "aoci_unrealized_loss": aoci[i],
                                "tangible_common_equity": 40.0}})
                 for i, s in enumerate(panel)]
        sig = SignalEngine().evaluate(panel, claims=[])
        self.assertGreater(sig.reporting_entropy, 0.0)

    def test_healthy_bank_does_not_fire(self) -> None:
        sig = SignalEngine().evaluate(_healthy_bank(), claims=[])
        self.assertEqual(sig.metrics["reporting_divergence"], 0.0)
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class ReitChannelTests(unittest.TestCase):
    def test_affo_wedge_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_reit(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("ttm_affo_decline", "affo_wedge_widening",
                    "same_store_noi_two_period_decline", "dividend_above_affo"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_primary_ttm_is_affo_not_fcf(self) -> None:
        # REIT execution gate keys off AFFO's TTM window, not FCF.
        sig = SignalEngine().evaluate(_broken_reit(), claims=[])
        self.assertIsNotNone(sig.metrics["primary_ttm"])


if __name__ == "__main__":
    unittest.main()
