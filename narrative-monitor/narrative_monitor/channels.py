"""channels — the sector microstructure the truth is denominated in.

The divergence x entropy engine is universal. What changes across sectors is
*which line items* carry the cash-vs-story divergence. An industrial hides it in
FCF and gross margin; a bank hides it in loan-loss reserves and net charge-offs;
a REIT hides it in the FFO->AFFO wedge and same-store NOI. More estimate-laden
sectors (banks, REITs) have MORE discretion, so the narrative can diverge further
from cash — they are the richest hunting ground, not the exception.

A `ChannelSet` maps a sector onto the same seven-slot structure the engine
consumes. Every channel is comparable-period (Q4/Q4) or trailing-twelve-month and
returns a continuous [0,1] magnitude; the engine combines them with noisy-OR and
weights by narrative entropy exactly as before.

Sectors implemented: industrial (FCF/margins), financial (bank credit reserves),
reit (AFFO wedge), broker (rate carry on customer float), insurance (reserve
adequacy / combined ratio). Adding another is one subclass plus a registry entry.

Stdlib only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .entropy import clip, noisy_or, ramp
from .models import FundamentalSnapshot, Period

# a value extracted from one snapshot; None when the line item is absent
Getter = Callable[[FundamentalSnapshot], "float | None"]


@dataclass
class Channel:
    key: str
    magnitude: float  # [0,1] strength of this channel's divergence
    reason: str


# ------------------------------------------------------------------ context
@dataclass(frozen=True)
class ChannelContext:
    """Comparable-period accessors shared by every ChannelSet.

    All the seasonality-safe plumbing lives here so a channel set only has to
    say *which* line item and *how severe*, never re-derive comparable-period or
    TTM logic. `getter` callables let one set read typed fields
    (`s.free_cash_flow`) and another read `s.line_items["net_charge_offs"]`
    through the identical helpers.
    """

    ordered: Sequence[FundamentalSnapshot]
    by_period: dict[Period, FundamentalSnapshot]
    current: FundamentalSnapshot
    prior_year: FundamentalSnapshot | None

    # -- generic line-item helpers --
    @staticmethod
    def item(key: str) -> Getter:
        return lambda s: s.line_items.get(key) if s is not None else None

    def value(self, getter: Getter, snap: FundamentalSnapshot | None) -> float | None:
        return getter(snap) if snap is not None else None

    def yoy(self, getter: Getter) -> float | None:
        """Comparable-period % change of a line item (current vs prior year)."""
        now = getter(self.current)
        ago = getter(self.prior_year) if self.prior_year is not None else None
        if now is None or ago is None or ago == 0:
            return None
        return now / ago - 1.0

    def yoy_at(self, getter: Getter, period: Period) -> float | None:
        now = self.by_period.get(period)
        ago = self.by_period.get(period.prior_year())
        a = getter(now) if now else None
        b = getter(ago) if ago else None
        if a is None or b is None or b == 0:
            return None
        return a / b - 1.0

    def level_change_yoy(self, getter: Getter) -> float | None:
        """Comparable-period change in a *level/ratio* (now - year_ago)."""
        now = getter(self.current)
        ago = getter(self.prior_year) if self.prior_year is not None else None
        if now is None or ago is None:
            return None
        return now - ago

    def prior_quarter(self, period: Period) -> Period:
        if period.quarter == 1:
            return Period(period.year - 1, 4)
        return Period(period.year, period.quarter - 1)

    def margin_change_at(self, getter: Getter, period: Period | None) -> float | None:
        """Level change of a ratio getter vs its comparable period."""
        if period is None:
            return None
        now = self.by_period.get(period)
        ago = self.by_period.get(period.prior_year())
        a = getter(now) if now else None
        b = getter(ago) if ago else None
        if a is None or b is None:
            return None
        return a - b

    def ttm(self, getter: Getter, end: Period | None = None) -> float | None:
        """Trailing-twelve-month sum of a line item; None if any quarter or any
        value in the window is missing (a partial window never poses as a year)."""
        period = end or self.current.parsed_period
        total = 0.0
        for _ in range(4):
            snap = self.by_period.get(period)
            v = getter(snap) if snap else None
            if v is None:
                return None
            total += v
            period = self.prior_quarter(period)
        return total

    def decelerating(self, getter: Getter) -> bool | None:
        """Is this quarter's YoY growth of `getter` below last quarter's YoY
        growth? Comparable-period throughout (organic-growth deceleration)."""
        cur_p = self.current.parsed_period
        prev_q = self.prior_quarter(cur_p)
        now_g = self.yoy_at(getter, cur_p)
        prev_g = self.yoy_at(getter, prev_q)
        if now_g is None or prev_g is None:
            return None
        return now_g < prev_g

    def prior_guidance(self, getter: Getter) -> float | None:
        """The most recent non-None guidance value *before* the latest one."""
        vals = [
            v for s in self.ordered
            if (v := getter(s)) is not None
        ]
        return vals[-2] if len(vals) >= 2 else None


# ------------------------------------------------------------------ base
class ChannelSet(ABC):
    """A sector's microstructure. The engine treats every set identically."""

    sector: str = "generic"

    @abstractmethod
    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        ...

    @abstractmethod
    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        ...

    @abstractmethod
    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        """The sector's primary cash metric over TTM. The engine requires a
        complete window of this before a signal can be execution-eligible."""

    def reporting_entropy(self, ctx: ChannelContext) -> float:
        """H(R): obfuscation as a *narrowing* of disclosure vs the comparable
        period. Shared default: fewer segments, more non-GAAP, or a core line
        reported a year ago now blank. Sectors override to add their own tells."""
        cur, py = ctx.current, ctx.prior_year
        if py is None:
            return 0.0
        contributions: list[float] = []
        if (
            cur.reported_segments is not None
            and py.reported_segments is not None
            and cur.reported_segments < py.reported_segments
            and py.reported_segments > 0
        ):
            contributions.append(
                clip((py.reported_segments - cur.reported_segments) / py.reported_segments)
            )
        if (
            cur.non_gaap_metric_count is not None
            and py.non_gaap_metric_count is not None
            and cur.non_gaap_metric_count > py.non_gaap_metric_count
        ):
            contributions.append(
                clip((cur.non_gaap_metric_count - py.non_gaap_metric_count)
                     / max(py.non_gaap_metric_count, 3))
            )
        return round(noisy_or(contributions), 4)


