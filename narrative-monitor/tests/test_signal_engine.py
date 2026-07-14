"""Tests for the narrative-breakdown engine.

    python3 -m unittest discover -s tests

Locks in the properties the thesis (THESIS.md) depends on:
  * comparable-period logic (a seasonal Q4->Q1 drop is NOT deterioration),
  * S ∝ divergence (a loud narrative alone can never make a signal),
  * narrative entropy amplifies a benign consensus and forecasts decay,
  * obfuscation (H(R)) feeds divergence but lowers confidence,
  * the point-in-time contract (restated data can't be executable).
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
    narrative_entropy,
    narrative_intensity,
)
from narrative_monitor.entropy import noisy_or, ramp, stance_entropy
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


def _benign_event(source: str = "test") -> NarrativeEvent:
    return NarrativeEvent(
        "IBM",
        "2026-04-22T08:00:00-04:00",
        "IBM issues soft guidance",
        "deal timing, ai infrastructure, budget reallocation, pipeline remains strong",
        source,
    )


class EntropyMathTests(unittest.TestCase):
    def test_ramp_bounds(self) -> None:
        self.assertEqual(ramp(0.0, 0.0, 0.25), 0.0)
        self.assertEqual(ramp(0.25, 0.0, 0.25), 1.0)
        self.assertAlmostEqual(ramp(0.125, 0.0, 0.25), 0.5)

    def test_noisy_or_compounds_but_saturates(self) -> None:
        self.assertAlmostEqual(noisy_or([0.5, 0.5]), 0.75)
        self.assertEqual(noisy_or([0.0, 0.0]), 0.0)  # missing evidence drops out
        self.assertGreater(noisy_or([0.5, 0.5, 0.5]), noisy_or([0.5, 0.5]))

    def test_unanimous_narrative_is_zero_entropy(self) -> None:
        self.assertEqual(stance_entropy({"benign": 5}), 0.0)
        self.assertAlmostEqual(stance_entropy({"benign": 1, "admit": 1}), 1.0)


class PeriodTests(unittest.TestCase):
    def test_comparable_period_is_same_quarter_prior_year(self) -> None:
        self.assertEqual(Period.parse("2026-Q1").prior_year(), Period(2025, 1))
        self.assertEqual(Period.parse("2025-Q4").prior_year(), Period(2024, 4))

    def test_bad_period_raises(self) -> None:
        with self.assertRaises(ValueError):
            Period.parse("2026Q1")


class SeasonalityTests(unittest.TestCase):
    def test_flat_yoy_with_seasonal_sequential_drop(self) -> None:
        snaps = [
            _flat("2024-Q1"),
            _flat("2024-Q2", revenue=15.5, free_cash_flow=2.5),
            _flat("2024-Q3", revenue=14.7, free_cash_flow=2.0),
            _flat("2024-Q4", revenue=17.5, free_cash_flow=5.6),
            _flat("2025-Q1"),  # identical to 2024-Q1: YoY flat
        ]
        signal = SignalEngine().evaluate(snaps, claims=[])
        self.assertEqual(signal.metrics["reporting_divergence"], 0.0)
        self.assertIn(
            signal.state,
            {SignalState.INCONCLUSIVE, SignalState.NARRATIVE_ONLY},
        )
        self.assertFalse(signal.execution_eligible)


class DivergenceInvariantTests(unittest.TestCase):
    def test_loud_narrative_with_flat_reporting_cannot_signal(self) -> None:
        # S ∝ divergence: no reporting divergence -> narrative_only, score 0.
        events = [_benign_event()]
        claims = extract_claims(events)
        snaps = [_flat("2025-Q1"), _flat("2026-Q1")]
        signal = SignalEngine().evaluate(
            snaps, claims, narrative_intensity(claims)
        )
        self.assertEqual(signal.state, SignalState.NARRATIVE_ONLY)
        self.assertEqual(signal.breakdown_score, 0.0)
        self.assertFalse(signal.execution_eligible)


class IbmDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snaps = CsvFilingSource(DATA).fetch("IBM")

    def test_benign_consensus_partial_divergence_is_early_evidence(self) -> None:
        claims = extract_claims([_benign_event()])
        signal = SignalEngine().evaluate(
            self.snaps, claims, narrative_intensity(claims)
        )
        self.assertEqual(signal.state, SignalState.EARLY_EVIDENCE)
        self.assertGreater(signal.breakdown_score, 0.25)
        self.assertLess(signal.breakdown_score, 0.60)
        self.assertEqual(signal.narrative_entropy, 0.0)      # unanimous parrots
        self.assertEqual(signal.expected_decay, "slow")      # tight consensus
        self.assertFalse(signal.execution_eligible)

    def test_guidance_cut_pushes_to_confirmed_and_executable(self) -> None:
        snaps = list(self.snaps)
        snaps[-1] = dataclasses.replace(snaps[-1], fy_fcf_guidance=11.0)
        claims = extract_claims([_benign_event()])
        signal = SignalEngine().evaluate(snaps, claims)
        self.assertEqual(signal.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertGreaterEqual(signal.breakdown_score, 0.60)
        self.assertIn("fy_fcf_guidance_cut", signal.confirmed_criteria)
        self.assertTrue(signal.execution_eligible)
        self.assertTrue(execution_gate(_to_payload(signal)))

    def test_split_narrative_raises_entropy_and_speeds_decay(self) -> None:
        # Same reporting, but the parrot layer disagrees: one benign source,
        # one admitting source -> higher entropy -> lower score, faster decay.
        benign = _benign_event("analyst_a")
        admitting = NarrativeEvent(
            "IBM", "t", "IBM demand environment weak",
            "management cited demand environment and execution issue", "analyst_b",
        )
        unanimous = extract_claims([benign])
        split = extract_claims([benign, admitting])
        self.assertEqual(narrative_entropy(unanimous), 0.0)
        self.assertGreater(narrative_entropy(split), 0.0)

        s_unanimous = SignalEngine().evaluate(self.snaps, unanimous)
        s_split = SignalEngine().evaluate(self.snaps, split)
        self.assertGreater(s_split.narrative_entropy, s_unanimous.narrative_entropy)
        self.assertLessEqual(s_split.breakdown_score, s_unanimous.breakdown_score)
        self.assertEqual(s_split.expected_decay, "fast")


class ObfuscationTests(unittest.TestCase):
    def test_disclosure_withdrawal_adds_divergence_but_cuts_confidence(self) -> None:
        base = CsvFilingSource(DATA).fetch("IBM")
        # prior year reported 5 segments; current reports 2 -> withdrawal.
        snaps = list(base)
        py = snaps[-5]  # 2025-Q1, the comparable period
        snaps[-5] = dataclasses.replace(py, reported_segments=5)
        snaps[-1] = dataclasses.replace(snaps[-1], reported_segments=2)

        clean = SignalEngine().evaluate(base, claims=[])
        obf = SignalEngine().evaluate(snaps, claims=[])
        self.assertGreater(obf.reporting_entropy, 0.0)
        self.assertGreater(obf.metrics["reporting_divergence"],
                           clean.metrics["reporting_divergence"])
        self.assertLess(obf.confidence, clean.confidence)


class PointInTimeTests(unittest.TestCase):
    def test_restated_row_is_never_executable(self) -> None:
        snaps = list(CsvFilingSource(DATA).fetch("IBM"))
        snaps[-1] = dataclasses.replace(
            snaps[-1], fy_fcf_guidance=11.0, restated=True
        )
        signal = SignalEngine().evaluate(snaps, claims=[])
        self.assertEqual(signal.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(signal.execution_eligible)  # restated -> blocked
        self.assertFalse(signal.metrics["as_filed"])

    def test_gate_rejects_low_confidence(self) -> None:
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
