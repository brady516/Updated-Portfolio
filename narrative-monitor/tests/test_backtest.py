"""Tests for the forward-calibration harness.

    python3 -m unittest discover -s tests

The harness is the thesis's own falsification tool, so its integrity is the
thing under test: point-in-time discipline (no restated data, no future
events), correct forward returns, and a report that recovers a known effect.
"""

from __future__ import annotations

import unittest
from datetime import date

from narrative_monitor import (
    FundamentalSnapshot,
    NarrativeEvent,
    PriceSeries,
    run_backtest,
)


def _snap(period: str, rep: str, fcf: float, **kw) -> FundamentalSnapshot:
    base = dict(
        ticker="X", period=period, revenue=15.0, free_cash_flow=fcf,
        operating_cash_flow=fcf + 0.7, capex=0.4, gross_margin=0.56,
        receivables=7.0, reported_at=rep,
    )
    base.update(kw)
    return FundamentalSnapshot(**base)


def _declining_panel() -> list[FundamentalSnapshot]:
    # 2024 healthy, 2025+ weaker YoY, guidance cut -> real divergence.
    rows = [
        _snap("2024-Q1", "2024-04-22", 2.2), _snap("2024-Q2", "2024-07-22", 2.8),
        _snap("2024-Q3", "2024-10-22", 2.3), _snap("2024-Q4", "2025-01-27", 6.2),
        _snap("2025-Q1", "2025-04-21", 1.7, gross_margin=0.545),
        _snap("2025-Q2", "2025-07-21", 2.1, gross_margin=0.545, fy_fcf_guidance=12.0),
        _snap("2025-Q3", "2025-10-20", 1.6, gross_margin=0.545, fy_fcf_guidance=10.5),
        _snap("2025-Q4", "2026-01-26", 4.6, gross_margin=0.545, fy_fcf_guidance=9.5),
        _snap("2026-Q1", "2026-04-20", 1.4, gross_margin=0.545, fy_fcf_guidance=9.0),
    ]
    return rows


def _falling_prices(start_px: float = 100.0) -> PriceSeries:
    prices = PriceSeries()
    d = date(2024, 1, 1)
    from datetime import timedelta
    while d <= date(2026, 8, 15):
        # steady decline from 2025-04 onward
        drop = max(0, (d - date(2025, 4, 21)).days) / 365 * 40
        prices.add("X", d, round(start_px - drop, 2))
        d += timedelta(days=7)
    return prices.finalize()


class ForwardReturnTests(unittest.TestCase):
    def test_forward_return_enters_and_exits_on_or_after(self) -> None:
        p = PriceSeries()
        p.add("X", date(2025, 1, 1), 100.0)
        p.add("X", date(2025, 4, 1), 90.0)
        p.finalize()
        r = p.forward_return("X", date(2025, 1, 1), horizon_days=80)
        self.assertAlmostEqual(r, -0.10, places=4)

    def test_missing_exit_price_returns_none(self) -> None:
        p = PriceSeries()
        p.add("X", date(2025, 1, 1), 100.0)
        p.finalize()
        self.assertIsNone(p.forward_return("X", date(2025, 1, 1), horizon_days=80))


class PointInTimeGuardTests(unittest.TestCase):
    def test_restated_rows_excluded_from_evaluation(self) -> None:
        panel = _declining_panel()
        # mark the whole panel restated -> nothing is as-filed -> no obs graded
        panel = [FundamentalSnapshot(**{**s.__dict__, "restated": True}) for s in panel]
        report = run_backtest(panel, [], _falling_prices(), horizon_days=90)
        self.assertEqual(len(report.observations), 0)

    def test_future_dated_events_are_invisible(self) -> None:
        # A benign event dated in the future must not color earlier signals.
        panel = _declining_panel()
        future = NarrativeEvent(
            "X", "2027-01-01T00:00:00+00:00", "later", "deal timing", "s", "media"
        )
        r_with = run_backtest(panel, [future], _falling_prices(), horizon_days=90)
        r_without = run_backtest(panel, [], _falling_prices(), horizon_days=90)
        # identical signals: the future event never enters any point-in-time set
        self.assertEqual(
            [o.state for o in r_with.observations],
            [o.state for o in r_without.observations],
        )


class RecoveryTests(unittest.TestCase):
    def test_divergence_with_falling_prices_gives_positive_ic(self) -> None:
        report = run_backtest(
            _declining_panel(), [], _falling_prices(), horizon_days=90
        )
        graded = [o for o in report.observations if o.forward_return is not None]
        self.assertTrue(graded)
        # higher breakdown score should track more negative forward returns
        self.assertGreater(report.information_coefficient, 0.0)
        det = [o for o in graded if o.breakdown_score > 0.25]
        self.assertTrue(all(o.forward_return < 0 for o in det))


if __name__ == "__main__":
    unittest.main()
