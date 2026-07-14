"""signal_engine — the narrative-breakdown model (see THESIS.md).

The signal is the *divergence* between a confident narrative and the reporting
microstructure, weighted by how uniform the narrative is:

    S_t  =  D_report  ×  (0.5 + 0.5·A)  ×  (0.5 + 0.5·(1 − H(N)))

  * D_report — reporting divergence: a sector's microstructure channels (see
    channels.py), each scored continuously to [0,1] and combined by noisy-OR,
    plus a disclosure-withdrawal channel so obfuscation H(R) counts as
    divergence.
  * A — benign_alignment: how much the narrative denies weakness.
  * H(N) — narrative entropy: a tight parrot consensus amplifies the score and
    implies slow capitulation.

The engine is SECTOR-AGNOSTIC. It selects a ChannelSet by `snapshot.sector`
(industrial / financial / reit / …) and consumes whatever channels it returns —
the divergence x entropy math, the state machine, the gate, and the backtest are
identical across sectors. Truth is denominated differently per sector; the engine
does not care which denomination.

Invariant: S_t ∝ D_report — with zero reporting divergence the score is zero no
matter how loud the narrative. Comparable-period / TTM only; as-filed only.
Stdlib only.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from .channels import Channel, ChannelContext, channel_set_for
from .entropy import noisy_or
from .models import FundamentalSnapshot, NarrativeClaim, Period, Signal, SignalState
from .narrative_monitor import benign_alignment, narrative_entropy

# state cut points on the breakdown score S_t
CONFIRMED_SCORE = 0.60
EARLY_SCORE = 0.25
NARRATIVE_ONLY_DIVERGENCE_FLOOR = 0.10
EXECUTION_MIN_CONFIDENCE = 0.75
CONTRIBUTING_MAGNITUDE = 0.10


def _index_by_period(
    snapshots: Sequence[FundamentalSnapshot],
) -> dict[Period, FundamentalSnapshot]:
    return {snap.parsed_period: snap for snap in snapshots}


class SignalEngine:
    """Turns snapshots + extracted claims into a gated, entropy-weighted Signal,
    reading whichever sector microstructure the snapshots are denominated in."""

    def evaluate(
        self,
        snapshots: Sequence[FundamentalSnapshot],
        claims: Sequence[NarrativeClaim],
        narrative_intensity: float = 0.0,
    ) -> Signal:
        if not snapshots:
            raise ValueError("At least one fundamental snapshot is required.")

        ordered = sorted(snapshots, key=lambda s: s.parsed_period)
        by_period = _index_by_period(ordered)
        current = ordered[-1]
        cur_p = current.parsed_period
        prior_year = by_period.get(cur_p.prior_year())

        ctx = ChannelContext(ordered, by_period, current, prior_year)
        channels = channel_set_for(current.sector)

        # --- narrative side: benign alignment A and entropy H(N) ----------
        has_stance = any(c.stance in ("benign", "admit") for c in claims)
        alignment = benign_alignment(claims)
        h_narrative = narrative_entropy(claims)

        # --- reporting side: sector channels + obfuscation ----------------
        det = channels.deterioration(ctx)
        imp = channels.improvement(ctx)
        h_reporting = channels.reporting_entropy(ctx)
        if h_reporting > 0:
            det.append(
                Channel(
                    "disclosure_withdrawal",
                    h_reporting,
                    "Disclosure narrowed or marks look stale relative to a year "
                    "ago (obfuscation).",
                )
            )

        d_report = noisy_or(c.magnitude for c in det)
        d_improve = noisy_or(c.magnitude for c in imp)
        divergence = d_report - d_improve

        entropy_factor = 0.5 + 0.5 * (1.0 - h_narrative)
        breakdown_score = round(
            d_report * (0.5 + 0.5 * alignment) * entropy_factor, 4
        )
        improve_score = round(
            d_improve * (0.5 + 0.5 * (1.0 - alignment)) * entropy_factor, 4
        )

        has_narrative = has_stance or narrative_intensity > 0
        state = self._state(breakdown_score, improve_score, d_report, has_narrative)

        primary_ttm = channels.primary_ttm(ctx)
        confidence = self._confidence(
            ordered, current, det, imp, h_reporting, state, primary_ttm
        )
        execution_eligible = (
            state is SignalState.CONFIRMED_DETERIORATION
            and confidence >= EXECUTION_MIN_CONFIDENCE
            and primary_ttm is not None            # sector's own TTM window
            and not current.restated               # point-in-time contract
        )
        expected_decay = self._expected_decay(h_narrative, has_narrative)

        contributing = [
            c for c in (det if breakdown_score >= improve_score else imp)
            if c.magnitude >= CONTRIBUTING_MAGNITUDE
        ]
        contributing.sort(key=lambda c: c.magnitude, reverse=True)
        reasons = [c.reason for c in contributing] or [
            "No comparable-period channel diverged materially."
        ]
        if state is SignalState.NARRATIVE_ONLY:
            reasons.insert(
                0,
                "Narrative present but the reporting does not diverge "
                f"(divergence {d_report:.2f}).",
            )

        metrics = self._metrics(
            ctx, channels.sector, alignment, h_narrative, h_reporting,
            d_report, primary_ttm, narrative_intensity,
        )

        return Signal(
            ticker=current.ticker,
            state=state,
            score=round(breakdown_score - improve_score, 4),
            confidence=confidence,
            generated_at=datetime.now(UTC).isoformat(),
            reasons=reasons,
            metrics=metrics,
            execution_eligible=execution_eligible,
            claims=[c.label for c in claims],
            confirmed_criteria=[c.key for c in contributing],
            divergence=round(divergence, 4),
            breakdown_score=breakdown_score,
            narrative_entropy=round(h_narrative, 4),
            reporting_entropy=round(h_reporting, 4),
            expected_decay=expected_decay,
        )

    # --- state / decay / confidence --------------------------------------
    def _state(
        self, breakdown_score: float, improve_score: float,
        d_report: float, has_narrative: bool,
    ) -> SignalState:
        if breakdown_score >= CONFIRMED_SCORE and breakdown_score > improve_score:
            return SignalState.CONFIRMED_DETERIORATION
        if improve_score >= CONFIRMED_SCORE and improve_score > breakdown_score:
            return SignalState.IMPROVING
        if breakdown_score >= EARLY_SCORE and breakdown_score >= improve_score:
            return SignalState.EARLY_EVIDENCE
        if improve_score >= EARLY_SCORE and improve_score > breakdown_score:
            return SignalState.EARLY_EVIDENCE
        if has_narrative and d_report < NARRATIVE_ONLY_DIVERGENCE_FLOOR:
            return SignalState.NARRATIVE_ONLY
        return SignalState.INCONCLUSIVE

    @staticmethod
    def _expected_decay(h_narrative: float, has_narrative: bool) -> str:
        """Slow capitulation <=> tight (low-entropy) parrot consensus. Binary
        entropy runs high even for lopsided splits, so the bands are wide."""
        if not has_narrative:
            return "n/a"
        if h_narrative < 0.40:
            return "slow"
        if h_narrative < 0.75:
            return "medium"
        return "fast"

    def _confidence(
        self, ordered: Sequence[FundamentalSnapshot],
        current: FundamentalSnapshot, det: Sequence[Channel],
        imp: Sequence[Channel], h_reporting: float, state: SignalState,
        primary_ttm: float | None,
    ) -> float:
        """Evidence depth, not conviction. Obfuscation and thin history lower it
        so a signal can't clear the execution gate on a shallow window."""
        has_ttm = primary_ttm is not None
        has_prior_ttm = has_ttm and len(ordered) >= 8
        active = [c for c in (det if state is not SignalState.IMPROVING else imp)
                  if c.magnitude > 0]
        confidence = (
            0.30
            + 0.04 * min(len(ordered), 8)
            + (0.12 if has_ttm else 0.0)
            + (0.10 if has_prior_ttm else 0.0)
            + 0.04 * min(len(active), 4)
        )
        confidence *= 1.0 - 0.5 * h_reporting  # obfuscation penalty
        return round(min(0.95, confidence), 3)

    def _metrics(
        self, ctx: ChannelContext, sector: str, benign_alignment_: float,
        h_narrative: float, h_reporting: float, d_report: float,
        primary_ttm: float | None, narrative_intensity: float,
    ) -> dict[str, float | str | None]:
        cur = ctx.current
        cur_p = cur.parsed_period
        m: dict[str, float | str | None] = {
            "sector": sector,
            "period": str(cur_p),
            "comparable_period": str(cur_p.prior_year()),
            "as_filed": not cur.restated,
            "primary_ttm": primary_ttm,
            "reporting_divergence": round(d_report, 4),
            "benign_alignment": round(benign_alignment_, 4),
            "narrative_entropy": round(h_narrative, 4),
            "reporting_entropy": round(h_reporting, 4),
            "narrative_intensity": narrative_intensity,
        }
        if sector == "industrial":  # keep the familiar industrial detail
            m["fcf_margin"] = cur.fcf_margin if cur.revenue else None
            m["revenue_yoy"] = ctx.yoy(lambda s: s.revenue if s else None)
            m["free_cash_flow_yoy"] = ctx.yoy(lambda s: s.free_cash_flow if s else None)
        return m
