"""Tests for the EDGAR FilingSource normalizer — run fully offline.

Exercises the real company-facts XBRL schema against a recorded fixture: discrete
quarter extraction, Q4 = annual - (Q1+Q2+Q3) derivation, FCF = OCF - capex, gross
margin, instant (balance-sheet) alignment, and the as-filed / point-in-time
discipline (earliest-filed value wins over a later amendment). No network.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from narrative_monitor import SignalEngine
from narrative_monitor.edgar import (
    EdgarClient, EdgarFilingSource, sector_from_sic,
)

FIXTURE = Path(__file__).parent / "fixtures" / "edgar_companyfacts.json"


def _dur(concept, rows):
    """rows: (frame, val, filed) -> a us-gaap duration concept node."""
    return {"units": {"USD": [
        {"val": v, "filed": f, "frame": fr} for fr, v, f in rows]}}


def _inst(concept, rows):
    return {"units": {"USD": [
        {"val": v, "filed": f, "frame": fr} for fr, v, f in rows]}}


def _saas_facts():
    Q = ["CY2023Q1", "CY2023Q2", "CY2023Q3"]
    QI = ["CY2023Q1I", "CY2023Q2I", "CY2023Q3I", "CY2023Q4I", "CY2024Q1I"]
    filed = "2024-01-01"
    return {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": _dur("rev", [
            ("CY2023Q1", 100, filed), ("CY2023Q2", 110, filed),
            ("CY2023Q3", 120, filed), ("CY2023", 460, filed),
            ("CY2024Q1", 105, filed)]),
        "NetCashProvidedByUsedInOperatingActivities": _dur("ocf", [
            ("CY2023Q1", 20, filed), ("CY2023Q2", 22, filed),
            ("CY2023Q3", 24, filed), ("CY2023", 90, filed),
            ("CY2024Q1", 21, filed)]),
        "PaymentsToAcquirePropertyPlantAndEquipment": _dur("capex", [
            ("CY2023Q1", 2, filed), ("CY2023Q2", 2, filed),
            ("CY2023Q3", 2, filed), ("CY2023", 8, filed),
            ("CY2024Q1", 2, filed)]),
        "ContractWithCustomerLiabilityCurrent": _inst("def", [
            ("CY2023Q1I", 200, filed), ("CY2023Q2I", 210, filed),
            ("CY2023Q3I", 215, filed), ("CY2023Q4I", 230, filed),
            ("CY2024Q1I", 225, filed)]),
        "RevenueRemainingPerformanceObligation": _inst("rpo", [
            ("CY2023Q1I", 500, filed), ("CY2023Q2I", 520, filed),
            ("CY2023Q3I", 540, filed), ("CY2023Q4I", 560, filed),
            ("CY2024Q1I", 555, filed)]),
        "ShareBasedCompensation": _dur("sbc", [
            ("CY2023Q1", 15, filed), ("CY2023Q2", 16, filed),
            ("CY2023Q3", 18, filed), ("CY2023", 70, filed),
            ("CY2024Q1", 21, filed)]),
    }}}


class SicRoutingTests(unittest.TestCase):
    def test_sic_maps_to_sector(self) -> None:
        self.assertEqual(sector_from_sic(6022), "financial")   # state bank
        self.assertEqual(sector_from_sic(6798), "reit")
        self.assertEqual(sector_from_sic(6331), "insurance")
        self.assertEqual(sector_from_sic(7372), "saas")
        self.assertEqual(sector_from_sic(1311), "energy")
        self.assertEqual(sector_from_sic(3711), "industrial")  # motor vehicles
        self.assertEqual(sector_from_sic(None), "industrial")


class SaasLiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snaps = {
            s.period: s for s in
            EdgarFilingSource(email="t@x.com").normalize(_saas_facts(), "saasco", "saas")
        }

    def test_billings_derived_from_revenue_and_deferred(self) -> None:
        # billings = revenue + change in deferred revenue
        self.assertAlmostEqual(self.snaps["2023-Q2"].line_items["billings"], 120.0)  # 110 + (210-200)
        self.assertAlmostEqual(self.snaps["2024-Q1"].line_items["billings"], 100.0)  # 105 + (225-230)

    def test_crpo_and_sbc_populated(self) -> None:
        q = self.snaps["2023-Q2"]
        self.assertEqual(q.sector, "saas")
        self.assertAlmostEqual(q.line_items["crpo"], 520.0)
        self.assertAlmostEqual(q.line_items["sbc_pct_revenue"], 16 / 110)

    def test_saas_snapshots_route_to_saas_channels(self) -> None:
        sig = SignalEngine().evaluate(list(self.snaps.values()), claims=[])
        self.assertEqual(sig.metrics["sector"], "saas")


class EdgarNormalizeTests(unittest.TestCase):
    def setUp(self) -> None:
        facts = json.loads(FIXTURE.read_text())
        self.snaps = {
            s.period: s for s in
            EdgarFilingSource(email="t@example.com").normalize(facts, "testco")
        }

    def test_discrete_quarters_and_derived_q4(self) -> None:
        self.assertEqual(
            sorted(self.snaps), ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1"]
        )
        # Q4 derived from annual (460) minus Q1+Q2+Q3 (100+110+120)
        self.assertAlmostEqual(self.snaps["2023-Q4"].revenue, 130.0)
        self.assertAlmostEqual(self.snaps["2023-Q4"].operating_cash_flow, 27.0)
        self.assertAlmostEqual(self.snaps["2023-Q4"].capex, 10.0)

    def test_as_filed_earliest_wins_over_amendment(self) -> None:
        # Q1 revenue was amended to 98 later; the as-filed 100 must be used.
        self.assertAlmostEqual(self.snaps["2023-Q1"].revenue, 100.0)
        self.assertEqual(self.snaps["2023-Q1"].reported_at, "2023-04-20")

    def test_derived_fields(self) -> None:
        q1 = self.snaps["2023-Q1"]
        self.assertAlmostEqual(q1.free_cash_flow, 17.0)          # 25 - 8
        self.assertAlmostEqual(q1.gross_margin, 0.40)            # (100-60)/100
        self.assertAlmostEqual(q1.receivables, 40.0)            # instant, quarter-end
        self.assertEqual(q1.sector, "industrial")

    def test_ticker_is_upcased(self) -> None:
        self.assertEqual(self.snaps["2023-Q1"].ticker, "TESTCO")

    def test_normalized_snapshots_drive_the_engine(self) -> None:
        # end-to-end: live-shaped snapshots flow through the engine unchanged
        signal = SignalEngine().evaluate(list(self.snaps.values()), claims=[])
        self.assertEqual(signal.metrics["sector"], "industrial")
        self.assertIsNotNone(signal.state)


class EdgarClientTests(unittest.TestCase):
    def test_client_builds_offline_with_contact_user_agent(self) -> None:
        # Constructing the client does no network I/O; SEC requires a contact UA.
        client = EdgarClient(email="blgallag.bg@gmail.com")
        self.assertIn("blgallag.bg@gmail.com", client.user_agent)


if __name__ == "__main__":
    unittest.main()
