#!/usr/bin/env python3
"""Live end-to-end: real SEC EDGAR filings -> a gated signal.

Fetches a ticker's as-filed quarterly fundamentals from SEC EDGAR company-facts,
normalizes them (discrete quarters, FCF, gross margin, point-in-time), and runs
the engine — the same pipeline the synthetic demos use, now on real numbers.

    python3 run_live_demo.py IBM
    python3 run_live_demo.py AAPL MSFT NVDA

Requires outbound HTTPS to sec.gov. SEC asks for a declared User-Agent with a
contact address (set EDGAR_EMAIL or edit below).
"""

from __future__ import annotations

import os
import sys
import urllib.error

from narrative_monitor import EdgarFilingSource, SignalEngine

EMAIL = os.environ.get("EDGAR_EMAIL", "blgallag.bg@gmail.com")


def main(tickers: list[str]) -> int:
    source = EdgarFilingSource(email=EMAIL)
    engine = SignalEngine()
    for ticker in tickers:
        try:
            snapshots = source.fetch(ticker)
        except urllib.error.HTTPError as exc:
            print(f"{ticker}: SEC returned HTTP {exc.code}. If this is a 403 from a "
                  "proxy, sec.gov egress is blocked for this environment — run where "
                  "SEC is reachable, or have an admin allowlist data.sec.gov.")
            return 2
        except (urllib.error.URLError, OSError) as exc:
            print(f"{ticker}: could not reach SEC EDGAR ({exc}). sec.gov egress may be "
                  "blocked in this environment.")
            return 2
        except KeyError as exc:
            print(f"{ticker}: {exc}")
            continue

        if len(snapshots) < 3:
            print(f"{ticker}: only {len(snapshots)} normalized quarters — "
                  "not enough comparable-period history.")
            continue

        signal = engine.evaluate(snapshots, claims=[])
        print(f"\n=== {ticker} ({len(snapshots)} quarters, "
              f"latest {snapshots[-1].period}, filed {snapshots[-1].reported_at}) ===")
        print(f"state: {signal.state.value}   breakdown_score: {signal.breakdown_score}   "
              f"divergence: {signal.divergence}   executable: {signal.execution_eligible}")
        for reason in signal.reasons[:4]:
            print("  •", reason)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:] or ["IBM"]
    raise SystemExit(main(args))
