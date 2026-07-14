"""backtest — forward calibration of the breakdown score.

This is the falsifiable test of the thesis (THESIS.md §6). It walks the panel
forward, re-deriving each signal from ONLY the information available on the
filing date, then grades it against a realized forward return the score never
saw. Three disciplines are enforced in code, because every one of them is a way
to lie to yourself:

  * As-filed only. A snapshot with `restated=True`, or one whose `reported_at`
    is after the evaluation date, is invisible at that date.
  * Score forward, don't fit backward. S_t uses `<= t` data; the return over
    [t, t+h] grades it and is never fed back in.
  * Stratify by H(N). The thesis makes a falsifiable prediction: low-entropy
    benign consensus should show more persistent forward drift than a divided
    narrative. The report puts that side by side so it can be refuted.

The harness is provider-agnostic — hand it as-filed snapshots, narrative
events, and a price series. Stdlib only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from .filing_ingestor import FundamentalSnapshot
from .models import NarrativeEvent, SignalState
from .narrative_monitor import extract_claims, narrative_intensity
from .signal_engine import SignalEngine

# entropy strata (must line up with expected_decay bands in the engine)
ENTROPY_BUCKETS = (("low", 0.40), ("medium", 0.75), ("high", 1.01))


def _to_date(text: str) -> date | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


class PriceSeries:
    """Per-ticker daily closes with forward-return lookup.

    `forward_return` enters at the first close on/after the evaluation date and
    exits at the first close on/after date + horizon. Both must exist, or it
    returns None — a missing exit price is never silently treated as zero.
    """

    def __init__(self) -> None:
        self._by_ticker: dict[str, list[tuple[date, float]]] = {}

    def add(self, ticker: str, day: date, close: float) -> None:
        self._by_ticker.setdefault(ticker, []).append((day, close))

    def finalize(self) -> "PriceSeries":
        for series in self._by_ticker.values():
            series.sort(key=lambda dc: dc[0])
        return self

    def _price_on_or_after(self, ticker: str, day: date) -> float | None:
        for d, close in self._by_ticker.get(ticker, ()):
            if d >= day:
                return close
        return None

    def forward_return(
        self, ticker: str, as_of: date, horizon_days: int
    ) -> float | None:
        entry = self._price_on_or_after(ticker, as_of)
        exit_ = self._price_on_or_after(ticker, as_of + timedelta(days=horizon_days))
        if entry is None or exit_ is None or entry == 0:
            return None
        return exit_ / entry - 1.0


class CsvPriceSource:
    """Loads a PriceSeries from a CSV: ticker,date,close."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> PriceSeries:
        import csv

        series = PriceSeries()
        with self.path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                d = _to_date(row["date"])
                if d is not None:
                    series.add(row["ticker"].strip(), d, float(row["close"]))
        return series.finalize()


@dataclass(frozen=True)
class Observation:
    ticker: str
    as_of: str
    state: str
    breakdown_score: float
    narrative_entropy: float
    confidence: float
    execution_eligible: bool
    forward_return: float | None


@dataclass
class BacktestReport:
    horizon_days: int
    observations: list[Observation] = field(default_factory=list)
    by_state: dict[str, dict[str, float]] = field(default_factory=dict)
    by_entropy: dict[str, dict[str, float]] = field(default_factory=dict)
    information_coefficient: float = 0.0
    execution_mean_return: float | None = None

    def render(self) -> str:
        lines = [
            f"Backtest — horizon {self.horizon_days}d, "
            f"{len(self.observations)} observations",
            "",
            "By state:            n   mean_fwd   hit_rate",
        ]
        for state, s in self.by_state.items():
            lines.append(
                f"  {state:<20}{int(s['count']):>3}  {s['mean_return']:>8.2%}  "
                f"{s['hit_rate']:>8.0%}"
            )
        lines += ["", "Deterioration by narrative entropy (thesis test):",
                  "  bucket        n   mean_fwd"]
        for bucket, s in self.by_entropy.items():
            lines.append(
                f"  {bucket:<12}{int(s['count']):>3}  {s['mean_return']:>8.2%}"
            )
        lines += [
            "",
            f"Information coefficient (score vs -fwd return): "
            f"{self.information_coefficient:+.3f}",
        ]
        if self.execution_mean_return is not None:
            lines.append(
                f"Execution-eligible mean forward return: "
                f"{self.execution_mean_return:+.2%}"
            )
        return "\n".join(lines)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if vx == 0 or vy == 0:
        return 0.0
    return cov / (vx * vy)


