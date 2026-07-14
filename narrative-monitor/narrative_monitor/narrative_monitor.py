"""narrative_monitor — news / transcripts -> structured claims + entropy.

Two jobs, both direction-free:

  1. Identify *what claim is being made* and its *stance toward the reporting*
     (benign vs admit) — never its market direction. That is the crucial line:
     NLP names the claim; the financial engine decides the sign.

  2. Measure the parrot layer's *entropy*. A frame repeated identically by
     management, the sell-side, and the media is a low-entropy consensus — the
     highest-conviction, slowest-to-capitulate breakdown setup.

     "AI investment temporarily depressed results." (benign)
        -> claim label: ai_investment, stance: benign
        -> if every source parrots it (low H(N)) while the reporting diverges,
           that is the setup the engine scores highest.

Deterministic and rule-based on purpose; swap `CLAIM_LEXICON` for a
model-backed extractor later — the NarrativeClaim contract is stable.

Stdlib only.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from .entropy import stance_entropy
from .models import NarrativeClaim, NarrativeEvent

# phrase -> (claim label, stance). Stance is toward the *reporting* — whether
# the frame denies weakness (benign) or concedes it (admit) — and carries no
# bullish/bearish market sign of its own.
CLAIM_LEXICON: dict[str, tuple[str, str]] = {
    "soft guidance": ("guidance_soft", "benign"),  # usually paired with excuses
    "lowered guidance": ("guidance_cut", "admit"),
    "reduced our outlook": ("guidance_cut", "admit"),
    "cut our outlook": ("guidance_cut", "admit"),
    "deal timing": ("deal_timing", "benign"),
    "deals slipped": ("deal_timing", "benign"),
    "slipped into": ("deal_timing", "benign"),
    "budget reallocation": ("budget_reallocation", "benign"),
    "ai investment": ("ai_investment", "benign"),
    "ai infrastructure": ("ai_investment", "benign"),
    "investing in ai": ("ai_investment", "benign"),
    "customer optimization": ("customer_optimization", "benign"),
    "customer uncertainty": ("demand_softness", "admit"),
    "temporary headwind": ("temporary_headwind", "benign"),
    "macro uncertainty": ("macro", "benign"),  # externalizing = deflection
    "execution issue": ("execution", "admit"),
    "pipeline remains strong": ("pipeline_intact", "benign"),
    "demand environment": ("demand_softness", "admit"),
}


def extract_claims(
    events: Sequence[NarrativeEvent],
) -> list[NarrativeClaim]:
    """Return the distinct claims present across `events`.

    Distinct by (label, source): the same label from two different sources is
    kept, because narrative *entropy* depends on how many sources carry each
    stance. Case-insensitive substring match over headline + body.
    """
    claims: list[NarrativeClaim] = []
    seen: set[tuple[str, str]] = set()
    for event in events:
        haystack = f"{event.headline} {event.body}".lower()
        for phrase, (label, stance) in CLAIM_LEXICON.items():
            key = (label, event.source)
            if phrase in haystack and key not in seen:
                seen.add(key)
                claims.append(
                    NarrativeClaim(
                        ticker=event.ticker,
                        label=label,
                        phrase=phrase,
                        source=event.source,
                        stance=stance,
                    )
                )
    return claims


def narrative_intensity(claims: Iterable[NarrativeClaim]) -> float:
    """0..1 gauge of how *loud* the story is — never its direction. Cannot, on
    its own, raise a signal above narrative_only; only reporting divergence can.
    """
    distinct = len({claim.label for claim in claims})
    return min(1.0, distinct / 3.0)


def _stance_weights(claims: Sequence[NarrativeClaim]) -> tuple[float, float]:
    """Aggregate benign/admit weight across the parrot layer, weighting by
    SOURCE, not raw phrase count.

    Each source contributes total weight 1, split by the proportion of its own
    claims that are benign vs admit. So a chatty analyst who repeats one frame
    ten ways cannot masquerade as a ten-source consensus, and two sources on
    opposite sides read as a genuine 50/50 split.
    """
    by_source: dict[str, Counter[str]] = {}
    for c in claims:
        if c.stance in ("benign", "admit"):
            by_source.setdefault(c.source, Counter())[c.stance] += 1
    benign = admit = 0.0
    for counts in by_source.values():
        total = sum(counts.values())
        if total == 0:
            continue
        benign += counts.get("benign", 0) / total
        admit += counts.get("admit", 0) / total
    return benign, admit


def benign_alignment(claims: Sequence[NarrativeClaim]) -> float:
    """Source-weighted fraction of the narrative that denies weakness.

    High -> the consensus is "nothing is really wrong," which is exactly the
    frame a diverging filing breaks. If the narrative already admits weakness,
    there is no breakdown to catch — it is acknowledged and largely priced.
    Returns 0.5 (neutral) when there is no benign/admit signal at all.
    """
    benign, admit = _stance_weights(claims)
    if benign + admit == 0:
        return 0.5
    return benign / (benign + admit)


def narrative_entropy(claims: Sequence[NarrativeClaim]) -> float:
    """H(N) in [0,1]: entropy of the source-weighted benign/admit split.
    0 = unanimous parrots (slow to capitulate); 1 = evenly divided."""
    benign, admit = _stance_weights(claims)
    if benign + admit == 0:
        return 0.0
    return stance_entropy({"benign": benign, "admit": admit})
