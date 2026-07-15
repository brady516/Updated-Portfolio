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
from narrative_monitor.edgar import EdgarClient, EdgarFilingSource

FIXTURE = Path(__file__).parent / "fixtures" / "edgar_companyfacts.json"


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