# ------------------------------------------------------------------ industrial
class IndustrialChannels(ChannelSet):
    """FCF / margin / receivables microstructure — the original set."""

    sector = "industrial"

    _FCF = staticmethod(lambda s: s.free_cash_flow if s else None)
    _GM = staticmethod(lambda s: s.gross_margin if s else None)
    _REV = staticmethod(lambda s: s.revenue if s else None)
    _CAPEX = staticmethod(lambda s: s.capex if s else None)
    _REC = staticmethod(lambda s: s.receivables if s else None)
    _GUID = staticmethod(lambda s: s.fy_fcf_guidance if s else None)

    @staticmethod
    def _fcf_margin(s: FundamentalSnapshot | None) -> float | None:
        if s is None or s.revenue == 0:
            return None
        return s.free_cash_flow / s.revenue

    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        return ctx.ttm(self._FCF)

    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period

        # 1. TTM FCF declines (severe at -25%)
        now, prev = ctx.ttm(self._FCF), ctx.ttm(self._FCF, cur_p.prior_year())
        m = _decline(now, prev, 0.25)
        out.append(Channel("ttm_fcf_decline", m,
            f"TTM free cash flow fell to {now:.2f} from {prev:.2f}." if m > 0
            else "TTM FCF did not decline (or window incomplete)."))

        # 2. FCF margin declines two consecutive comparable periods (severe -5pt)
        m = _two_period_margin(ctx, self._fcf_margin, floor=0.005, severe=0.05)
        out.append(Channel("fcf_margin_two_period_decline", m,
            "FCF margin fell YoY two consecutive quarters." if m > 0
            else "FCF margin did not fall YoY two consecutive quarters."))

        # 3. Gross margin contracts (>100 bps floor, 300 bps severe)
        c = ctx.level_change_yoy(self._GM)
        m = ramp(-c, 0.010, 0.030) if c is not None and c < 0 else 0.0
        out.append(Channel("gross_margin_contraction", m,
            f"Gross margin contracted {c:+.1%} YoY." if m > 0
            else "Gross margin did not contract >100 bps YoY."))

        # 4. Receivables outrun revenue (10 ppt floor, 30 ppt severe)
        m = _lead(ctx.yoy(self._REC), ctx.yoy(self._REV), 0.10, 0.30)
        out.append(Channel("receivables_outrun_revenue", m,
            "Receivables outran revenue YoY." if m > 0
            else "Receivables did not outrun revenue by >=10 ppt YoY."))

        # 5. Capex rises while organic revenue slows (severe +20% capex)
        cy = ctx.yoy(self._CAPEX)
        m = (ramp(cy, 0.0, 0.20)
             if cy is not None and cy > 0 and ctx.decelerating(self._REV) else 0.0)
        out.append(Channel("capex_up_revenue_slowing", m,
            f"Capex rose {cy:+.1%} YoY while revenue slowed." if m > 0
            else "Not both: capex rising and revenue slowing."))

        # 6. Full-year FCF guidance reduced (severe -15%)
        m = _guidance_cut(ctx, self._GUID)
        out.append(Channel("fy_fcf_guidance_cut", m,
            "Full-year FCF guidance was reduced." if m > 0
            else "Full-year FCF guidance was not reduced."))

        # 7. Previously delayed deals never landed (binary)
        m = 1.0 if ctx.current.delayed_deals_recovered is False else 0.0
        out.append(Channel("delayed_deals_never_landed", m,
            "Deals attributed to 'timing' never appeared in revenue." if m > 0
            else "No evidence delayed deals failed to land."))
        return out

    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period
        now, prev = ctx.ttm(self._FCF), ctx.ttm(self._FCF, cur_p.prior_year())
        out.append(Channel("ttm_fcf_rise", _rise(now, prev, 0.25),
                            "TTM free cash flow rose YoY."))
        c = ctx.level_change_yoy(self._GM)
        out.append(Channel("gross_margin_expansion",
                           ramp(c, 0.010, 0.030) if c is not None and c > 0 else 0.0,
                           "Gross margin expanded YoY."))
        return out