def _entropy_bucket(h: float) -> str:
    for name, ceiling in ENTROPY_BUCKETS:
        if h < ceiling:
            return name
    return "high"


def run_backtest(
    filings: Sequence[FundamentalSnapshot],
    narratives: Sequence[NarrativeEvent],
    prices: PriceSeries,
    horizon_days: int = 90,
    engine: SignalEngine | None = None,
    min_history: int = 3,
) -> BacktestReport:
    """Walk the panel forward and grade each point-in-time signal."""
    engine = engine or SignalEngine()
    tickers = sorted({s.ticker for s in filings})
    observations: list[Observation] = []

    for ticker in tickers:
        t_filings = [s for s in filings if s.ticker == ticker]
        t_narr = [e for e in narratives if e.ticker == ticker]

        # each filing date is one evaluation point
        eval_dates = sorted(
            {d for s in t_filings if (d := _to_date(s.reported_at)) is not None}
        )
        for t in eval_dates:
            # POINT-IN-TIME: as-filed only, nothing filed after t, no restatements
            available = [
                s for s in t_filings
                if (rd := _to_date(s.reported_at)) is not None
                and rd <= t
                and not s.restated
            ]
            if len(available) < min_history:
                continue
            claims = extract_claims(
                [e for e in t_narr if (_to_date(e.event_time) or date.max) <= t]
            )
            signal = engine.evaluate(
                available, claims, narrative_intensity(claims)
            )
            fwd = prices.forward_return(ticker, t, horizon_days)
            observations.append(
                Observation(
                    ticker=ticker,
                    as_of=t.isoformat(),
                    state=signal.state.value,
                    breakdown_score=signal.breakdown_score,
                    narrative_entropy=signal.narrative_entropy,
                    confidence=signal.confidence,
                    execution_eligible=signal.execution_eligible,
                    forward_return=fwd,
                )
            )

    return _summarize(observations, horizon_days)


def _summarize(
    observations: Sequence[Observation], horizon_days: int
) -> BacktestReport:
    report = BacktestReport(horizon_days=horizon_days, observations=list(observations))
    graded = [o for o in observations if o.forward_return is not None]

    # by state: count, mean forward return, directional hit rate
    deterioration = {
        SignalState.CONFIRMED_DETERIORATION.value,
        SignalState.EARLY_EVIDENCE.value,
    }
    for state in {o.state for o in observations}:
        rows = [o for o in graded if o.state == state]
        if not rows:
            report.by_state[state] = {"count": 0, "mean_return": 0.0, "hit_rate": 0.0}
            continue
        mean_r = sum(o.forward_return for o in rows) / len(rows)
        if state in deterioration:
            hits = sum(o.forward_return < 0 for o in rows)
        elif state == SignalState.IMPROVING.value:
            hits = sum(o.forward_return > 0 for o in rows)
        else:
            hits = 0
        report.by_state[state] = {
            "count": len(rows),
            "mean_return": mean_r,
            "hit_rate": hits / len(rows),
        }

    # deterioration stratified by narrative entropy — the thesis prediction
    det_graded = [
        o for o in graded
        if o.state in deterioration and o.breakdown_score > 0
    ]
    for bucket, _ in ENTROPY_BUCKETS:
        rows = [o for o in det_graded if _entropy_bucket(o.narrative_entropy) == bucket]
        report.by_entropy[bucket] = {
            "count": len(rows),
            "mean_return": (
                sum(o.forward_return for o in rows) / len(rows) if rows else 0.0
            ),
        }

    # information coefficient: higher score should predict more negative return
    if len(graded) >= 2:
        report.information_coefficient = _pearson(
            [o.breakdown_score for o in graded],
            [-o.forward_return for o in graded],
        )

    exec_rows = [o for o in graded if o.execution_eligible]
    if exec_rows:
        report.execution_mean_return = sum(
            o.forward_return for o in exec_rows
        ) / len(exec_rows)

    return report
