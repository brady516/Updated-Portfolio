"""signal_engine — evidence scoring and state transitions.

This is where a claim meets the financials. It answers the three questions the
whole project is built around:

    1. What is the narrative?          (handed in as claims)
    2. Has it shown up in the data?    (the 7 confirmation criteria below)
    3. Is the evidence strong enough?  (state + execution_eligible)

Two rules make it trustworthy:

  * Every comparison is COMPARABLE-PERIOD (Q4 vs Q4, Q3 vs Q3) or trailing
    twelve months. Sequential quarters are never compared, because a Q4->Q1
    cash-flow drop is seasonality, not deterioration.
  * Confirmation is a COUNT of independent criteria, not a headline. "Confirmed
    deterioration requires at least three of seven." A management explanation
    cannot manufacture a single one of them.

Stdlib only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from .models import (
    FundamentalSnapshot,
    NarrativeClaim,
    Period,
    Signal,
    SignalState,
)

# --- thresholds (all comparable-period unless noted) ------------------------
FCF_MARGIN_DROP = 0.005          # 50 bps YoY, applied over two periods
GROSS_MARGIN_CONTRACTION = 0.010  # 100 bps YoY
RECEIVABLES_LEAD = 0.10          # receivables YoY - revenue YoY >= 10 ppt
GROSS_MARGIN_EXPANSION = 0.010
FCF_MARGIN_RISE = 0.005
CONFIRMED_MIN_CRITERIA = 3       # "at least three of seven"
EXECUTION_MIN_CONFIDENCE = 0.75


@dataclass
class _Criterion:
    key: str
    supported: bool
    reason: str


def _index_by_period(
    snapshots: Sequence[FundamentalSnapshot],
) -> dict[Period, FundamentalSnapshot]:
    return {snap.parsed_period: snap for snap in snapshots}


def _yoy(current: float | None, year_ago: float | None) -> float | None:
    """Comparable-period percentage change; None if not computable."""
    if current is None or year_ago is None or year_ago == 0:
        return None
    return current / year_ago - 1.0


def _ttm_fcf(
    by_period: dict[Period, FundamentalSnapshot], end: Period
) -> float | None:
    """Trailing-twelve-month FCF ending at `end` (that quarter + the prior 3).

    Returns None unless all four comparable quarters are present, so a partial
    window never masquerades as a full-year figure.
    """
    total = 0.0
    period = end
    for _ in range(4):
        snap = by_period.get(period)
        if snap is None:
            return None
        total += snap.free_cash_flow
        # step back one quarter
        period = (
            Period(period.year - 1, 4)
            if period.quarter == 1
            else Period(period.year, period.quarter - 1)
        )
    return total


class SignalEngine:
    """Turns snapshots + extracted claims into a gated Signal."""

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
        prior_year = by_period.get(cur_p.prior_year())  # comparable period

        deterioration = self._deterioration_criteria(
            ordered, by_period, current, prior_year
        )
        improvement = self._improvement_criteria(current, prior_year, by_period)

        confirmed = [c for c in deterioration if c.supported]
        improved = [c for c in improvement if c.supported]
        d_count = len(confirmed)
        i_count = len(improved)

        state = self._state(
            narrative_intensity, d_count, i_count
        )
        confidence = self._confidence(ordered, by_period, d_count, i_count)
        execution_eligible = (
            state is SignalState.CONFIRMED_DETERIORATION
            and confidence >= EXECUTION_MIN_CONFIDENCE
            and _ttm_fcf(by_period, cur_p) is not None
        )

        reasons = [c.reason for c in confirmed] or [
            c.reason for c in improved
        ]
        if not reasons:
            reasons = ["No comparable-period criterion was triggered."]
        if state is SignalState.NARRATIVE_ONLY:
            reasons.insert(
                0,
                "Narrative present but financials do not confirm it "
                f"({d_count}/7 criteria).",
            )

        metrics = self._metrics(
            current, prior_year, by_period, d_count, i_count, narrative_intensity
        )

        return Signal(
            ticker=current.ticker,
            state=state,
            score=float(d_count - i_count),
            confidence=confidence,
            generated_at=datetime.now(UTC).isoformat(),
            reasons=reasons,
            metrics=metrics,
            execution_eligible=execution_eligible,
            claims=[c.label for c in claims],
            confirmed_criteria=[c.key for c in confirmed],
        )

    # --- the seven deterioration criteria ---------------------------------
    def _deterioration_criteria(
        self,
        ordered: Sequence[FundamentalSnapshot],
        by_period: dict[Period, FundamentalSnapshot],
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
    ) -> list[_Criterion]:
        out: list[_Criterion] = []
        cur_p = current.parsed_period

        # 1. Trailing-twelve-month FCF declines vs the prior TTM window.
        ttm_now = _ttm_fcf(by_period, cur_p)
        # prior TTM ends one year earlier (same quarter, year-1).
        ttm_prev = _ttm_fcf(by_period, cur_p.prior_year())
        supported = ttm_now is not None and ttm_prev is not None and ttm_now < ttm_prev
        out.append(
            _Criterion(
                "ttm_fcf_decline",
                supported,
                f"TTM free cash flow fell to {ttm_now:.2f} from {ttm_prev:.2f}."
                if supported
                else "TTM FCF did not decline (or window incomplete).",
            )
        )

        # 2. FCF margin declines for two consecutive COMPARABLE periods.
        prev_q = self._prior_quarter(cur_p)
        this_yoy = self._fcf_margin_yoy(by_period, cur_p)
        last_yoy = self._fcf_margin_yoy(by_period, prev_q) if prev_q else None
        supported = (
            this_yoy is not None
            and last_yoy is not None
            and this_yoy <= -FCF_MARGIN_DROP
            and last_yoy <= -FCF_MARGIN_DROP
        )
        out.append(
            _Criterion(
                "fcf_margin_two_period_decline",
                supported,
                "FCF margin fell year-over-year for two consecutive quarters "
                f"({last_yoy:+.1%} then {this_yoy:+.1%})."
                if supported
                else "FCF margin did not fall YoY in two consecutive quarters.",
            )
        )

        # 3. Gross margin contracts by more than 100 bps YoY.
        gm_change = (
            current.gross_margin - prior_year.gross_margin
            if prior_year is not None
            and current.gross_margin is not None
            and prior_year.gross_margin is not None
            else None
        )
        supported = gm_change is not None and gm_change <= -GROSS_MARGIN_CONTRACTION
        out.append(
            _Criterion(
                "gross_margin_contraction",
                supported,
                f"Gross margin contracted {gm_change:+.1%} YoY."
                if supported
                else "Gross margin did not contract >100 bps YoY.",
            )
        )

        # 4. Receivables grow >= 10 ppt faster than revenue (YoY).
        rec_yoy = _yoy(
            current.receivables,
            prior_year.receivables if prior_year else None,
        )
        rev_yoy = _yoy(
            current.revenue, prior_year.revenue if prior_year else None
        )
        supported = (
            rec_yoy is not None
            and rev_yoy is not None
            and rec_yoy - rev_yoy >= RECEIVABLES_LEAD
        )
        out.append(
            _Criterion(
                "receivables_outrun_revenue",
                supported,
                f"Receivables grew {rec_yoy:+.1%} vs revenue {rev_yoy:+.1%} YoY."
                if supported
                else "Receivables did not outrun revenue by >=10 ppt YoY.",
            )
        )

        # 5. Capex/capitalized development rises while organic revenue slows.
        capex_yoy = _yoy(
            current.capex, prior_year.capex if prior_year else None
        )
        rev_slowing = self._revenue_decelerating(by_period, cur_p)
        supported = (
            capex_yoy is not None and capex_yoy > 0 and rev_slowing is True
        )
        out.append(
            _Criterion(
                "capex_up_revenue_slowing",
                supported,
                f"Capex rose {capex_yoy:+.1%} YoY while revenue growth slowed."
                if supported
                else "Not both: capex rising and revenue growth slowing.",
            )
        )

        # 6. Full-year FCF guidance is reduced.
        guidance_now = current.fy_fcf_guidance
        guidance_prev = self._prior_guidance(ordered)
        supported = (
            guidance_now is not None
            and guidance_prev is not None
            and guidance_now < guidance_prev
        )
        out.append(
            _Criterion(
                "fy_fcf_guidance_cut",
                supported,
                f"Full-year FCF guidance cut to {guidance_now:.2f} "
                f"from {guidance_prev:.2f}."
                if supported
                else "Full-year FCF guidance was not reduced.",
            )
        )

        # 7. Previously delayed deals fail to appear in subsequent revenue.
        supported = current.delayed_deals_recovered is False
        out.append(
            _Criterion(
                "delayed_deals_never_landed",
                supported,
                "Deals attributed to 'timing' did not appear in later revenue."
                if supported
                else "No evidence delayed deals failed to land.",
            )
        )
        return out

    def _improvement_criteria(
        self,
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
        by_period: dict[Period, FundamentalSnapshot],
    ) -> list[_Criterion]:
        out: list[_Criterion] = []
        cur_p = current.parsed_period

        ttm_now = _ttm_fcf(by_period, cur_p)
        ttm_prev = _ttm_fcf(by_period, cur_p.prior_year())
        out.append(
            _Criterion(
                "ttm_fcf_rise",
                ttm_now is not None and ttm_prev is not None and ttm_now > ttm_prev,
                "TTM free cash flow rose year-over-year.",
            )
        )

        gm_change = (
            current.gross_margin - prior_year.gross_margin
            if prior_year is not None
            and current.gross_margin is not None
            and prior_year.gross_margin is not None
            else None
        )
        out.append(
            _Criterion(
                "gross_margin_expansion",
                gm_change is not None and gm_change >= GROSS_MARGIN_EXPANSION,
                "Gross margin expanded >100 bps YoY.",
            )
        )

        fcf_yoy = self._fcf_margin_yoy(by_period, cur_p)
        out.append(
            _Criterion(
                "fcf_margin_rise",
                fcf_yoy is not None and fcf_yoy >= FCF_MARGIN_RISE,
                "FCF margin improved year-over-year.",
            )
        )

        guidance_now = current.fy_fcf_guidance
        guidance_prev = self._prior_guidance(list(by_period.values()))
        out.append(
            _Criterion(
                "fy_fcf_guidance_raise",
                guidance_now is not None
                and guidance_prev is not None
                and guidance_now > guidance_prev,
                "Full-year FCF guidance was raised.",
            )
        )
        return out

    # --- helpers ----------------------------------------------------------
    @staticmethod
    def _prior_quarter(period: Period) -> Period | None:
        if period.quarter == 1:
            return Period(period.year - 1, 4)
        return Period(period.year, period.quarter - 1)

    def _fcf_margin_yoy(
        self, by_period: dict[Period, FundamentalSnapshot], period: Period | None
    ) -> float | None:
        """Change in FCF *margin* (not level) vs the comparable prior-year
        quarter, in margin points."""
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
        """Is this quarter's YoY revenue growth lower than the prior quarter's
        YoY revenue growth? Comparable-period throughout."""
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
        """Most recent full-year FCF guidance *before* the latest one."""
        ordered = sorted(snapshots, key=lambda s: s.parsed_period)
        with_guidance = [s for s in ordered if s.fy_fcf_guidance is not None]
        if len(with_guidance) < 2:
            return None
        return with_guidance[-2].fy_fcf_guidance

    def _state(
        self, narrative_intensity: float, d_count: int, i_count: int
    ) -> SignalState:
        if d_count >= CONFIRMED_MIN_CRITERIA and d_count > i_count:
            return SignalState.CONFIRMED_DETERIORATION
        if i_count >= CONFIRMED_MIN_CRITERIA and i_count > d_count:
            return SignalState.IMPROVING
        if 1 <= d_count and d_count >= i_count:
            return SignalState.EARLY_EVIDENCE
        if narrative_intensity > 0 and d_count == 0 and i_count == 0:
            return SignalState.NARRATIVE_ONLY
        if i_count >= 1 and i_count > d_count:
            return SignalState.EARLY_EVIDENCE  # early improvement
        return SignalState.INCONCLUSIVE

    def _confidence(
        self,
        ordered: Sequence[FundamentalSnapshot],
        by_period: dict[Period, FundamentalSnapshot],
        d_count: int,
        i_count: int,
    ) -> float:
        """Confidence reflects *evidence depth*, not conviction in a direction.

        More comparable history, a complete TTM window, and more agreeing
        criteria raise it; a thin dataset caps it low so it can never clear the
        execution gate on one or two quarters.
        """
        cur_p = ordered[-1].parsed_period
        has_ttm = _ttm_fcf(by_period, cur_p) is not None
        has_prior_ttm = _ttm_fcf(by_period, cur_p.prior_year()) is not None
        dominant = max(d_count, i_count)
        confidence = (
            0.30
            + 0.04 * min(len(ordered), 8)
            + (0.12 if has_ttm else 0.0)
            + (0.10 if has_prior_ttm else 0.0)
            + 0.04 * min(dominant, 4)
        )
        return round(min(0.95, confidence), 3)

    def _metrics(
        self,
        current: FundamentalSnapshot,
        prior_year: FundamentalSnapshot | None,
        by_period: dict[Period, FundamentalSnapshot],
        d_count: int,
        i_count: int,
        narrative_intensity: float,
    ) -> dict[str, float | str | None]:
        cur_p = current.parsed_period
        return {
            "period": str(cur_p),
            "comparable_period": str(cur_p.prior_year()),
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
            "capex_intensity": current.capex_intensity,
            "cash_conversion": current.cash_conversion,
            "narrative_intensity": narrative_intensity,
            "deterioration_criteria": d_count,
            "improvement_criteria": i_count,
        }
