"""execution_adapter — the hard gate between research and an order.

The engine's job ends at a Signal. This module is the *only* place a signal is
allowed to become an action, and it is deliberately paranoid: it re-checks
every gating condition itself rather than trusting a single boolean, so a
malformed or hand-edited JSONL line can't slip a position through.

Wire `paper_or_live` to Interactive Brokers or another OMS. Until then it is a
dry-run that just logs what it *would* do — which is the correct default for a
research engine.

Stdlib only.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

EXECUTION_MIN_CONFIDENCE = 0.75


def execution_gate(signal: dict) -> bool:
    """Reject anything not explicitly, independently eligible.

    All three conditions must hold. The `execution_eligible` flag alone is not
    trusted — state and confidence are re-verified here on purpose.
    """
    return (
        signal.get("execution_eligible") is True
        and signal.get("state") == "confirmed_deterioration"
        and float(signal.get("confidence", 0)) >= EXECUTION_MIN_CONFIDENCE
    )


def consume(signal: dict, *, live: bool = False) -> bool:
    """Decide and (optionally) act. Returns True iff an order was placed.

    `live=False` (default) is a dry run: it logs the intended action and places
    nothing. This keeps "research engine" the safe default and "order engine"
    an explicit opt-in.
    """
    if not execution_gate(signal):
        logger.info(
            "Rejected %s: state=%s eligible=%s confidence=%s",
            signal.get("ticker"),
            signal.get("state"),
            signal.get("execution_eligible"),
            signal.get("confidence"),
        )
        return False

    if not live:
        logger.info(
            "DRY RUN — would submit deterioration position for %s "
            "(confidence %s). Pass live=True with an OMS wired to act.",
            signal.get("ticker"),
            signal.get("confidence"),
        )
        return False

    # Wire your OMS here (Interactive Brokers, etc.), behind hard risk limits.
    raise NotImplementedError(
        "Attach a broker adapter with position sizing and hard limits before "
        "enabling live execution."
    )
