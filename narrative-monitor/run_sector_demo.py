#!/usr/bin/env python3
"""Sector demo: the SAME engine reading bank and REIT microstructure.

Financials and REITs aren't the exception to the thesis — they're the richest
case, because reserves, marks, and FFO adjustments are management estimates with
more room for the story to diverge from cash. This runs a bank and a REIT whose
*narratives are benign* ("credit remains benign", "growth is intact") while their
own reported microstructure breaks down, and shows the sector channels firing.

    python3 run_sector_demo.py
"""

from __future__ import annotations

from datetime import date

from narrative_monitor import (
    FundamentalSnapshot,
    NarrativeEvent,
    SignalEngine,
    extract_claims,
    narrative_intensity,
)

QUARTERS = [
    ("2024-Q1", "2024-04-22"), ("2024-Q2", "2024-07-22"),
    ("2024-Q3", "2024-10-22"), ("2024-Q4", "2025-01-27"),
    ("2025-Q1", "2025-04-21"), ("2025-Q2", "2025-07-21"),
    ("2025-Q3", "2025-10-20"), ("2025-Q4", "2026-01-26"),
    ("2026-Q1", "2026-04-20"),
]


def _panel(ticker: str, sector: str, series: dict[str, list[float]],
           guidance_key: str, guidance: dict[str, float]) -> list[FundamentalSnapshot]:
    out = []
    for i, (period, rep) in enumerate(QUARTERS):
        items = {k: v[i] for k, v in series.items()}
        if period in guidance:
            items[guidance_key] = guidance[period]
        out.append(FundamentalSnapshot(
            ticker=ticker, period=period, revenue=0.0, free_cash_flow=0.0,
            operating_cash_flow=0.0, capex=0.0, reported_at=rep,
            sector=sector, line_items=items,
        ))
    return out


def bank_panel() -> list[FundamentalSnapshot]:
    # credit deteriorates: charge-offs rise, coverage falls, reserves drained,
    # NPAs outrun loans, NIM compresses, TBVPS erodes, AOCI losses build.
    series = {
        "gross_loans":                [100, 101, 102, 103, 104, 105, 106, 107, 108],
        "net_charge_offs":            [.20, .20, .22, .22, .35, .40, .50, .55, .60],
        "provision_for_credit_losses":[.25, .25, .25, .25, .30, .32, .35, .40, .35],
        "allowance_for_loan_losses":  [1.50,1.50,1.52,1.52,1.40,1.35,1.30,1.25,1.20],
        "nonperforming_assets":       [1.0, 1.0, 1.1, 1.1, 1.5, 1.7, 1.9, 2.1, 2.3],
        "net_interest_margin":        [.0350,.0350,.0348,.0348,.0335,.0330,.0325,.0320,.0310],
        "tangible_book_value_per_share":[50,50,50,50,49,48,47,46,45],
        "net_income":                 [3.0, 3.0, 3.1, 3.2, 2.5, 2.3, 2.1, 1.9, 1.6],
        "aoci_unrealized_loss":       [1, 1, 1, 1, 3, 4, 5, 6, 7],
        "tangible_common_equity":     [40]*9,
    }
    guid = {"2025-Q2": 25.0, "2025-Q3": 24.0, "2025-Q4": 23.0, "2026-Q1": 22.0}
    return _panel("BANKX", "financial", series, "fy_nii_guidance", guid)


def reit_panel() -> list[FundamentalSnapshot]:
    # AFFO falls while FFO holds (wedge widens), same-store NOI decelerates,
    # straight-line rent inflates, capitalized interest rises, dividend > AFFO.
    series = {
        "ffo":                        [2.0, 2.1, 2.0, 2.3, 2.0, 2.1, 2.0, 2.3, 2.0],
        "affo":                       [1.6, 1.7, 1.6, 1.9, 1.3, 1.3, 1.2, 1.4, 1.1],
        "same_store_noi":             [10.0,10.2,10.1,10.3,9.9, 9.8, 9.9, 9.9, 9.2],
        "total_noi":                  [10.0,10.2,10.1,10.3,11.0,11.5,12.0,12.5,13.0],
        "straight_line_rent_receivable":[5,5,5,5,5.5,5.8,6.0,6.3,6.8],
        "capitalized_interest":       [.30,.30,.30,.30,.40,.45,.50,.55,.60],
        "occupancy":                  [.95,.95,.94,.94,.93,.92,.91,.90,.89],
        "dividend_per_share":         [.40]*9,
        "affo_per_share":             [.55,.58,.55,.62,.45,.44,.42,.46,.35],
    }
    guid = {"2025-Q2": 1.60, "2025-Q3": 1.50, "2025-Q4": 1.40, "2026-Q1": 1.30}
    return _panel("REITX", "reit", series, "fy_affo_guidance", guid)


