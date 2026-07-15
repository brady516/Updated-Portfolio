#!/usr/bin/env python3
"""The whole system, wired together: every sector's inversion through one gated,
forward-calibrated pipeline.

For each sector it builds three names on the SAME breaking filing:
  * LOW  — a benign, unanimous narrative (H(N)=0) + persistent price decline,
  * HIGH — a split narrative (H(N)=1) + a dip that mean-reverts inside the horizon,
  * OK   — a healthy filing + drift up.

If the machinery is honest, every sector's LOW name confirms and prints a
negative forward return, the HIGH names decay fast (near zero), the healthy names
drift up, the low-entropy bucket is the most negative, and the information
coefficient is positive — the thesis reproduced across all seven microstructures.

SYNTHETIC DATA — validates the wiring, not the thesis.

    python3 run_multisector_backtest.py
"""

from __future__ import annotations

from datetime import date, timedelta

from narrative_monitor import PriceSeries, run_backtest, samples

START, END = date(2024, 1, 1), date(2026, 8, 15)


def _prices(ticker: str, regime: str) -> list[tuple[date, float]]:
    out, d = [], START
    while d <= END:
        x = (d - samples.ONSET).days
        if regime == "ok":
            px = 100.0 * (1 + 0.08 * (d - START).days / 365)
        elif regime == "low":
            px = 100.0 if x <= 0 else 100.0 - 40.0 * (x / 365)
        else:  # high: a dip fully inside the 90d horizon, then recovers
            pulse = max(0.0, 1 - abs(x - 30) / 30) if 0 <= x <= 60 else 0.0
            px = 100.0 - 25.0 * pulse
        out.append((d, round(px, 2)))
        d += timedelta(days=7)
    return out


def main() -> None:
    filings, narratives, prices = [], [], PriceSeries()

    for sector, (breakdown_fn, healthy_fn) in samples.SECTORS.items():
        tag = sector[:4].upper()
        low, high, ok = f"{tag}LO", f"{tag}HI", f"{tag}OK"
        # two breakdowns on the same filing, one healthy counterpart
        filings += breakdown_fn(low) + breakdown_fn(high) + healthy_fn(ok)
        narratives += samples.benign_events(low, split=False)   # H(N)=0
        narratives += samples.benign_events(high, split=True)   # H(N)=1
        for tk, regime in ((low, "low"), (high, "high"), (ok, "ok")):
            for day, close in _prices(tk, regime):
                prices.add(tk, day, close)
    prices.finalize()

    report = run_backtest(filings, narratives, prices, horizon_days=90)
    print("SYNTHETIC DATA — validates the wiring, not the thesis.")
    print(f"Universe: {len(samples.SECTORS)} sectors x 3 names\n")
    print(report.render())

    confirmed = sorted({o.ticker for o in report.observations
                        if o.state == "confirmed_deterioration"})
    print("\nConfirmed (executable) names across sectors:")
    print(" ", ", ".join(confirmed))


if __name__ == "__main__":
    main()
