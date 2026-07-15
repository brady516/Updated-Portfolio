#!/usr/bin/env python3
"""Scan the whole US filer universe through the engine, one ticker at a time.

Pulls every ticker from SEC's map (~10k+ filers), fetches each company's as-filed
quarterly fundamentals from EDGAR, runs the engine, and writes a signal per name
to JSONL. At the end it ranks the biggest breakdowns so you don't read 10k lines.

    python3 run_universe_scan.py                 # everything (a ~30-60 min run)
    python3 run_universe_scan.py --limit 100     # a quick trial
    python3 run_universe_scan.py --tickers my.txt --out hits.jsonl --cache .edgar

It is polite (paced under SEC's 10 req/s), resumable (skips tickers already in the
output file, so re-running continues), and crash/Ctrl-C safe (writes as it goes).

Point-in-time and as-filed discipline come from the EDGAR adapter; nothing here
relaxes them. SEC asks for a contact User-Agent — set EDGAR_EMAIL or edit below.

CAVEAT: the live adapter reads the INDUSTRIAL concept set, so every name is scored
on FCF/margins. Banks, REITs, insurers, and BDCs need their sector XBRL concept
maps before their hits are trustworthy — treat non-industrial confirmations as
candidates to verify, not signals.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
from pathlib import Path

from narrative_monitor import EdgarClient, EdgarFilingSource, SignalEngine

EMAIL = os.environ.get("EDGAR_EMAIL", "blgallag.bg@gmail.com")
ACTIONABLE = {"confirmed_deterioration", "early_evidence", "improving"}


def _already_done(out_path: Path) -> set[str]:
    done: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["ticker"])
            except (json.JSONDecodeError, KeyError):
                pass
    return done


def scan(tickers: list[str], out_path: Path, source) -> None:
    engine = SignalEngine()
    done = _already_done(out_path)
    counts = {"scanned": 0, "no_data": 0, "error": 0, "hit": 0}
    started = time.time()

    with out_path.open("a", encoding="utf-8") as out:
        for i, ticker in enumerate(tickers, 1):
            if ticker in done:
                continue
            try:
                snaps = source.fetch(ticker)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    counts["no_data"] += 1          # funds/ADRs/deregistered: no XBRL
                else:
                    counts["error"] += 1
                continue
            except (urllib.error.URLError, OSError, ValueError, KeyError):
                counts["error"] += 1
                continue

            counts["scanned"] += 1
            if len(snaps) < 3:
                counts["no_data"] += 1
                continue

            signal = engine.evaluate(snaps, claims=[])
            if signal.state.value in ACTIONABLE:
                counts["hit"] += 1
                out.write(json.dumps({
                    "ticker": ticker,
                    "state": signal.state.value,
                    "breakdown_score": signal.breakdown_score,
                    "divergence": signal.divergence,
                    "confidence": signal.confidence,
                    "execution_eligible": signal.execution_eligible,
                    "period": snaps[-1].period,
                    "reported_at": snaps[-1].reported_at,
                    "confirmed_criteria": signal.confirmed_criteria,
                    "reasons": signal.reasons[:3],
                }) + "\n")
                out.flush()

            if i % 100 == 0:
                rate = i / max(time.time() - started, 1e-9)
                print(f"[{i}/{len(tickers)}] scanned={counts['scanned']} "
                      f"hits={counts['hit']} no_data={counts['no_data']} "
                      f"err={counts['error']}  {rate:.1f} tick/s", file=sys.stderr)

    print(f"\nDone. {counts}", file=sys.stderr)


def rank(out_path: Path, top: int = 25) -> None:
    rows = []
    for line in out_path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    deteriorating = [r for r in rows if r["state"] in
                     ("confirmed_deterioration", "early_evidence")]
    deteriorating.sort(key=lambda r: (r["execution_eligible"], r["breakdown_score"]),
                       reverse=True)
    print(f"\nTop {min(top, len(deteriorating))} breakdowns "
          f"(of {len(deteriorating)} deteriorating / {len(rows)} actionable):\n")
    print(f"{'ticker':<8}{'state':<24}{'score':>6} {'exec':>5}  latest   channels")
    for r in deteriorating[:top]:
        chans = ", ".join(r.get("confirmed_criteria", [])[:3])
        print(f"{r['ticker']:<8}{r['state']:<24}{r['breakdown_score']:>6.2f} "
              f"{str(r['execution_eligible']):>5}  {r['period']:<8} {chans}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="scan only the first N tickers")
    ap.add_argument("--tickers", help="file with one ticker per line (default: all SEC filers)")
    ap.add_argument("--out", default="universe_signals.jsonl")
    ap.add_argument("--cache", help="dir to cache raw EDGAR responses (faster re-runs)")
    ap.add_argument("--rank-only", action="store_true", help="just rank an existing --out")
    args = ap.parse_args()

    out_path = Path(args.out)
    if args.rank_only:
        rank(out_path)
        return 0

    client = EdgarClient(email=EMAIL, cache_dir=args.cache)
    try:
        if args.tickers:
            tickers = [t.strip().upper() for t in Path(args.tickers).read_text().split() if t.strip()]
        else:
            tickers = client.all_tickers()
    except (urllib.error.URLError, OSError) as exc:
        print(f"Could not load the ticker universe ({exc}). Is sec.gov reachable?",
              file=sys.stderr)
        return 2
    if args.limit:
        tickers = tickers[:args.limit]

    print(f"Scanning {len(tickers)} tickers -> {out_path} "
          f"(resuming past {len(_already_done(out_path))})", file=sys.stderr)
    source = EdgarFilingSource(email=EMAIL, client=client)
    try:
        scan(tickers, out_path, source)
    except KeyboardInterrupt:
        print("\nInterrupted — progress saved. Re-run to resume.", file=sys.stderr)
    rank(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
