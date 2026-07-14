#!/usr/bin/env python3
"""End-to-end demo: the IBM "down 23% on soft guidance" scenario.

Runs the full pipeline on nine quarters of illustrative IBM-shaped data:

    filings CSV  -> filing_ingestor  -> normalized snapshots
    headline     -> narrative_monitor -> structured claims
    both         -> signal_engine     -> gated Signal
    Signal       -> store             -> SQLite audit + JSONL feed
    JSONL line   -> execution_adapter -> accept / reject (dry run)

The point of this example: the narrative is loud (soft guidance, AI investment,
deal timing) but only two comparable-period criteria confirm, so the engine
returns EARLY_EVIDENCE and refuses to make it executable. Formally cutting
full-year FCF guidance would add the third criterion and flip it to
CONFIRMED_DETERIORATION — see tests/test_signal_engine.py.

    python3 run_demo.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from narrative_monitor import (
    CsvFilingSource,
    NarrativeEvent,
    SignalEngine,
    SignalStore,
    consume,
    execution_gate,
    extract_claims,
    narrative_intensity,
    publish_signal,
)
from narrative_monitor.store import _to_payload

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)

DATA = Path(__file__).parent / "data" / "ibm_sample.csv"


def main() -> None:
    # 1. What is the narrative?
    events = [
        NarrativeEvent(
            ticker="IBM",
            event_time="2026-04-22T08:00:00-04:00",
            headline="IBM issues soft guidance; shares fall 23%",
            body=(
                "Management cited deal timing, AI infrastructure spending, "
                "budget reallocation and customer uncertainty. Pipeline "
                "remains strong, executives said."
            ),
            source="demo",
        )
    ]
    claims = extract_claims(events)
    intensity = narrative_intensity(claims)

    # 2. Has the narrative appeared in reported financials?
    snapshots = CsvFilingSource(DATA).fetch("IBM")
    signal = SignalEngine().evaluate(snapshots, claims, intensity)

    # persist: durable audit log + machine-readable feed
    store = SignalStore()
    store.save(signal)
    store.close()
    publish_signal(signal)

    # 3. Is the evidence strong enough for the strategy to consume?
    line = _to_payload(signal)  # exactly what lands in the JSONL feed
    accepted = consume(line, live=False)

    print(json.dumps(asdict(signal), indent=2, default=str))
    print("\nClaims identified:", ", ".join(signal.claims) or "(none)")
    print("Confirmed criteria:", ", ".join(signal.confirmed_criteria) or "(none)")
    print("execution_gate():", execution_gate(line))
    print("order placed:", accepted)


if __name__ == "__main__":
    main()