# ------------------------------------------------------------------ financials
class FinancialChannels(ChannelSet):
    """Bank / insurer microstructure: credit-reserve adequacy is the truth.

    The narrative "credit remains benign" dies when the allowance is drained to
    flatter EPS while charge-offs and non-performers accelerate. line_items:
      provision_for_credit_losses, net_charge_offs, allowance_for_loan_losses,
      gross_loans, nonperforming_assets, net_interest_margin,
      tangible_book_value_per_share, aoci_unrealized_loss, tangible_common_equity,
      net_income (primary cash proxy), fy_nii_guidance
    """

    sector = "financial"

    _NI = staticmethod(ChannelContext.item("net_income"))
    _NIM = staticmethod(ChannelContext.item("net_interest_margin"))
    _ACL = staticmethod(ChannelContext.item("allowance_for_loan_losses"))
    _LOANS = staticmethod(ChannelContext.item("gross_loans"))
    _NCO = staticmethod(ChannelContext.item("net_charge_offs"))
    _PROV = staticmethod(ChannelContext.item("provision_for_credit_losses"))
    _NPA = staticmethod(ChannelContext.item("nonperforming_assets"))
    _TBVPS = staticmethod(ChannelContext.item("tangible_book_value_per_share"))
    _GUID = staticmethod(ChannelContext.item("fy_nii_guidance"))

    @staticmethod
    def _coverage(s: FundamentalSnapshot | None) -> float | None:
        if s is None:
            return None
        acl, loans = s.line_items.get("allowance_for_loan_losses"), s.line_items.get("gross_loans")
        if acl is None or not loans:
            return None
        return acl / loans

    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        return ctx.ttm(self._NI)

    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period

        # 1. Reserve build below net charge-offs -> draining the allowance
        prov, nco = self._PROV(ctx.current), self._NCO(ctx.current)
        m = 0.0
        if prov is not None and nco is not None and nco > 0 and prov < nco:
            m = ramp((nco - prov) / nco, 0.05, 0.50)
        out.append(Channel("reserve_release_below_chargeoffs", m,
            f"Provision {prov:.2f} ran below net charge-offs {nco:.2f}." if m > 0
            else "Provisions covered net charge-offs."))

        # 2. NIM compresses two consecutive comparable periods (severe -40 bps)
        m = _two_period_margin(ctx, self._NIM, floor=0.0005, severe=0.004)
        out.append(Channel("nim_two_period_compression", m,
            "Net interest margin compressed YoY two quarters running." if m > 0
            else "NIM did not compress YoY two consecutive quarters."))

        # 3. Allowance coverage ratio falls (>10 bps floor, 50 bps severe)
        c = ctx.level_change_yoy(self._coverage)
        m = ramp(-c, 0.001, 0.005) if c is not None and c < 0 else 0.0
        out.append(Channel("allowance_coverage_decline", m,
            f"Allowance coverage fell {c:+.2%} of loans YoY." if m > 0
            else "Allowance coverage did not fall materially."))

        # 4. Non-performing assets outrun loan growth (10 ppt floor)
        m = _lead(ctx.yoy(self._NPA), ctx.yoy(self._LOANS), 0.10, 0.40)
        out.append(Channel("npa_outrun_loans", m,
            "Non-performing assets outran loan growth YoY." if m > 0
            else "NPAs did not outrun loan growth by >=10 ppt."))

        # 5. Coverage falling WHILE charge-offs rise -> reserve inadequacy
        cov_down = c is not None and c < 0
        nco_yoy = ctx.yoy(self._NCO)
        m = (ramp(nco_yoy, 0.0, 0.50)
             if cov_down and nco_yoy is not None and nco_yoy > 0 else 0.0)
        out.append(Channel("reserve_inadequacy", m,
            "Allowance coverage falling while charge-offs rise YoY." if m > 0
            else "No combined coverage-down / charge-offs-up signal."))

        # 6. Net-interest-income guidance reduced
        m = _guidance_cut(ctx, self._GUID)
        out.append(Channel("nii_guidance_cut", m,
            "Net-interest-income guidance was reduced." if m > 0
            else "NII guidance was not reduced."))

        # 7. Tangible book value per share erodes YoY
        tb = ctx.yoy(self._TBVPS)
        m = ramp(-tb, 0.0, 0.10) if tb is not None and tb < 0 else 0.0
        out.append(Channel("tbvps_erosion", m,
            f"Tangible book value per share fell {tb:+.1%} YoY." if m > 0
            else "Tangible book value per share did not erode."))
        return out

    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period
        now, prev = ctx.ttm(self._NI), ctx.ttm(self._NI, cur_p.prior_year())
        out.append(Channel("ttm_net_income_rise", _rise(now, prev, 0.25),
                            "TTM net income rose YoY."))
        c = ctx.level_change_yoy(self._coverage)
        out.append(Channel("allowance_coverage_build",
                           ramp(c, 0.001, 0.005) if c is not None and c > 0 else 0.0,
                           "Allowance coverage strengthened YoY."))
        return out

    def reporting_entropy(self, ctx: ChannelContext) -> float:
        """Adds the bank tell: unrealized securities losses (AOCI) growing vs
        tangible common equity — burying mark risk while the narrative stays
        calm (the SVB pattern)."""
        base = super().reporting_entropy(ctx)
        cur, py = ctx.current, ctx.prior_year
        extra = 0.0
        aoci = cur.line_items.get("aoci_unrealized_loss")
        tce = cur.line_items.get("tangible_common_equity")
        aoci_prev = py.line_items.get("aoci_unrealized_loss") if py else None
        if aoci is not None and tce and aoci_prev is not None and aoci > aoci_prev:
            extra = ramp(aoci / tce, 0.05, 0.30)  # loss vs capital
        return round(noisy_or([base, extra]), 4)


