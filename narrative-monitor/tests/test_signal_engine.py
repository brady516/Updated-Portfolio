"""Tests for the signal engine — run with: python3 -m unittest discover tests

These lock in the two properties that make the engine trustworthy:
  * comparable-period logic (a seasonal Q4->Q1 drop must NOT read as decline),
  * the 3-of-7 confirmation gate (headlines can't manufacture execution).
"""

from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from narrative_monitor import (
    CsvFilingSource,
    FundamentalSnapshot,
    NarrativeEvent,
    Period,
    SignalEngine,
    SignalState,
    execution_gate,
    extract_claims,
    narrative_intensity,
)
from narrative_monitor.store import _to_payload

DATA = Path(__file__).parent.parent / "data" / "ibm_sample.csv"


def _flat(period: str, **overrides) -> FundamentalSnapshot:
    base = dict(
        ticker="TST",
        period=period,
        revenue=14.5,
        free_cash_flow=1.8,
        operating_cash_flow=2.4,
        capex=0.4,
        gross_margin=0.55,
        receivables=7.0,
    )
    base.update(overrides)
    return FundamentalSnapshot(**base)


class PeriodTests(unittest.TestCase):
    def test_comparable_period_is_same_quarter_prior_year(self) -> None:
        self.assertEqual(Period.parse("2026-Q1").prior_year(), Period(2025, 1))
        self.assertEqual(Period.parse("2025-Q4").prior_year(), Period(2024, 4))

    def test_ordering(self) -> None:
        self.assertLess(Period(2025, 4), Period(2026, 1))

    def test_bad_period_raises(self) -> None:
        with self.assertRaises(ValueError):
            Period.parse("2026Q1")


class SeasonalityTests(unittest.TestCase):
    """A sequential Q4->Q1 cash-flow cliff must not read as deterioration."""

    def test_flat_yoy_with_seasonal_sequential_drop(self) -> None:
        # Identical every year; only the sequential Q4->Q1 step looks scary.
        snaps = [
            _flat("2024-Q1"),
            _flat("2024-Q2", revenue=15.5, free_cash_flow=2.5),
            _flat("2024-Q3", revenue=14.7, free_cash_flow=2.0),
            _flat("2024-Q4", revenue=17.5, free_cash_flow=5.6),
            _flat("2025-Q1"),  # same as 2024-Q1: YoY flat
        ]
        signal = SignalEngine().evaluate(snaps, claims=[])
        self.assertEqual(signal.metrics["deterioration_criteria"], 0)
        self.assertIn(
            signal.state,
            {SignalState.INCONCLUSIVE, SignalState.NARRATIVE_ONLY},
        )
        self.assertFalse(signal.execution_eligible)


class IbmDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snaps = CsvFilingSource(DATA).fetch("IBM")

    def test_loud_narrative_only_reaches_early_evidence(self) -> None:
        events = [
            NarrativeEvent(
                "IBM",
                "2026-04-22T08:00:00-04:00",
                "IBM issues soft guidance",
                "deal timing, ai infrastructure, budget reallocation",
                "test",
            )
        ]
        claims = extract_claims(events)
        signal = SignalEngine().evaluate(
            self.snaps, claims, narrative_intensity(claims)
        )
        # two comparable-period criteria confirm: TTM FCF + 2-period FCF margin
        self.assertEqual(signal.state, SignalState.EARLY_EVIDENCE)
        self.assertEqual(signal.metrics["deterioration_criteria"], 2)
        self.assertFalse(signal.execution_eligible)
        self.assertFalse(execution_gate(_to_payload(signal)))

    def test_formal_guidance_cut_confirms_and_becomes_executable(self) -> None:
        # Add the third criterion: a real full-year FCF guidance reduction.
        snaps = list(self.snaps)
        snaps[-1] = dataclasses.replace(snaps[-1], fy_fcf_guidance=12.0)
        signal = SignalEngine().evaluate(snaps, claims=[])
        self.assertEqual(signal.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertGreaterEqual(signal.metrics["deterioration_criteria"], 3)
        self.assertIn("fy_fcf_guidance_cut", signal.confirmed_criteria)
        self.assertTrue(signal.execution_eligible)
        self.assertTrue(execution_gate(_to_payload(signal)))


class GateTests(unittest.TestCase):
    def test_narrative_only_when_no_criteria(self) -> None:
        events = [
            NarrativeEvent(
                "TST", "t", "soft guidance", "macro uncertainty", "test"
            )
        ]
        claims = extract_claims(events)
        # single flat comparable pair -> no criteria can fire
        snaps = [_flat("2025-Q1"), _flat("2026-Q1")]
        signal = SignalEngine().evaluate(
            snaps, claims, narrative_intensity(claims)
        )
        self.assertEqual(signal.state, SignalState.NARRATIVE_ONLY)
        self.assertFalse(signal.execution_eligible)

    def test_gate_rejects_tampered_eligibility(self) -> None:
        # eligible flag set but confidence too low: gate must still reject.
        forged = {
            "execution_eligible": True,
            "state": "confirmed_deterioration",
            "confidence": 0.5,
        }
        self.assertFalse(execution_gate(forged))

    def test_empty_snapshots_raises(self) -> None:
        with self.assertRaises(ValueError):
            SignalEngine().evaluate([], claims=[])


if __name__ == "__main__":
    unittest.main()
