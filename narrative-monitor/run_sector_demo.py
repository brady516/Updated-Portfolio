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


if __name__ == "__main__":
    main()