# ------------------------------------------------------------------ REITs
class ReitChannels(ChannelSet):
    """REIT microstructure: AFFO and same-store NOI are the truth.

    The narrative "growth is strong" (on acquisitions) dies when same-store NOI
    decelerates, the FFO->AFFO wedge widens, and the dividend runs above AFFO.
    line_items: ffo, affo, total_noi, same_store_noi, occupancy,
      straight_line_rent_receivable, capitalized_interest, dividend_per_share,
      affo_per_share, fy_affo_guidance
    """

    sector = "reit"

    _AFFO = staticmethod(ChannelContext.item("affo"))
    _FFO = staticmethod(ChannelContext.item("ffo"))
    _SSNOI = staticmethod(ChannelContext.item("same_store_noi"))
    _TOTNOI = staticmethod(ChannelContext.item("total_noi"))
    _SLR = staticmethod(ChannelContext.item("straight_line_rent_receivable"))
    _CAPINT = staticmethod(ChannelContext.item("capitalized_interest"))
    _OCC = staticmethod(ChannelContext.item("occupancy"))
    _GUID = staticmethod(ChannelContext.item("fy_affo_guidance"))

    @staticmethod
    def _affo_wedge(s: FundamentalSnapshot | None) -> float | None:
        """1 - AFFO/FFO: how much of FFO evaporates after real capex + non-cash
        rent. A widening wedge is the REIT quality tell."""
        if s is None:
            return None
        ffo, affo = s.line_items.get("ffo"), s.line_items.get("affo")
        if not ffo or affo is None:
            return None
        return 1.0 - affo / ffo

    @staticmethod
    def _payout(s: FundamentalSnapshot | None) -> float | None:
        if s is None:
            return None
        dps, affops = s.line_items.get("dividend_per_share"), s.line_items.get("affo_per_share")
        if dps is None or not affops:
            return None
        return dps / affops

    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        return ctx.ttm(self._AFFO)

    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period

        # 1. TTM AFFO declines (severe -25%)
        now, prev = ctx.ttm(self._AFFO), ctx.ttm(self._AFFO, cur_p.prior_year())
        m = _decline(now, prev, 0.25)
        out.append(Channel("ttm_affo_decline", m,
            f"TTM AFFO fell to {now:.2f} from {prev:.2f}." if m > 0
            else "TTM AFFO did not decline (or window incomplete)."))

        # 2. Same-store NOI margin proxy declines two comparable periods
        m = _two_period_yoy_decline(ctx, self._SSNOI, floor=0.005, severe=0.05)
        out.append(Channel("same_store_noi_two_period_decline", m,
            "Same-store NOI fell YoY two quarters running." if m > 0
            else "Same-store NOI did not fall YoY two consecutive quarters."))

        # 3. FFO->AFFO wedge widens (>100 bps floor, 500 bps severe)
        c = ctx.level_change_yoy(self._affo_wedge)
        m = ramp(c, 0.010, 0.050) if c is not None and c > 0 else 0.0
        out.append(Channel("affo_wedge_widening", m,
            f"FFO->AFFO wedge widened {c:+.1%} YoY." if m > 0
            else "FFO->AFFO wedge did not widen."))

        # 4. Straight-line rent receivable outruns cash NOI (10 ppt floor)
        m = _lead(ctx.yoy(self._SLR), ctx.yoy(self._SSNOI), 0.10, 0.40)
        out.append(Channel("straightline_rent_outrun_noi", m,
            "Straight-line rent receivable outran same-store NOI YoY." if m > 0
            else "Straight-line rent did not outrun NOI by >=10 ppt."))

        # 5. Capitalized interest rises while occupancy / organic NOI slows
        cy = ctx.yoy(self._CAPINT)
        m = (ramp(cy, 0.0, 0.25)
             if cy is not None and cy > 0 and ctx.decelerating(self._SSNOI) else 0.0)
        out.append(Channel("capitalized_interest_up_noi_slowing", m,
            f"Capitalized interest rose {cy:+.1%} while NOI slowed." if m > 0
            else "Not both: capitalized interest up and NOI slowing."))

        # 6. AFFO guidance reduced
        m = _guidance_cut(ctx, self._GUID)
        out.append(Channel("affo_guidance_cut", m,
            "AFFO guidance was reduced." if m > 0 else "AFFO guidance was not reduced."))

        # 7. Dividend runs above AFFO (payout > 100%)
        payout = self._payout(ctx.current)
        m = ramp(payout - 1.0, 0.0, 0.20) if payout is not None and payout > 1.0 else 0.0
        out.append(Channel("dividend_above_affo", m,
            f"Dividend/AFFO payout is {payout:.0%} — above cash." if m > 0
            else "Dividend is covered by AFFO."))
        return out

    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period
        now, prev = ctx.ttm(self._AFFO), ctx.ttm(self._AFFO, cur_p.prior_year())
        out.append(Channel("ttm_affo_rise", _rise(now, prev, 0.25), "TTM AFFO rose YoY."))
        c = ctx.level_change_yoy(self._affo_wedge)
        out.append(Channel("affo_wedge_narrowing",
                           ramp(-c, 0.010, 0.050) if c is not None and c < 0 else 0.0,
                           "FFO->AFFO wedge narrowed YoY."))
        return out


