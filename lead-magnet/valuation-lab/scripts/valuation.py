#!/usr/bin/env python3
"""North de Noise — Valuation Lab calculator.

Deterministic DCF / DDM / reverse-DCF math, stdlib only. Claude (driving the
skill) collects + confirms inputs, then calls this so the numbers are auditable
and reproducible rather than guessed.

Usage:
    python3 valuation.py --model dcf  --json '{...}'
    python3 valuation.py --model ddm  --json '{...}'
    python3 valuation.py --model all  --json '{...}'   # both, sharing keys

All outputs are ESTIMATES that depend entirely on the assumptions supplied.
They are educational ranges, never a recommendation. (Disclaimer printed below.)
"""

import argparse
import json
import sys

DISCLAIMER = (
    "Educational estimate only — not investment advice or a recommendation to "
    "buy or sell. Output depends entirely on the assumptions above; change an "
    "assumption and the value changes. Past performance does not indicate or "
    "guarantee future results. Verify all inputs independently."
)


def _money(x):
    return f"{x:,.2f}"


# --------------------------- DCF ---------------------------
def dcf_per_share(fcf0, high_growth, years, terminal_growth, wacc, shares, net_debt):
    """Two-stage FCF DCF -> equity value per share."""
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal growth.")
    ev = 0.0
    fcf = fcf0
    for t in range(1, years + 1):
        fcf = fcf * (1 + high_growth)
        ev += fcf / ((1 + wacc) ** t)
    # terminal value (Gordon) on year-N FCF, discounted back
    tv = fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    ev += tv / ((1 + wacc) ** years)
    equity = ev - net_debt
    return equity / shares


def sensitivity_grid(base, fields):
    """5x5 grid over WACC (rows) x terminal growth (cols)."""
    waccs = [base["wacc"] + d for d in (-0.01, -0.005, 0, 0.005, 0.01)]
    tgs = [base["terminal_growth"] + d for d in (-0.01, -0.005, 0, 0.005, 0.01)]
    rows = []
    header = "WACC \\ g   " + "".join(f"{g*100:7.2f}%" for g in tgs)
    rows.append(header)
    for w in waccs:
        cells = []
        for g in tgs:
            try:
                v = dcf_per_share(fields["fcf0"], fields["high_growth"], fields["years"],
                                  g, w, fields["shares"], fields["net_debt"])
                cells.append(f"{v:8.2f}")
            except ValueError:
                cells.append("     n/a")
        rows.append(f"{w*100:6.2f}%   " + "".join(cells))
    return "\n".join(rows)


def reverse_dcf(price, fields):
    """Solve the constant FCF growth rate the current price implies."""
    lo, hi = -0.50, 1.00
    target = price

    def f(g):
        return dcf_per_share(fields["fcf0"], g, fields["years"],
                             fields["terminal_growth"], fields["wacc"],
                             fields["shares"], fields["net_debt"]) - target

    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None  # price not reachable in plausible range
    for _ in range(100):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-6:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def run_dcf(d):
    req = ["fcf0", "high_growth", "years", "terminal_growth", "wacc", "shares", "net_debt"]
    missing = [k for k in req if k not in d]
    if missing:
        raise ValueError(f"DCF missing inputs: {', '.join(missing)}")
    base = dcf_per_share(d["fcf0"], d["high_growth"], d["years"],
                         d["terminal_growth"], d["wacc"], d["shares"], d["net_debt"])
    out = []
    out.append("=" * 60)
    out.append(f"DCF — INTRINSIC VALUE  ({d.get('ticker','(stock)')})")
    out.append("=" * 60)
    out.append("Inputs:")
    out.append(f"  Base FCF .............. {_money(d['fcf0'])}")
    out.append(f"  High-growth rate ...... {d['high_growth']*100:.2f}% for {d['years']} yrs")
    out.append(f"  Terminal growth ....... {d['terminal_growth']*100:.2f}%")
    out.append(f"  WACC (discount rate) .. {d['wacc']*100:.2f}%")
    out.append(f"  Shares ................ {_money(d['shares'])}")
    out.append(f"  Net debt .............. {_money(d['net_debt'])}")
    out.append("")
    out.append(f"  >> Base-case intrinsic value:  {base:,.2f} per share")
    out.append("")
    out.append("Sensitivity (per-share value): rows = WACC, cols = terminal growth")
    out.append(sensitivity_grid(d, d))
    lo = min(base * 0.8, base)
    out.append("")
    out.append(f"  Reasonable range (illustrative): ~{base*0.8:,.2f} – {base*1.2:,.2f}")
    if d.get("current_price"):
        cp = d["current_price"]
        g_imp = reverse_dcf(cp, d)
        out.append("")
        out.append(f"Reverse DCF — what the market price of {cp:,.2f} implies:")
        if g_imp is None:
            out.append("  Current price is outside the plausible growth range tested.")
        else:
            out.append(f"  Implied constant FCF growth for {d['years']} yrs: {g_imp*100:.2f}%")
            out.append(f"  (You assumed {d['high_growth']*100:.2f}%. Do you believe more or less?)")
    out.append("")
    out.append(DISCLAIMER)
    return "\n".join(out)