def broker_panel() -> list[FundamentalSnapshot]:
    # a rate carry turning over: NII peaks then compresses, float erodes,
    # net income falls, while reliance on NII and rate sensitivity stay high.
    series = {
        "net_interest_income":     [700,750,800,850,820,780,730,690,640],
        "pretax_income":           [500,540,580,620,560,520,470,430,380],
        "net_income":              [400,430,460,490,450,420,380,350,300],
        "customer_credit_balances":[90,92,94,96,93,90,86,82,78],
        "commission_revenue":      [200,205,200,210,200,198,195,195,190],
        "rate_sensitivity_25bp":   [150,150,160,160,180,190,195,200,200],
    }
    guid = {"2025-Q2":3200,"2025-Q3":3000,"2025-Q4":2800,"2026-Q1":2600}
    return _panel("BROKERX", "broker", series, "fy_nii_guidance", guid)


def insurance_panel() -> list[FundamentalSnapshot]:
    # combined ratio crosses 100, current accident year worse than reported,
    # premiums grow into a rising loss ratio, reserves turn adverse.
    series = {
        "combined_ratio":            [.95,.96,.95,.94,.99,1.01,1.03,1.04,1.06],
        "loss_ratio":                [.65,.66,.65,.64,.69,.71,.73,.74,.76],
        "accident_year_loss_ratio":  [.66,.67,.66,.65,.74,.77,.80,.82,.85],
        "favorable_reserve_development":[30,32,30,33,20,15,8,2,-10],
        "pretax_income":             [200,210,205,215,180,160,140,120,100],
        "net_premiums_written":      [100,102,101,103,112,116,120,124,130],
        "net_income":                [160,168,164,172,144,128,112,96,80],
    }
    guid = {"2025-Q2":0.99,"2025-Q3":1.01,"2025-Q4":1.03,"2026-Q1":1.05}
    return _panel("INSURX", "insurance", series, "fy_combined_ratio_guidance", guid)


def lender_panel() -> list[FundamentalSnapshot]:
    # originations accelerate while the newest vintages rot: growth by loosening
    # underwriting, reserves lagging, roll rates climbing.
    series = {
        "originations":               [50,55,60,65,75,85,95,105,115],
        "receivables":                [200,210,220,230,245,260,278,298,320],
        "allowance_for_credit_losses":[6.0,6.3,6.6,6.9,6.8,6.9,7.0,7.1,7.2],
        "net_charge_offs":            [1.0,1.0,1.1,1.1,1.4,1.7,2.1,2.5,3.0],
        "provision_for_credit_losses":[1.3,1.3,1.3,1.3,1.6,1.8,2.0,2.2,2.4],
        "delinquency_rate":           [.030,.030,.032,.032,.038,.042,.046,.050,.055],
        "vintage_early_delinquency":  [.020,.020,.021,.021,.028,.032,.036,.040,.045],
        "roll_rate":                  [.15,.15,.16,.16,.18,.20,.22,.24,.26],
        "net_income":                 [8,8.2,8.4,8.6,7.0,6.0,5.0,4.0,3.0],
    }
    guid = {"2025-Q2":.045,"2025-Q3":.050,"2025-Q4":.055,"2026-Q1":.060}
    return _panel("LENDX", "lender", series, "fy_loss_rate_guidance", guid)


def _run(name: str, panel, body: str) -> None:
    events = [NarrativeEvent(panel[0].ticker, "2026-04-20T08:00:00-04:00",
                             f"{panel[0].ticker} update", body, s, "sell_side")
              for s in ("analyst_a", "analyst_b", "analyst_c")]
    claims = extract_claims(events)
    signal = SignalEngine().evaluate(panel, claims, narrative_intensity(claims))
    print(f"\n=== {name} ({panel[0].sector}) ===")
    print(f"state: {signal.state.value}   breakdown_score: {signal.breakdown_score}   "
          f"divergence: {signal.divergence}")
    print(f"H(N): {signal.narrative_entropy}   H(R): {signal.reporting_entropy}   "
          f"confidence: {signal.confidence}   executable: {signal.execution_eligible}")
    print("channels fired:", ", ".join(signal.confirmed_criteria))
    for r in signal.reasons[:4]:
        print("  •", r)


def main() -> None:
    print("SAME engine, different microstructure. Benign narratives, broken filings.")
    _run("Bank — 'credit remains benign'", bank_panel(),
         "credit remains benign, net interest margin pressure is a temporary headwind")
    _run("REIT — 'external growth is accretive'", reit_panel(),
         "pipeline remains strong, ai investment aside our growth is intact via deal timing")
    _run("Broker — 'durable franchise earnings'", broker_panel(),
         "durable franchise, pipeline remains strong, the rate move is a temporary headwind")
    _run("Insurer — 'underwriting stays disciplined'", insurance_panel(),
         "underwriting is disciplined, pipeline remains strong, a temporary headwind on cats")
    _run("Lender — 'record originations, TAM expansion'", lender_panel(),
         "record originations, pipeline remains strong, the vintage is a temporary headwind")


if __name__ == "__main__":
    main()
