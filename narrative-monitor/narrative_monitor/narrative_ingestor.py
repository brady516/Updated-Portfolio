"""narrative_ingestor — raw feeds -> the parrot layer of NarrativeEvents.

The entropy machinery is only as good as the corpus behind it. A single
management quote gives you `H(N)=0`; the signal lives in the *breadth* — the
management frame plus every sell-side note and media piece that echoes or
dissents from it. This service assembles that layer and measures its
propagation.

Real deployments wire `NarrativeSource.fetch` to a transcript/news stack;
ships with a JSONL loader so the demo runs with no credentials. The record
schema is the contract every provider adapter must emit.

Stdlib only.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import NarrativeClaim, NarrativeEvent
from .narrative_monitor import extract_claims


class NarrativeSource(ABC):
    """Provider adapter contract. Implement `fetch` for a transcript/news feed."""

    @abstractmethod
    def fetch(self, ticker: str) -> Sequence[NarrativeEvent]:
        ...


class JsonlNarrativeSource(NarrativeSource):
    """Loads NarrativeEvents from newline-delimited JSON.

    Each line: {ticker, event_time, headline, body, source, source_type}.
    `source_type` is one of management | sell_side | media | other.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch(self, ticker: str) -> list[NarrativeEvent]:
        return [e for e in self.load_all() if e.ticker == ticker]

    def load_all(self) -> list[NarrativeEvent]:
        events: list[NarrativeEvent] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                events.append(
                    NarrativeEvent(
                        ticker=row["ticker"],
                        event_time=row["event_time"],
                        headline=row.get("headline", ""),
                        body=row.get("body", ""),
                        source=row["source"],
                        source_type=row.get("source_type", "other"),
                    )
                )
        return events


@dataclass(frozen=True)
class PropagationSummary:
    """How a frame moved through the parrot layer — the input to decay.

    A benign frame that originated with management and was echoed by many
    sources with no dissent is the slow-to-capitulate setup. The first admit
    from any source is the capitulation; the lag until it is the head start.
    """

    ticker: str
    benign_sources: int
    admit_sources: int
    originator: str | None      # source that first stated the dominant frame
    originator_type: str | None
    dominant_frames: list[str]  # claim labels carried by the most sources
    capitulation_lag_hours: float | None  # first benign -> first admit
    capitulated: bool = field(default=False)


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parrot_propagation(events: Sequence[NarrativeEvent]) -> PropagationSummary:
    """Summarize how the narrative propagated across sources and time."""
    claims = extract_claims(events)
    ticker = events[0].ticker if events else ""

    benign_sources = {c.source for c in claims if c.stance == "benign"}
    admit_sources = {c.source for c in claims if c.stance == "admit"}

    # frames carried by the most distinct sources (the loudest parrots)
    label_sources: dict[str, set[str]] = {}
    for c in claims:
        label_sources.setdefault(c.label, set()).add(c.source)
    ranked = sorted(label_sources.items(), key=lambda kv: len(kv[1]), reverse=True)
    dominant = [label for label, srcs in ranked if len(srcs) == len(ranked[0][1])] \
        if ranked else []

    # originator: earliest event carrying a dominant benign frame
    event_by_source = {e.source: e for e in events}
    originator = originator_type = None
    if dominant:
        carriers = [
            event_by_source[c.source]
            for c in claims
            if c.label in dominant and c.stance == "benign" and c.source in event_by_source
        ]
        timed = [(e, _parse_time(e.event_time)) for e in carriers]
        timed = [(e, t) for e, t in timed if t is not None]
        if timed:
            first = min(timed, key=lambda et: et[1])[0]
            originator, originator_type = first.source, first.source_type

    # capitulation: first benign event vs first admit event
    def _first_time(stance: str) -> datetime | None:
        times = [
            _parse_time(event_by_source[c.source].event_time)
            for c in claims
            if c.stance == stance and c.source in event_by_source
        ]
        times = [t for t in times if t is not None]
        return min(times) if times else None

    first_benign = _first_time("benign")
    first_admit = _first_time("admit")
    lag_hours = None
    if first_benign is not None and first_admit is not None:
        lag_hours = round((first_admit - first_benign).total_seconds() / 3600.0, 2)

    return PropagationSummary(
        ticker=ticker,
        benign_sources=len(benign_sources),
        admit_sources=len(admit_sources),
        originator=originator,
        originator_type=originator_type,
        dominant_frames=dominant,
        capitulation_lag_hours=lag_hours,
        capitulated=bool(admit_sources),
    )