# --------------------------- DDM ---------------------------
def ddm_value(div0, high_growth, years, terminal_growth, required_return):
    """Two-stage dividend discount model -> value per share."""
    if required_return <= terminal_growth:
        raise ValueError("Required return must be greater than terminal growth.")
    value = 0.0
    div = div0
    for t in range(1, years + 1):
        div = div * (1 + high_growth)
        value += div / ((1 + required_return) ** t)
    tv = div * (1 + terminal_growth) / (required_return - terminal_growth)
    value += tv / ((1 + required_return) ** years)
    return value


def run_ddm(d):
    req = ["dividend0", "high_growth", "years", "terminal_growth", "required_return"]
    missing = [k for k in req if k not in d]
    if missing:
        raise ValueError(f"DDM missing inputs: {', '.join(missing)}")
    val = ddm_value(d["dividend0"], d["high_growth"], d["years"],
                    d["terminal_growth"], d["required_return"])
    # also a simple Gordon value for contrast
    gordon = (d["dividend0"] * (1 + d["terminal_growth"])) / (d["required_return"] - d["terminal_growth"]) \
        if d["required_return"] > d["terminal_growth"] else float("nan")
    out = []
    out.append("=" * 60)
    out.append(f"DDM — DIVIDEND DISCOUNT MODEL  ({d.get('ticker','(stock)')})")
    out.append("=" * 60)
    out.append("Inputs:")
    out.append(f"  Current annual dividend . {_money(d['dividend0'])}/share")
    out.append(f"  High-growth rate ........ {d['high_growth']*100:.2f}% for {d['years']} yrs")
    out.append(f"  Terminal growth ......... {d['terminal_growth']*100:.2f}%")
    out.append(f"  Required return ......... {d['required_return']*100:.2f}%")
    out.append("")
    out.append(f"  >> Two-stage DDM value:     {val:,.2f} per share")
    out.append(f"     Single-stage (Gordon):   {gordon:,.2f} per share")
    if d.get("current_price"):
        out.append(f"     Current price:           {d['current_price']:,.2f} per share")
    out.append("")
    out.append("Note: DDM only works for stable, reliable dividend payers. If the")
    out.append("payout is uncertain or the company doesn't pay dividends, use the DCF.")
    out.append("")
    out.append(DISCLAIMER)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="North de Noise — Valuation Lab calculator")
    ap.add_argument("--model", choices=["dcf", "ddm", "all"], required=True)
    ap.add_argument("--json", help="JSON string of inputs; if omitted, read from stdin")
    args = ap.parse_args()

    raw = args.json if args.json else sys.stdin.read()
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON ({e})", file=sys.stderr)
        sys.exit(1)

    try:
        if args.model == "dcf":
            print(run_dcf(d))
        elif args.model == "ddm":
            print(run_ddm(d))
        else:
            print(run_dcf(d))
            print()
            print(run_ddm(d))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
