#!/usr/bin/env python3
"""Forward-calibration harness on a SYNTHETIC panel.

IMPORTANT: the data here is fabricated with a known effect baked in, so you can
watch the harness *recover* it end to end. This validates the harness and its
point-in-time discipline — it does NOT validate the thesis. Real validation
needs real as-filed filings, a real parrot-layer feed, and real prices.

The embedded effect mirrors the thesis prediction:
  * low-entropy breakdowns  (unanimous benign narrative) -> persistent decline,
  * high-entropy breakdowns  (split narrative)           -> fast mean-reversion,
  * healthy names            (no reporting divergence)    -> drift up.

If the harness is honest, the low-entropy bucket should print the most negative
forward return and the information coefficient should be positive.

    python3 run_backtest_demo.py
"""

from __future__ import annotations

from datetime import date, timedelta

from narrative_monitor import FundamentalSnapshot, NarrativeEvent
from narrative_monitor.backtest import PriceSeries, run_backtest

# quarter -> (reported_at date)
QUARTERS = [
    ("2024-Q1", date(2024, 4, 22)),
    ("2024-Q2", date(2024, 7, 22)),
    ("2024-Q3", date(2024, 10, 22)),
    ("2024-Q4", date(2025, 1, 27)),
    ("2025-Q1", date(2025, 4, 21)),
    ("2025-Q2", date(2025, 7, 21)),
    ("2025-Q3", date(2025, 10, 20)),
    ("2025-Q4", date(2026, 1, 26)),
    ("2026-Q1", date(2026, 4, 20)),
]
ONSET = date(2025, 4, 21)  # deterioration begins with the 2025-Q1 print

# healthy seasonal baseline (revenue, fcf) by quarter suffix
BASE = {"Q1": (15.0, 2.2), "Q2": (16.0, 2.8), "Q3": (15.2, 2.3), "Q4": (18.0, 6.2)}
# breakdown FCF, weaker every 2025+ quarter than its 2024 comparable
WEAK_FCF = {"Q1": 1.7, "Q2": 2.1, "Q3": 1.6, "Q4": 4.6}
GUIDANCE = {"2025-Q2": 12.0, "2025-Q3": 10.5, "2025-Q4": 9.5, "2026-Q1": 9.0}


def _snapshots(ticker: str, breakdown: bool) -> list[FundamentalSnapshot]:
    out: list[FundamentalSnapshot] = []
    for period, rep in QUARTERS:
        q = period[-2:]
        year = int(period[:4])
        rev, fcf = BASE[q]
        gm = 0.560
        if breakdown and year >= 2025:
            fcf = WEAK_FCF[q]
            gm = 0.545
        capex = 0.55 if q == "Q4" else 0.40
        out.append(
            FundamentalSnapshot(
                ticker=ticker,
                period=period,
                revenue=rev + (0.3 if breakdown and year >= 2025 else 0.0),
                free_cash_flow=fcf,
                operating_cash_flow=fcf + 0.7,
                capex=capex,
                gross_margin=gm,
                receivables=7.0,
                fy_fcf_guidance=GUIDANCE.get(period) if breakdown else (
                    13.0 if period in GUIDANCE else None
                ),
                reported_at=rep.isoformat(),
            )
        )
    return out


def _narrative(ticker: str, split: bool) -> list[NarrativeEvent]:
    """Attach a contemporaneous narrative at each deteriorating quarter."""
    benign = "deal timing, ai investment, budget reallocation, pipeline remains strong"
    admit = "demand environment and execution issue"
    events: list[NarrativeEvent] = []
    for period, rep in QUARTERS:
        if period not in GUIDANCE:  # only the 2025-Q2..2026-Q1 window
            continue
        t = f"{rep.isoformat()}T08:00:00-04:00"
        for i in range(3):  # three benign sources always
            events.append(
                NarrativeEvent(ticker, t, f"{ticker} update", benign,
                               f"benign_{i}", "sell_side")
            )
        if split:  # plus three admitting sources -> high entropy
            for i in range(3):
                events.append(
                    NarrativeEvent(ticker, t, f"{ticker} downgrade", admit,
                                   f"admit_{i}", "sell_side")
                )
    return events


def _price(ticker: str, regime: str, start: date, end: date) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    d = start
    while d <= end:
        x = (d - ONSET).days
        if regime == "healthy":
            px = 100.0 * (1 + 0.08 * (d - start).days / 365)
        elif regime == "low_breakdown":
            px = 100.0 if x <= 0 else 100.0 - 40.0 * (x / 365)
        else:  # high_breakdown: a dip fully inside the horizon, then recovers
            pulse = max(0.0, 1 - abs(x - 30) / 30) if 0 <= x <= 60 else 0.0
            px = 100.0 - 25.0 * pulse
        out.append((d, round(px, 2)))
        d += timedelta(days=7)
    return out


def main() -> None:
    tickers = {
        "LOWA": "low_breakdown", "LOWB": "low_breakdown",
        "HIA": "high_breakdown", "HIB": "high_breakdown",
        "OKA": "healthy", "OKB": "healthy",
    }
    filings: list[FundamentalSnapshot] = []
    narratives: list[NarrativeEvent] = []
    prices = PriceSeries()
    start, end = date(2024, 1, 1), date(2026, 8, 15)

    for ticker, regime in tickers.items():
        breakdown = regime != "healthy"
        filings += _snapshots(ticker, breakdown)
        if breakdown:
            narratives += _narrative(ticker, split=regime == "high_breakdown")
        for day, close in _price(ticker, regime, start, end):
            prices.add(ticker, day, close)
    prices.finalize()

    report = run_backtest(filings, narratives, prices, horizon_days=90)
    print("SYNTHETIC DATA — validates the harness, not the thesis.\n")
    print(report.render())


if __name__ == "__main__":
    main()