# ------------------------------------------------------------------ brokers
class BrokerChannels(ChannelSet):
    """Broker / capital-markets microstructure: earnings quality BY SOURCE.

    The narrative "durable franchise earnings" over a P&L that is really a
    rate-carry on customer float. The breakdown is the carry turning — net
    interest income compressing and the float base eroding (cash sorting) —
    while the sell-side still calls it a franchise. line_items:
      net_interest_income, pretax_income, customer_credit_balances,
      commission_revenue, rate_sensitivity_25bp (annual NII lost per -25 bps),
      net_income, fy_nii_guidance
    """

    sector = "broker"

    _NII = staticmethod(ChannelContext.item("net_interest_income"))
    _FLOAT = staticmethod(ChannelContext.item("customer_credit_balances"))
    _COMM = staticmethod(ChannelContext.item("commission_revenue"))
    _RATESENS = staticmethod(ChannelContext.item("rate_sensitivity_25bp"))
    _NI = staticmethod(ChannelContext.item("net_income"))
    _GUID = staticmethod(ChannelContext.item("fy_nii_guidance"))

    @staticmethod
    def _nii_reliance(s: FundamentalSnapshot | None) -> float | None:
        if s is None:
            return None
        nii, pretax = s.line_items.get("net_interest_income"), s.line_items.get("pretax_income")
        if nii is None or not pretax:
            return None
        return nii / pretax

    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        return ctx.ttm(self._NI)

    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period

        # 1. TTM net income declines (severe -25%)
        now, prev = ctx.ttm(self._NI), ctx.ttm(self._NI, cur_p.prior_year())
        m = _decline(now, prev, 0.25)
        out.append(Channel("ttm_net_income_decline", m,
            f"TTM net income fell to {now:.0f} from {prev:.0f}." if m > 0
            else "TTM net income did not decline (or window incomplete)."))

        # 2. Net interest income compresses two consecutive comparable periods
        m = _two_period_yoy_decline(ctx, self._NII, floor=0.02, severe=0.20)
        out.append(Channel("nii_two_period_compression", m,
            "Net interest income compressed YoY two quarters running." if m > 0
            else "NII did not compress YoY two consecutive quarters."))

        # 3. Rate-carry reliance: NII as a share of pretax is high (the P&L IS
        #    interest, not franchise) — 45% floor, 75% severe
        r = self._nii_reliance(ctx.current)
        m = ramp(r, 0.45, 0.75) if r is not None and r > 0.45 else 0.0
        out.append(Channel("nii_reliance_high", m,
            f"Net interest income is {r:.0%} of pretax — a rate carry." if m > 0
            else "Net interest income is not an outsized share of pretax."))

        # 4. Customer float erodes YoY (cash sorting out of idle balances)
        fy = ctx.yoy(self._FLOAT)
        m = ramp(-fy, 0.0, 0.20) if fy is not None and fy < 0 else 0.0
        out.append(Channel("customer_float_erosion", m,
            f"Customer credit balances fell {fy:+.1%} YoY (cash sorting)." if m > 0
            else "Customer float did not erode YoY."))

        # 5. NII compressing while commissions don't compensate
        niy, cy = ctx.yoy(self._NII), ctx.yoy(self._COMM)
        m = (ramp(-niy, 0.0, 0.20)
             if niy is not None and niy < 0 and (cy is None or cy <= 0) else 0.0)
        out.append(Channel("nii_down_commissions_flat", m,
            "NII fell YoY and commissions did not compensate." if m > 0
            else "Not both: NII down and commissions flat/down."))

        # 6. Net-interest-income guidance reduced
        m = _guidance_cut(ctx, self._GUID)
        out.append(Channel("nii_guidance_cut", m,
            "Net-interest-income guidance was reduced." if m > 0
            else "NII guidance was not reduced."))

        # 7. The coiled spring: a rate cut wipes a large share of earnings
        rs, ttm_ni = self._RATESENS(ctx.current), ctx.ttm(self._NI)
        m = (ramp(rs / ttm_ni, 0.05, 0.30)
             if rs is not None and ttm_ni and ttm_ni > 0 else 0.0)
        out.append(Channel("rate_cut_earnings_exposure", m,
            "Disclosed rate sensitivity is a large share of earnings." if m > 0
            else "Rate sensitivity is a modest share of earnings."))
        return out

    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period
        now, prev = ctx.ttm(self._NI), ctx.ttm(self._NI, cur_p.prior_year())
        out.append(Channel("ttm_net_income_rise", _rise(now, prev, 0.25),
                            "TTM net income rose YoY."))
        fy = ctx.yoy(self._FLOAT)
        out.append(Channel("customer_float_growth",
                           ramp(fy, 0.0, 0.20) if fy is not None and fy > 0 else 0.0,
                           "Customer float grew YoY."))
        return out


