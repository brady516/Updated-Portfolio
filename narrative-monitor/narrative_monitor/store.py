"""Signal persistence: an auditable SQLite log plus a JSONL feed.

The JSONL feed is the handoff to the execution process — it can tail the file
or drain it through a queue. The SQLite table is the durable audit trail: every
signal the engine ever emitted, including the ones it refused to make
executable, so a later post-mortem can ask "what did we know, and when."

Stdlib only.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .models import Signal

DATABASE_PATH = Path("fundamental_monitor.db")
SIGNAL_OUTPUT_PATH = Path("fundamental_signals.jsonl")


def _to_payload(signal: Signal) -> dict:
    payload = asdict(signal)
    payload["state"] = signal.state.value  # StrEnum -> plain string
    return payload


class SignalStore:
    def __init__(self, path: Path = DATABASE_PATH) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                generated_at TEXT NOT NULL,
                ticker TEXT NOT NULL,
                state TEXT NOT NULL,
                score REAL NOT NULL,
                confidence REAL NOT NULL,
                execution_eligible INTEGER NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (generated_at, ticker)
            )
            """
        )
        self.connection.commit()

    def save(self, signal: Signal) -> None:
        payload = json.dumps(_to_payload(signal), default=str)
        self.connection.execute(
            """
            INSERT OR REPLACE INTO signals (
                generated_at, ticker, state, score, confidence,
                execution_eligible, payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.generated_at,
                signal.ticker,
                signal.state.value,
                signal.score,
                signal.confidence,
                int(signal.execution_eligible),
                payload,
            ),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


def publish_signal(
    signal: Signal, output_path: Path = SIGNAL_OUTPUT_PATH
) -> None:
    """Append one JSON line the execution engine can consume. Every signal is
    published; the consumer decides via the execution gate, not this writer."""
    with output_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(_to_payload(signal)) + "\n")
