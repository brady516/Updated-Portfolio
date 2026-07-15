"""Synthetic sector panels — one source of truth for the demos and backtest.

Fabricated data with known effects baked in, so the sector channels and the
harness can be seen recovering them end to end. Validates the machinery, NOT the
thesis. Every breakdown panel runs a benign narrative over a filing that breaks
through that sector's own microstructure; every healthy panel is a clean
counterpart the channels must leave alone.

Stdlib only.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .models import FundamentalSnapshot, NarrativeEvent

QUARTERS = [
    ("2024-Q1", "2024-04-22"), ("2024-Q2", "2024-07-22"),
    ("2024-Q3", "2024-10-22"), ("2024-Q4", "2025-01-27"),
    ("2025-Q1", "2025-04-21"), ("2025-Q2", "2025-07-21"),
    ("2025-Q3", "2025-10-20"), ("2025-Q4", "2026-01-26"),
    ("2026-Q1", "2026-04-20"),
]
ONSET = date(2025, 4, 21)  # deterioration begins with the 2025-Q1 print

# a benign, low-entropy frame and a dissenting, admitting one
BENIGN_BODY = "pipeline remains strong, ai investment and deal timing, a temporary headwind"
ADMIT_BODY = "the demand environment is weak and we see an execution issue"


def _panel(
    ticker: str, sector: str, series: dict[str, list[float]],
    guidance_key: str | None = None, guidance: dict[str, float] | None = None,
    typed: dict[str, list[float]] | None = None,
) -> list[FundamentalSnapshot]:
    """Build 9 quarters. `series` -> line_items; `typed` -> typed fields
    (revenue/free_cash_flow/etc. for industrial and SaaS)."""
    guidance = guidance or {}
    typed = typed or {}
    out = []
    for i, (period, rep) in enumerate(QUARTERS):
        items = {k: v[i] for k, v in series.items()}
        if guidance_key and period in guidance:
            items[guidance_key] = guidance[period]
        tvals = {k: v[i] for k, v in typed.items()}
        out.append(FundamentalSnapshot(
            ticker=ticker, period=period, reported_at=rep, sector=sector,
            revenue=tvals.get("revenue", 0.0),
            free_cash_flow=tvals.get("free_cash_flow", 0.0),
            operating_cash_flow=tvals.get("operating_cash_flow", 0.0),
            capex=tvals.get("capex", 0.0),
            gross_margin=tvals.get("gross_margin"),
            receivables=tvals.get("receivables"),
            fy_fcf_guidance=tvals.get("fy_fcf_guidance"),
            line_items=items,
        ))
    return out


# ------------------------------------------------------------ breakdown panels
def industrial(ticker: str = "INDX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "industrial", {}, typed={
        "revenue":            [15.0,16.0,15.2,18.0,14.5,15.4,14.6,17.2,13.9],
        "free_cash_flow":     [2.2,2.8,2.3,6.2,1.7,2.1,1.6,4.6,1.3],
        "operating_cash_flow":[3.1,3.7,3.2,7.1,2.6,3.0,2.5,5.5,2.2],
        "capex":              [.4,.4,.4,.55,.4,.4,.4,.55,.4],
        "gross_margin":       [.560,.560,.558,.558,.550,.550,.548,.548,.535],
        "receivables":        [7.0]*9,
        "fy_fcf_guidance":    [None,None,None,None,None,12.0,11.0,10.0,9.5],
    })


def bank(ticker: str = "BANKX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.22,.22,.35,.40,.50,.55,.60],
        "provision_for_credit_losses":[.25,.25,.25,.25,.30,.32,.35,.40,.35],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.4,1.35,1.3,1.25,1.2],
        "nonperforming_assets":       [1.0,1.0,1.1,1.1,1.5,1.7,1.9,2.1,2.3],
        "net_interest_margin":        [.035,.035,.0348,.0348,.0335,.033,.0325,.032,.031],
        "tangible_book_value_per_share":[50,50,50,50,49,48,47,46,45],
        "net_income":                 [3.0,3.0,3.1,3.2,2.5,2.3,2.1,1.9,1.6],
        "aoci_unrealized_loss":       [1,1,1,1,3,4,5,6,7],
        "tangible_common_equity":     [40]*9,
    }, "fy_nii_guidance", {"2025-Q2":25.0,"2025-Q3":24.0,"2025-Q4":23.0,"2026-Q1":22.0})


def reit(ticker: str = "REITX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "reit", {
        "ffo":                        [2.0,2.1,2.0,2.3,2.0,2.1,2.0,2.3,2.0],
        "affo":                       [1.6,1.7,1.6,1.9,1.3,1.3,1.2,1.4,1.1],
        "same_store_noi":             [10,10.2,10.1,10.3,9.9,9.8,9.9,9.9,9.2],
        "straight_line_rent_receivable":[5,5,5,5,5.5,5.8,6.0,6.3,6.8],
        "capitalized_interest":       [.3,.3,.3,.3,.4,.45,.5,.55,.6],
        "dividend_per_share":         [.4]*9,
        "affo_per_share":             [.55,.58,.55,.62,.45,.44,.42,.46,.35],
    }, "fy_affo_guidance", {"2025-Q2":1.6,"2025-Q3":1.5,"2025-Q4":1.4,"2026-Q1":1.3})


def broker(ticker: str = "BROKERX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "broker", {
        "net_interest_income":     [700,750,800,850,820,780,730,690,640],
        "pretax_income":           [500,540,580,620,560,520,470,430,380],
        "net_income":              [400,430,460,490,450,420,380,350,300],
        "customer_credit_balances":[90,92,94,96,93,90,86,82,78],
        "commission_revenue":      [200,205,200,210,200,198,195,195,190],
        "rate_sensitivity_25bp":   [150,150,160,160,180,190,195,200,200],
    }, "fy_nii_guidance", {"2025-Q2":3200,"2025-Q3":3000,"2025-Q4":2800,"2026-Q1":2600})


def insurer(ticker: str = "INSURX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "insurance", {
        "combined_ratio":            [.95,.96,.95,.94,.99,1.01,1.03,1.04,1.06],
        "loss_ratio":                [.65,.66,.65,.64,.69,.71,.73,.74,.76],
        "accident_year_loss_ratio":  [.66,.67,.66,.65,.74,.77,.80,.82,.85],
        "favorable_reserve_development":[30,32,30,33,20,15,8,2,-10],
        "pretax_income":             [200,210,205,215,180,160,140,120,100],
        "net_premiums_written":      [100,102,101,103,112,116,120,124,130],
        "net_income":                [160,168,164,172,144,128,112,96,80],
    }, "fy_combined_ratio_guidance", {"2025-Q2":.99,"2025-Q3":1.01,"2025-Q4":1.03,"2026-Q1":1.05})


def lender(ticker: str = "LENDX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "lender", {
        "originations":               [50,55,60,65,75,85,95,105,115],
        "receivables":                [200,210,220,230,245,260,278,298,320],
        "allowance_for_credit_losses":[6.0,6.3,6.6,6.9,6.8,6.9,7.0,7.1,7.2],
        "net_charge_offs":            [1.0,1.0,1.1,1.1,1.4,1.7,2.1,2.5,3.0],
        "provision_for_credit_losses":[1.3,1.3,1.3,1.3,1.6,1.8,2.0,2.2,2.4],
        "delinquency_rate":           [.030,.030,.032,.032,.038,.042,.046,.050,.055],
        "vintage_early_delinquency":  [.020,.020,.021,.021,.028,.032,.036,.040,.045],
        "roll_rate":                  [.15,.15,.16,.16,.18,.20,.22,.24,.26],
        "net_income":                 [8,8.2,8.4,8.6,7.0,6.0,5.0,4.0,3.0],
    }, "fy_loss_rate_guidance", {"2025-Q2":.045,"2025-Q3":.050,"2025-Q4":.055,"2026-Q1":.060})


def saas(ticker: str = "SAASX") -> list[FundamentalSnapshot]:
    return _panel(ticker, "saas", {
        "billings":              [110,120,132,145,150,150,148,150,145],
        "crpo":                  [200,220,240,260,275,285,290,295,298],
        "net_revenue_retention": [1.25,1.24,1.22,1.20,1.15,1.10,1.05,1.02,0.98],
        "deferred_revenue":      [80,85,90,95,98,99,98,97,95],
        "sm_pct_revenue":        [.40,.40,.41,.41,.44,.46,.48,.50,.52],
        "sbc_pct_revenue":       [.15,.15,.16,.16,.18,.20,.22,.24,.26],
    }, "fy_billings_guidance", {"2025-Q2":620,"2025-Q3":600,"2025-Q4":580,"2026-Q1":560},
       typed={
        "revenue":        [100,110,120,130,140,148,155,161,166],
        "free_cash_flow": [10,11,12,13,11,9,7,5,3],
        "operating_cash_flow":[12,13,14,15,13,11,9,7,5],
        "capex":          [1,1,1,1,1,1,1,1,1],
    })


# ------------------------------------------------------------ healthy panels
def industrial_healthy(ticker: str = "INDOK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "industrial", {}, typed={
        "revenue":            [15.0,16.0,15.2,18.0,15.8,16.9,16.1,19.1,16.8],
        "free_cash_flow":     [2.2,2.8,2.3,6.2,2.5,3.1,2.7,6.6,2.9],
        "operating_cash_flow":[3.1,3.7,3.2,7.1,3.4,4.0,3.6,7.5,3.8],
        "capex":              [.4,.4,.4,.55,.4,.4,.4,.55,.4],
        "gross_margin":       [.560,.560,.558,.558,.562,.562,.560,.560,.565],
        "receivables":        [7.0]*9,
    })


def bank_healthy(ticker: str = "BANKOK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.20,.20,.19,.19,.18,.18,.17],
        "provision_for_credit_losses":[.25,.25,.25,.25,.25,.25,.25,.25,.25],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.55,1.57,1.6,1.62,1.65],
        "nonperforming_assets":       [1.0]*9,
        "net_interest_margin":        [.035]*9,
        "tangible_book_value_per_share":[50,50,51,51,52,53,54,55,56],
        "net_income":                 [3.0,3.0,3.1,3.2,3.3,3.4,3.5,3.6,3.7],
    })


def reit_healthy(ticker: str = "REITOK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "reit", {
        "ffo":                        [2.0,2.1,2.0,2.3,2.1,2.2,2.1,2.4,2.2],
        "affo":                       [1.7,1.8,1.7,2.0,1.8,1.9,1.8,2.1,1.9],
        "same_store_noi":             [10,10.2,10.1,10.3,10.4,10.6,10.6,10.8,10.9],
        "straight_line_rent_receivable":[5,5,5,5,5.1,5.1,5.2,5.2,5.3],
        "capitalized_interest":       [.3]*9,
        "dividend_per_share":         [.4]*9,
        "affo_per_share":             [.55,.58,.55,.62,.58,.61,.58,.65,.61],
    })


def broker_healthy(ticker: str = "BROKEROK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "broker", {
        "net_interest_income":     [600,620,640,660,680,700,720,740,760],
        "pretax_income":           [1600,1620,1640,1660,1680,1700,1720,1740,1760],
        "net_income":              [1200,1225,1250,1275,1300,1325,1350,1375,1400],
        "customer_credit_balances":[90,92,94,96,98,100,102,104,106],
        "commission_revenue":      [200,205,210,215,220,225,230,235,240],
        "rate_sensitivity_25bp":   [50]*9,
    })


def insurer_healthy(ticker: str = "INSUROK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "insurance", {
        "combined_ratio":            [.95,.94,.95,.94,.93,.93,.92,.92,.91],
        "loss_ratio":                [.65,.64,.65,.64,.63,.63,.62,.62,.61],
        "accident_year_loss_ratio":  [.65,.64,.65,.64,.63,.63,.62,.62,.61],
        "favorable_reserve_development":[10]*9,
        "pretax_income":             [200,205,205,210,212,214,216,218,220],
        "net_premiums_written":      [100,101,102,103,104,105,106,107,108],
        "net_income":                [160,164,164,168,170,172,174,175,176],
    })


def lender_healthy(ticker: str = "LENDOK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "lender", {
        "originations":               [50,55,60,65,75,85,95,105,115],  # same fast growth
        "receivables":                [200,210,220,230,245,260,278,298,320],
        "allowance_for_credit_losses":[6.0,6.3,6.6,6.9,7.4,7.9,8.5,9.1,9.8],
        "net_charge_offs":            [1.0]*9,
        "provision_for_credit_losses":[1.2]*9,
        "delinquency_rate":           [.030]*9,
        "vintage_early_delinquency":  [.020,.020,.020,.020,.019,.019,.018,.018,.017],
        "roll_rate":                  [.15]*9,
        "net_income":                 [8,8.5,9,9.5,10,10.5,11,11.5,12],
    })


def saas_healthy(ticker: str = "SAASOK") -> list[FundamentalSnapshot]:
    return _panel(ticker, "saas", {
        "billings":              [110,122,135,150,165,182,200,220,240],  # outgrowing revenue
        "crpo":                  [200,222,246,273,303,336,373,414,459],
        "net_revenue_retention": [1.20,1.20,1.21,1.21,1.22,1.22,1.23,1.23,1.24],
        "deferred_revenue":      [80,88,97,107,118,130,143,157,173],
        "sm_pct_revenue":        [.42,.42,.41,.41,.40,.40,.39,.39,.38],
        "sbc_pct_revenue":       [.16]*9,
    }, typed={
        "revenue":        [100,110,120,130,142,155,169,184,200],
        "free_cash_flow": [10,11,12,13,15,17,19,21,23],
        "operating_cash_flow":[12,13,14,15,17,19,21,23,25],
        "capex":          [1]*9,
    })


# breakdown builder, healthy builder — keyed by sector name
SECTORS: dict[str, tuple[Callable, Callable]] = {
    "industrial": (industrial, industrial_healthy),
    "financial": (bank, bank_healthy),
    "reit": (reit, reit_healthy),
    "broker": (broker, broker_healthy),
    "insurance": (insurer, insurer_healthy),
    "lender": (lender, lender_healthy),
    "saas": (saas, saas_healthy),
}


def benign_events(ticker: str, split: bool = False) -> list[NarrativeEvent]:
    """A benign, low-entropy narrative (or a split, high-entropy one) attached at
    each deteriorating quarter, so a contemporaneous story exists at every
    point-in-time evaluation date in the backtest."""
    events: list[NarrativeEvent] = []
    for period, rep in QUARTERS:
        if period < "2025-Q1":  # narrative runs from the deterioration onset
            continue
        t = f"{rep}T08:00:00-04:00"
        for i in range(3):
            events.append(NarrativeEvent(ticker, t, f"{ticker} update",
                                         BENIGN_BODY, f"benign_{i}", "sell_side"))
        if split:
            for i in range(3):
                events.append(NarrativeEvent(ticker, t, f"{ticker} downgrade",
                                             ADMIT_BODY, f"admit_{i}", "sell_side"))
    return events