# ------------------------------------------------------------------ insurers
class InsuranceChannels(ChannelSet):
    """Insurance microstructure: reserve adequacy and underwriting discipline.

    The narrative "great underwriting / profitable" propped up by prior-year
    reserve releases while the current accident year deteriorates and the
    combined ratio crosses 100. Investment income masks an underwriting loss.
    line_items: combined_ratio, loss_ratio, accident_year_loss_ratio,
      favorable_reserve_development (>0 release, <0 adverse strengthening, $),
      pretax_income, net_premiums_written, net_income, fy_combined_ratio_guidance
    """

    sector = "insurance"

    _COMBINED = staticmethod(ChannelContext.item("combined_ratio"))
    _LOSS = staticmethod(ChannelContext.item("loss_ratio"))
    _AYLOSS = staticmethod(ChannelContext.item("accident_year_loss_ratio"))
    _DEV = staticmethod(ChannelContext.item("favorable_reserve_development"))
    _PRETAX = staticmethod(ChannelContext.item("pretax_income"))
    _NPW = staticmethod(ChannelContext.item("net_premiums_written"))
    _NI = staticmethod(ChannelContext.item("net_income"))
    _GUID = staticmethod(ChannelContext.item("fy_combined_ratio_guidance"))

    def primary_ttm(self, ctx: ChannelContext) -> float | None:
        return ctx.ttm(self._NI)

    def deterioration(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []

        # 1. Combined ratio deteriorates (rises) two consecutive comparable periods
        m = _two_period_level_rise(ctx, self._COMBINED, floor=0.005, severe=0.05)
        out.append(Channel("combined_ratio_two_period_rise", m,
            "Combined ratio worsened YoY two quarters running." if m > 0
            else "Combined ratio did not worsen YoY two consecutive quarters."))

        # 2. Reserve-release reliance: favorable development a big share of pretax
        dev, pretax = self._DEV(ctx.current), self._PRETAX(ctx.current)
        m = 0.0
        if dev is not None and pretax and dev > 0:
            m = ramp(dev / pretax, 0.05, 0.30)
        out.append(Channel("reserve_release_reliance", m,
            "Prior-year reserve releases are propping up pretax income." if m > 0
            else "Earnings are not leaning on reserve releases."))

        # 3. Accident-year loss ratio worse than the reported loss ratio
        ay, reported = self._AYLOSS(ctx.current), self._LOSS(ctx.current)
        gap = ay - reported if ay is not None and reported is not None else None
        m = ramp(gap, 0.02, 0.10) if gap is not None and gap > 0 else 0.0
        out.append(Channel("accident_year_worse_than_reported", m,
            "Current accident-year loss ratio exceeds the reported ratio." if m > 0
            else "Accident-year and reported loss ratios are aligned."))

        # 4. Premiums grow fast while the loss ratio rises -> buying business
        npw_yoy = ctx.yoy(self._NPW)
        loss_rising = ctx.level_change_yoy(self._LOSS)
        m = (ramp(npw_yoy, 0.10, 0.30)
             if npw_yoy is not None and npw_yoy > 0.10
             and loss_rising is not None and loss_rising > 0 else 0.0)
        out.append(Channel("npw_growth_while_loss_rising", m,
            f"Premiums grew {npw_yoy:+.1%} YoY while the loss ratio rose." if m > 0
            else "Not both: premium growth and a rising loss ratio."))

        # 5. Underwriting loss masked by investment income (combined ratio > 1)
        cr = self._COMBINED(ctx.current)
        m = ramp(cr - 1.0, 0.0, 0.10) if cr is not None and cr > 1.0 else 0.0
        out.append(Channel("underwriting_loss_masked", m,
            f"Combined ratio {cr:.0%} is an underwriting loss." if m > 0
            else "Underwriting is at or below breakeven."))

        # 6. Combined-ratio guidance worsened (guided higher)
        m = _guidance_worse_up(ctx, self._GUID)
        out.append(Channel("combined_ratio_guidance_worse", m,
            "Full-year combined-ratio guidance was raised (worse)." if m > 0
            else "Combined-ratio guidance was not raised."))

        # 7. Adverse prior-year development -> they were under-reserved
        m = 0.0
        if dev is not None and pretax and dev < 0:
            m = ramp(-dev / pretax, 0.02, 0.20)
        out.append(Channel("adverse_reserve_development", m,
            "Prior-year reserves were strengthened (under-reserved)." if m > 0
            else "No adverse prior-year reserve development."))
        return out

    def improvement(self, ctx: ChannelContext) -> list[Channel]:
        out: list[Channel] = []
        cur_p = ctx.current.parsed_period
        now, prev = ctx.ttm(self._NI), ctx.ttm(self._NI, cur_p.prior_year())
        out.append(Channel("ttm_net_income_rise", _rise(now, prev, 0.25),
                            "TTM net income rose YoY."))
        # combined ratio improving (falling) YoY
        c = ctx.level_change_yoy(self._COMBINED)
        out.append(Channel("combined_ratio_improving",
                           ramp(-c, 0.005, 0.05) if c is not None and c < 0 else 0.0,
                           "Combined ratio improved YoY."))
        return out


# ------------------------------------------------------------------ shared ramps
def _decline(now: float | None, prev: float | None, severe: float) -> float:
    if now is None or prev is None or prev == 0:
        return 0.0
    d = (prev - now) / abs(prev)
    return ramp(d, 0.0, severe) if d > 0 else 0.0


def _rise(now: float | None, prev: float | None, severe: float) -> float:
    if now is None or prev is None or prev == 0:
        return 0.0
    r = (now - prev) / abs(prev)
    return ramp(r, 0.0, severe) if r > 0 else 0.0


def _lead(a_yoy: float | None, b_yoy: float | None, floor: float, severe: float) -> float:
    if a_yoy is None or b_yoy is None:
        return 0.0
    lead = a_yoy - b_yoy
    return ramp(lead, floor, severe) if lead > floor else 0.0


def _guidance_cut(ctx: ChannelContext, getter: Getter) -> float:
    now = getter(ctx.current)
    prev = ctx.prior_guidance(getter)
    if now is None or prev is None or prev == 0 or now >= prev:
        return 0.0
    return ramp((prev - now) / abs(prev), 0.0, 0.15)


def _two_period_margin(
    ctx: ChannelContext, getter: Getter, floor: float, severe: float
) -> float:
    """A ratio getter falling (level) YoY for two consecutive comparable quarters."""
    cur_p = ctx.current.parsed_period
    this = ctx.margin_change_at(getter, cur_p)
    last = ctx.margin_change_at(getter, ctx.prior_quarter(cur_p))
    if this is None or last is None or this > -floor or last > -floor:
        return 0.0
    return ramp(min(-this, -last), floor, severe)


def _two_period_yoy_decline(
    ctx: ChannelContext, getter: Getter, floor: float, severe: float
) -> float:
    """A level getter whose YoY % change is negative for two consecutive quarters."""
    cur_p = ctx.current.parsed_period
    this = ctx.yoy_at(getter, cur_p)
    last = ctx.yoy_at(getter, ctx.prior_quarter(cur_p))
    if this is None or last is None or this > -floor or last > -floor:
        return 0.0
    return ramp(min(-this, -last), floor, severe)


def _two_period_level_rise(
    ctx: ChannelContext, getter: Getter, floor: float, severe: float
) -> float:
    """A ratio getter *rising* (level) YoY for two consecutive quarters — used
    where higher is worse (a combined ratio climbing toward and past 100)."""
    cur_p = ctx.current.parsed_period
    this = ctx.margin_change_at(getter, cur_p)
    last = ctx.margin_change_at(getter, ctx.prior_quarter(cur_p))
    if this is None or last is None or this < floor or last < floor:
        return 0.0
    return ramp(min(this, last), floor, severe)


def _guidance_worse_up(ctx: ChannelContext, getter: Getter) -> float:
    """Guidance for a metric where higher is worse (combined ratio) revised up."""
    now = getter(ctx.current)
    prev = ctx.prior_guidance(getter)
    if now is None or prev is None or prev == 0 or now <= prev:
        return 0.0
    return ramp((now - prev) / abs(prev), 0.0, 0.15)


# ------------------------------------------------------------------ registry
CHANNEL_SETS: dict[str, ChannelSet] = {
    "industrial": IndustrialChannels(),
    "financial": FinancialChannels(),
    "reit": ReitChannels(),
    "broker": BrokerChannels(),
    "insurance": InsuranceChannels(),
}


def channel_set_for(sector: str) -> ChannelSet:
    return CHANNEL_SETS.get(sector, CHANNEL_SETS["industrial"])
