"""narrative_monitor — news / transcripts -> structured claims.

This service does ONE job: identify *what claim is being made*. It never
decides whether the claim is good or bad news. That is the crucial design
line — NLP identifies the claim; the financial engine decides direction.

    "AI investment temporarily depressed results."
        -> claim label: ai_investment
        -> the signal engine then asks: did capex intensity rise? did organic
           revenue slow? did FCF conversion fall? did margin weaken?

Deterministic and rule-based on purpose: a keyword map can't invent a motive,
only recognize the phrase that is on the page. Swap `CLAIM_LEXICON` for a
model-backed extractor later — the output contract (NarrativeClaim) is stable.

Stdlib only.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .models import NarrativeClaim, NarrativeEvent

# phrase -> claim label. Multiple phrases can map to the same label; the label
# is what the signal engine keys its financial tests on. Deliberately free of
# any sentiment weighting.
CLAIM_LEXICON: dict[str, str] = {
    "soft guidance": "guidance_soft",
    "lowered guidance": "guidance_cut",
    "reduced our outlook": "guidance_cut",
    "cut our outlook": "guidance_cut",
    "deal timing": "deal_timing",
    "deals slipped": "deal_timing",
    "slipped into": "deal_timing",
    "budget reallocation": "budget_reallocation",
    "ai investment": "ai_investment",
    "ai infrastructure": "ai_investment",
    "investing in ai": "ai_investment",
    "customer optimization": "customer_optimization",
    "customer uncertainty": "demand_softness",
    "temporary headwind": "temporary_headwind",
    "macro uncertainty": "macro",
    "execution issue": "execution",
    "pipeline remains strong": "pipeline_intact",
    "demand environment": "demand_softness",
}


def extract_claims(
    events: Sequence[NarrativeEvent],
) -> list[NarrativeClaim]:
    """Return the distinct claims present across `events`.

    Case-insensitive substring match. A phrase found in either the headline or
    the body counts. Duplicate labels are collapsed to their first occurrence
    so downstream code reasons over claim *kinds*, not raw hit counts.
    """
    claims: list[NarrativeClaim] = []
    seen_labels: set[str] = set()
    for event in events:
        haystack = f"{event.headline} {event.body}".lower()
        for phrase, label in CLAIM_LEXICON.items():
            if phrase in haystack and label not in seen_labels:
                seen_labels.add(label)
                claims.append(
                    NarrativeClaim(
                        ticker=event.ticker,
                        label=label,
                        phrase=phrase,
                        source=event.source,
                    )
                )
    return claims


def narrative_intensity(claims: Iterable[NarrativeClaim]) -> float:
    """A 0..1 gauge of *how loud* the story is — never its direction.

    Used only to distinguish "a narrative exists at all" (NARRATIVE_ONLY) from
    silence. It cannot raise a signal above NARRATIVE_ONLY on its own; only the
    financial engine can do that.
    """
    distinct = len({claim.label for claim in claims})
    return min(1.0, distinct / 3.0)
