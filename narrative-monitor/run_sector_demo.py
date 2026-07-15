#!/usr/bin/env python3
"""Sector demo: the SAME engine reading each sector's own microstructure.

Financials, REITs, brokers, insurers, lenders, and SaaS aren't exceptions to the
thesis — they're the richest cases, because reserves, marks, float, vintages, and
deferred revenue are estimates with room for the story to diverge from cash. Each
runs a *benign* narrative over a filing that breaks through its own channels.

    python3 run_sector_demo.py
"""

from __future__ import annotations

from narrative_monitor import (
    SignalEngine, extract_claims, narrative_intensity, samples,
)

LABELS = {
    "industrial": "Industrial — 'temporary headwind'",
    "financial": "Bank — 'credit remains benign'",
    "reit": "REIT — 'external growth is accretive'",
    "broker": "Broker — 'durable franchise earnings'",
    "insurance": "Insurer — 'underwriting stays disciplined'",
    "lender": "Lender — 'record originations, TAM expansion'",
    "saas": "SaaS — 'best-in-class retention, durable growth'",
}


def main() -> None:
    print("SAME engine, different microstructure. Benign narratives, broken filings.\n")
    engine = SignalEngine()
    for sector, (breakdown_fn, _healthy) in samples.SECTORS.items():
        panel = breakdown_fn(sector.upper()[:6])
        claims = extract_claims(samples.benign_events(panel[0].ticker))
        signal = engine.evaluate(panel, claims, narrative_intensity(claims))
        print(f"=== {LABELS[sector]} ({sector}) ===")
        print(f"state: {signal.state.value}   breakdown_score: {signal.breakdown_score}   "
              f"H(N): {signal.narrative_entropy}   executable: {signal.execution_eligible}")
        print("channels fired:", ", ".join(signal.confirmed_criteria))
        for r in signal.reasons[:3]:
            print("  •", r)
        print()


if __name__ == "__main__":
    main()
