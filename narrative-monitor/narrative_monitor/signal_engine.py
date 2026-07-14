"""signal_engine — the narrative-breakdown model (see THESIS.md).

The signal is the *divergence* between a confident narrative and the reporting
microstructure, weighted by how uniform the narrative is:

    S_t  =  D_report_eff  ×  (0.5 + 0.5·A)  ×  (0.5 + 0.5·(1 − H(N)))

  * D_report_eff — reporting divergence: the same comparable-period /
    trailing-twelve-month channels as before, each scored *continuously* to a
    [0,1] magnitude and combined by noisy-OR, plus a disclosure-withdrawal
    channel so obfuscation (H(R)) counts as divergence.
  * A — benign_alignment: how much the narrative denies weakness. A benign
    frame contradicted by the reporting is a breakdown; an admitting frame is
    just acknowledged bad news.
  * H(N) — narrative entropy: a tight, unanimous parrot consensus (low H)
    amplifies the score and implies slow capitulation (slow decay).

Invariant: S_t ∝ D_report, so with zero reporting divergence the score is zero
no matter how loud the narrative. A headline cannot create a signal.

Every comparison is comparable-period (Q4/Q4) or TTM, and only as-filed data is
trusted — a restated row can never be executable. Stdlib only.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from .entropy import clip, noisy_or, ramp, stance_entropy
from .models import (
    FundamentalSnapshot,
    NarrativeClaim,
    Period,
    Signal,
    SignalState,
)

# state cut points on the breakdown score S_t
CONFIRMED_SCORE = 0.60
EARLY_SCORE = 0.25
NARRATIVE_ONLY_DIVERGENCE_FLOOR = 0.10
EXECUTION_MIN_CONFIDENCE = 0.75
# a channel counts as "contributing" (listed in confirmed_criteria) above this
CONTRIBUTING_MAGNITUDE = 0.10


@dataclass
class _Channel:
    key: str
    magnitude: float  # [0,1] strength of this channel's divergence
    reason: str


def _index_by_period(
    snapshots: Sequence[FundamentalSnapshot],
) -> dict[Period, FundamentalSnapshot]:
    return {snap.parsed_period: snap for snap in snapshots}


def _yoy(current: float | None, year_ago: float | None) -> float | None:
    if current is None or year_ago is None or year_ago == 0:
        return None
    return current / year_ago - 1.0


def _ttm_fcf(
    by_period: dict[Period, FundamentalSnapshot], end: Period
) -> float | None:
    total = 0.0
    period = end
    for _ in range(4):
        snap = by_period.get(period)
        if snap is None:
            return None
        total += snap.free_cash_flow
        period = (
            Period(period.year - 1, 4)
            if period.quarter == 1
            else Period(period.year, period.quarter - 1)
        )
    return total


class SignalEngine:
    """Turns snapshots + extracted claims into a gated, entropy-weighted Signal."""

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

        # --- narrative side: benign alignment A and entropy H(N) ----------
        stances = [c.stance for c in claims if c.stance in ("benign", "admit")]
        benign_alignment = (
            stances.count("benign") / len(stances) if stances else 0.5
        )
        h_narrative = stance_entropy(Counter(stances)) if stances else 0.0

        # --- reporting side: continuous divergence channels ---------------
        det = self._deterioration_channels(
            ordered, by_period, current, prior_year
        )
        imp = self._improvement_channels(current, prior_year, by_period)
        h_reporting = self._reporting_entropy(current, prior_year)
        if h_reporting > 0:
            det.append(
                _Channel(
                    "disclosure_withdrawal",
                    h_reporting,
                    "Disclosure narrowed (segments dropped / non-GAAP rose / "
                    "a previously reported line went missing).",
                )
            )

        d_report = noisy_or(c.magnitude for c in det)
        d_improve = noisy_or(c.magnitude for c in imp)
        divergence = d_report - d_improve  # signed

        # --- combine into the breakdown score S_t -------------------------
        entropy_factor = 0.5 + 0.5 * (1.0 - h_narrative)
        breakdown_score = round(
            d_report * (0.5 + 0.5 * benign_alignment) * entropy_factor, 4
        )
        improve_score = round(
            d_improve * (0.5 + 0.5 * (1.0 - benign_alignment)) * entropy_factor,
            4,
        )

        has_narrative = bool(stances) or narrative_intensity > 0
        state = self._state(
            breakdown_score, improve_score, d_report, has_narrative
        )
        confidence = self._confidence(
            ordered, by_period, current, det, imp, h_reporting, state
        )
        execution_eligible = (
            state is SignalState.CONFIRMED_DETERIORATION
            and confidence >= EXECUTION_MIN_CONFIDENCE
            and _ttm_fcf(by_period, cur_p) is not None
            and not current.restated  # point-in-time contract
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
            current, prior_year, by_period, benign_alignment,
            h_narrative, h_reporting, d_report, narrative_intensity,
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

    # --- the seven reporting channels, scored continuously ----------------
    def _deterioration_channels(
        self,
        ordered: Sequence[FundamentalSnapshot],
        by_period: dict[Period, FundamentalSnapshot],
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
    ) -> list[_Channel]:
        out: list[_Channel] = []
        cur_p = current.parsed_period

        # 1. Trailing-twelve-month FCF declines (severe at -25%).
        ttm_now = _ttm_fcf(by_period, cur_p)
        ttm_prev = _ttm_fcf(by_period, cur_p.prior_year())
        m = 0.0
        if ttm_now is not None and ttm_prev is not None and ttm_prev != 0:
            decline = (ttm_prev - ttm_now) / abs(ttm_prev)
            m = ramp(decline, 0.0, 0.25) if decline > 0 else 0.0
        out.append(
            _Channel(
                "ttm_fcf_decline",
                m,
                f"TTM free cash flow fell to {ttm_now:.2f} from {ttm_prev:.2f}."
                if m > 0
                else "TTM FCF did not decline (or window incomplete).",
            )
        )

        # 2. FCF margin declines two consecutive comparable periods (severe -5pt).
        prev_q = self._prior_quarter(cur_p)
        this_yoy = self._fcf_margin_yoy(by_period, cur_p)
        last_yoy = self._fcf_margin_yoy(by_period, prev_q) if prev_q else None
        m = 0.0
        if (
            this_yoy is not None
            and last_yoy is not None
            and this_yoy <= -0.005
            and last_yoy <= -0.005
        ):
            worst_common = min(-this_yoy, -last_yoy)  # conservative: the smaller
            m = ramp(worst_common, 0.005, 0.05)
        out.append(
            _Channel(
                "fcf_margin_two_period_decline",
                m,
                "FCF margin fell YoY two consecutive quarters "
                f"({last_yoy:+.1%} then {this_yoy:+.1%})."
                if m > 0
                else "FCF margin did not fall YoY two consecutive quarters.",
            )
        )

        # 3. Gross margin contracts (>100 bps floor, severe at 300 bps).
        c = (
            prior_year.gross_margin - current.gross_margin
            if prior_year is not None
            and current.gross_margin is not None
            and prior_year.gross_margin is not None
            else None
        )
        m = ramp(c, 0.010, 0.030) if c is not None and c > 0 else 0.0
        out.append(
            _Channel(
                "gross_margin_contraction",
                m,
                f"Gross margin contracted {c:.1%} YoY."
                if m > 0
                else "Gross margin did not contract >100 bps YoY.",
            )
        )

        # 4. Receivables outrun revenue (10 ppt floor, severe at 30 ppt).
        rec_yoy = _yoy(
            current.receivables, prior_year.receivables if prior_year else None
        )
        rev_yoy = _yoy(
            current.revenue, prior_year.revenue if prior_year else None
        )
        m = 0.0
        if rec_yoy is not None and rev_yoy is not None:
            lead = rec_yoy - rev_yoy
            m = ramp(lead, 0.10, 0.30) if lead > 0.10 else 0.0
        out.append(
            _Channel(
                "receivables_outrun_revenue",
                m,
                f"Receivables grew {rec_yoy:+.1%} vs revenue {rev_yoy:+.1%} YoY."
                if m > 0
                else "Receivables did not outrun revenue by >=10 ppt YoY.",
            )
        )

        # 5. Capex rises while organic revenue slows (severe at +20% capex).
        capex_yoy = _yoy(
            current.capex, prior_year.capex if prior_year else None
        )
        rev_slowing = self._revenue_decelerating(by_period, cur_p)
        m = (
            ramp(capex_yoy, 0.0, 0.20)
            if capex_yoy is not None and capex_yoy > 0 and rev_slowing is True
            else 0.0
        )
        out.append(
            _Channel(
                "capex_up_revenue_slowing",
                m,
                f"Capex rose {capex_yoy:+.1%} YoY while revenue growth slowed."
                if m > 0
                else "Not both: capex rising and revenue growth slowing.",
            )
        )

        # 6. Full-year FCF guidance reduced (severe at -15%).
        g_now = current.fy_fcf_guidance
        g_prev = self._prior_guidance(ordered)
        m = 0.0
        if g_now is not None and g_prev is not None and g_now < g_prev and g_prev != 0:
            m = ramp((g_prev - g_now) / abs(g_prev), 0.0, 0.15)
        out.append(
            _Channel(
                "fy_fcf_guidance_cut",
                m,
                f"Full-year FCF guidance cut to {g_now:.2f} from {g_prev:.2f}."
                if m > 0
                else "Full-year FCF guidance was not reduced.",
            )
        )

        # 7. Previously delayed deals never landed (binary).
        m = 1.0 if current.delayed_deals_recovered is False else 0.0
        out.append(
            _Channel(
                "delayed_deals_never_landed",
                m,
                "Deals attributed to 'timing' did not appear in later revenue."
                if m > 0
                else "No evidence delayed deals failed to land.",
            )
        )
        return out

    def _improvement_channels(
        self,
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
        by_period: dict[Period, FundamentalSnapshot],
    ) -> list[_Channel]:
        out: list[_Channel] = []
        cur_p = current.parsed_period

        ttm_now = _ttm_fcf(by_period, cur_p)
        ttm_prev = _ttm_fcf(by_period, cur_p.prior_year())
        m = 0.0
        if ttm_now is not None and ttm_prev is not None and ttm_prev != 0:
            rise = (ttm_now - ttm_prev) / abs(ttm_prev)
            m = ramp(rise, 0.0, 0.25) if rise > 0 else 0.0
        out.append(_Channel("ttm_fcf_rise", m, "TTM free cash flow rose YoY."))

        e = (
            current.gross_margin - prior_year.gross_margin
            if prior_year is not None
            and current.gross_margin is not None
            and prior_year.gross_margin is not None
            else None
        )
        m = ramp(e, 0.010, 0.030) if e is not None and e > 0 else 0.0
        out.append(
            _Channel("gross_margin_expansion", m, "Gross margin expanded YoY.")
        )

        yoy = self._fcf_margin_yoy(by_period, cur_p)
        m = ramp(yoy, 0.005, 0.05) if yoy is not None and yoy > 0 else 0.0
        out.append(_Channel("fcf_margin_rise", m, "FCF margin improved YoY."))

        g_now = current.fy_fcf_guidance
        g_prev = self._prior_guidance(list(by_period.values()))
        m = 0.0
        if g_now is not None and g_prev is not None and g_now > g_prev and g_prev != 0:
            m = ramp((g_now - g_prev) / abs(g_prev), 0.0, 0.15)
        out.append(
            _Channel("fy_fcf_guidance_raise", m, "Full-year FCF guidance raised.")
        )
        return out

    def _reporting_entropy(
        self,
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
    ) -> float:
        """H(R): obfuscation as *change* in disclosure vs the comparable period.

        Static incompleteness is NOT obfuscation (it lowers confidence instead).
        Only a narrowing of disclosure — fewer segments, more non-GAAP, or a
        line that was reported a year ago and is now blank — raises H(R).
        """
        if prior_year is None:
            return 0.0
        contributions: list[float] = []

        if (
            current.reported_segments is not None
            and prior_year.reported_segments is not None
            and current.reported_segments < prior_year.reported_segments
            and prior_year.reported_segments > 0
        ):
            drop = prior_year.reported_segments - current.reported_segments
            contributions.append(clip(drop / prior_year.reported_segments))

        if (
            current.non_gaap_metric_count is not None
            and prior_year.non_gaap_metric_count is not None
            and current.non_gaap_metric_count > prior_year.non_gaap_metric_count
        ):
            rise = current.non_gaap_metric_count - prior_year.non_gaap_metric_count
            contributions.append(clip(rise / max(prior_year.non_gaap_metric_count, 3)))

        # a core line reported last year, missing now = disclosure withdrawal
        for field_name in ("gross_margin", "receivables", "operating_margin"):
            if (
                getattr(prior_year, field_name) is not None
                and getattr(current, field_name) is None
            ):
                contributions.append(1.0)

        return round(noisy_or(contributions), 4)

    # --- helpers ----------------------------------------------------------
    @staticmethod
    def _prior_quarter(period: Period) -> Period | None:
        if period.quarter == 1:
            return Period(period.year - 1, 4)
        return Period(period.year, period.quarter - 1)

    def _fcf_margin_yoy(
        self, by_period: dict[Period, FundamentalSnapshot], period: Period | None
    ) -> float | None:
        if period is None:
            return None
        now = by_period.get(period)
        ago = by_period.get(period.prior_year())
        if now is None or ago is None:
            return None
        if math.isnan(now.fcf_margin) or math.isnan(ago.fcf_margin):
            return None
        return now.fcf_margin - ago.fcf_margin

    def _revenue_decelerating(
        self, by_period: dict[Period, FundamentalSnapshot], period: Period
    ) -> bool | None:
        prev_q = self._prior_quarter(period)
        if prev_q is None:
            return None
        now = by_period.get(period)
        now_ago = by_period.get(period.prior_year())
        prev = by_period.get(prev_q)
        prev_ago = by_period.get(prev_q.prior_year())
        now_g = _yoy(now.revenue, now_ago.revenue) if now and now_ago else None
        prev_g = (
            _yoy(prev.revenue, prev_ago.revenue) if prev and prev_ago else None
        )
        if now_g is None or prev_g is None:
            return None
        return now_g < prev_g

    @staticmethod
    def _prior_guidance(
        snapshots: Sequence[FundamentalSnapshot],
    ) -> float | None:
        ordered = sorted(snapshots, key=lambda s: s.parsed_period)
        with_guidance = [s for s in ordered if s.fy_fcf_guidance is not None]
        if len(with_guidance) < 2:
            return None
        return with_guidance[-2].fy_fcf_guidance

    def _state(
        self,
        breakdown_score: float,
        improve_score: float,
        d_report: float,
        has_narrative: bool,
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
        """Slow capitulation <=> tight (low-entropy) parrot consensus."""
        if not has_narrative:
            return "n/a"
        if h_narrative < 0.25:
            return "slow"
        if h_narrative < 0.60:
            return "medium"
        return "fast"

    def _confidence(
        self,
        ordered: Sequence[FundamentalSnapshot],
        by_period: dict[Period, FundamentalSnapshot],
        current: FundamentalSnapshot,
        det: Sequence[_Channel],
        imp: Sequence[_Channel],
        h_reporting: float,
        state: SignalState,
    ) -> float:
        """Evidence *depth*, not conviction in a direction. Obfuscation and
        static incompleteness LOWER confidence even as obfuscation raises the
        divergence — that tension is deliberate and kept explicit."""
        cur_p = ordered[-1].parsed_period
        has_ttm = _ttm_fcf(by_period, cur_p) is not None
        has_prior_ttm = _ttm_fcf(by_period, cur_p.prior_year()) is not None
        active = [c for c in (det if state is not SignalState.IMPROVING else imp)
                  if c.magnitude > 0]
        core_present = sum(
            getattr(current, f) is not None for f in ("gross_margin", "receivables")
        ) / 2.0
        confidence = (
            0.30
            + 0.04 * min(len(ordered), 8)
            + (0.12 if has_ttm else 0.0)
            + (0.10 if has_prior_ttm else 0.0)
            + 0.04 * min(len(active), 4)
        )
        confidence *= 0.6 + 0.4 * core_present          # static completeness
        confidence *= 1.0 - 0.5 * h_reporting            # obfuscation penalty
        return round(min(0.95, confidence), 3)

    def _metrics(
        self,
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
        by_period: dict[Period, FundamentalSnapshot],
        benign_alignment: float,
        h_narrative: float,
        h_reporting: float,
        d_report: float,
        narrative_intensity: float,
    ) -> dict[str, float | str | None]:
        cur_p = current.parsed_period
        return {
            "period": str(cur_p),
            "comparable_period": str(cur_p.prior_year()),
            "as_filed": not current.restated,
            "fcf_margin": current.fcf_margin,
            "fcf_margin_yoy": self._fcf_margin_yoy(by_period, cur_p),
            "revenue_yoy": _yoy(
                current.revenue, prior_year.revenue if prior_year else None
            ),
            "free_cash_flow_yoy": _yoy(
                current.free_cash_flow,
                prior_year.free_cash_flow if prior_year else None,
            ),
            "ttm_fcf": _ttm_fcf(by_period, cur_p),
            "ttm_fcf_prior": _ttm_fcf(by_period, cur_p.prior_year()),
            "reporting_divergence": round(d_report, 4),
            "benign_alignment": round(benign_alignment, 4),
            "narrative_entropy": round(h_narrative, 4),
            "reporting_entropy": round(h_reporting, 4),
            "narrative_intensity": narrative_intensity,
        }
