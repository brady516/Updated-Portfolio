"""Information-theoretic primitives for the breakdown model.

The thesis (THESIS.md) rests on three quantities:

    * divergence   — how far reporting is from what the narrative implies,
    * narrative entropy H(N)  — how uniform/crowded the parrot consensus is,
    * reporting entropy H(R)  — how obfuscated the filing itself is.

This module holds only the math. It has no notion of filings or claims, so it
is trivially testable and reusable. Stdlib only.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ramp(magnitude: float, floor: float, severe: float) -> float:
    """Map a raw magnitude to [0, 1] linearly between `floor` and `severe`.

    Below `floor` -> 0 (not material). At/above `severe` -> 1 (saturated).
    This is how a channel's raw deterioration (e.g. an 11% TTM FCF drop)
    becomes a bounded divergence contribution.
    """
    if severe <= floor:
        raise ValueError("severe must exceed floor.")
    return clip((magnitude - floor) / (severe - floor))


def noisy_or(contributions: Iterable[float]) -> float:
    """Combine independent [0,1] evidence into a single [0,1] score.

    1 - Π(1 - c_i). Multiple weak channels compound, no single channel can
    saturate the total on its own, and a missing channel (contribution 0)
    simply drops out — which is exactly the completeness behavior we want:
    absent evidence neither helps nor hurts.
    """
    product = 1.0
    for c in contributions:
        product *= 1.0 - clip(c)
    return 1.0 - product


def shannon_entropy(distribution: Iterable[float], *, normalized: bool = True) -> float:
    """Shannon entropy of a probability distribution, in bits.

    `normalized=True` scales to [0, 1] against the maximum entropy for the
    number of outcomes, so a two-frame narrative and a five-frame narrative are
    comparable. An empty or single-outcome distribution has entropy 0.
    """
    probs = [p for p in distribution if p > 0]
    if len(probs) <= 1:
        return 0.0
    total = sum(probs)
    if total <= 0:
        return 0.0
    probs = [p / total for p in probs]
    bits = -sum(p * math.log2(p) for p in probs)
    if not normalized:
        return bits
    max_bits = math.log2(len(probs))
    return bits / max_bits if max_bits > 0 else 0.0


def stance_entropy(counts: Mapping[str, float]) -> float:
    """Normalized entropy over a map of stance -> weight (e.g. source counts).

    0.0  = unanimous (every source tells the same frame — a tight parrot
           consensus, the slowest to capitulate).
    1.0  = maximally split.
    """
    return shannon_entropy(counts.values(), normalized=True)
