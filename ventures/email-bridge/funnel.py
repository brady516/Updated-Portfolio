#!/usr/bin/env python3
"""
funnel.py — the Go Legit Local operating model. Demand-limited, not capacity-limited.

Plug in your (real, once you have them) conversion rates and it tells you the
sales/day each channel produces, the revenue that implies, and whether you're
under the one-operator fulfillment ceiling (i.e., when to hire a VA).

The defaults are STARTING ESTIMATES. Replace them with your actuals after the
first ~200 emails and ~10 calls — that's the whole point.

Examples:
    python3 funnel.py                       # model with default estimates
    python3 funnel.py --partners 8          # what 8 referral partners does
    python3 funnel.py --emails-per-day 250 --partners 8
    python3 funnel.py --target 4            # solve: what it takes to hit 4/day

Stdlib only.
"""

import argparse

WORKDAYS_PER_MONTH = 21
DELIVERY_CEILING_PER_DAY = 7.5  # one operator @ 20 min over ~2.5 delivery hrs


def cold_sales_per_day(emails_per_day: float, reply_rate: float, reply_close: float) -> float:
    return emails_per_day * reply_rate * reply_close


def partner_sales_per_day(partners: float, intros_wk: float, close: float) -> float:
    per_week = partners * intros_wk * close
    return per_week / 7.0


def report(a) -> None:
    cold = cold_sales_per_day(a.emails_per_day, a.reply_rate, a.reply_close)
    partner = partner_sales_per_day(a.partners, a.intros_per_partner, a.partner_close)
    total = cold + partner

    rev_day = total * a.price
    rev_week = rev_day * 5
    rev_month = total * WORKDAYS_PER_MONTH * a.price
    rev_year = rev_month * 12
    deliver_hrs = total * (a.delivery_min / 60.0)

    print("=" * 56)
    print("  Go Legit Local funnel model  (estimates until you have real data)")
    print("=" * 56)
    print(f"  Price/setup            ${a.price:,.0f}")
    print(f"  Delivery time          {a.delivery_min:.0f} min  (~${a.price/(a.delivery_min/60):,.0f}/hr labor)")
    print("-" * 56)
    print("  CHANNELS (sales/day)")
    print(f"    Cold email    {cold:5.2f}   "
          f"({a.emails_per_day:.0f}/day x {a.reply_rate:.1%} reply x {a.reply_close:.0%} close)")
    print(f"    Referral      {partner:5.2f}   "
          f"({a.partners:.0f} partners x {a.intros_per_partner:.1f} intros/wk x {a.partner_close:.0%})")
    print(f"    TOTAL         {total:5.2f}  sales/day")
    print("-" * 56)
    print("  REVENUE")
    print(f"    per day       ${rev_day:9,.0f}")
    print(f"    per week (5d) ${rev_week:9,.0f}")
    print(f"    per month     ${rev_month:9,.0f}   ({WORKDAYS_PER_MONTH} workdays)")
    print(f"    per year      ${rev_year:9,.0f}")
    print("-" * 56)
    print("  CAPACITY")
    print(f"    Delivery load  {deliver_hrs:.1f} hrs/day")
    if total > DELIVERY_CEILING_PER_DAY:
        print(f"    ** Over the {DELIVERY_CEILING_PER_DAY}/day one-operator ceiling — "
              f"hire a VA or raise price. **")
    else:
        headroom = DELIVERY_CEILING_PER_DAY - total
        print(f"    {headroom:.1f}/day headroom before the VA-hire trigger.")
    print("-" * 56)

    # rough exit framing on SDE (assume owner keeps most of it early; MRR not modeled)
    sde = rev_year * a.sde_margin
    print("  EXIT (rough — needs 12mo books + systematization + MRR layer)")
    print(f"    Est. annual SDE   ${sde:,.0f}   (at {a.sde_margin:.0%} margin)")
    print(f"    ~2x owner-run     ${sde*2:,.0f}")
    print(f"    ~3.5x systematized+MRR   ${sde*3.5:,.0f}")
    print("=" * 56)
    print("  Reminder: replace every rate above with YOUR measured numbers.")


def solve_target(a) -> None:
    """Given partners fixed, how many cold emails/day to hit --target sales/day?"""
    partner = partner_sales_per_day(a.partners, a.intros_per_partner, a.partner_close)
    need_from_cold = max(0.0, a.target - partner)
    per_email = a.reply_rate * a.reply_close
    emails_needed = need_from_cold / per_email if per_email else float("inf")
    print(f"\nTo hit {a.target:.1f} sales/day:")
    print(f"  {a.partners:.0f} referral partners already give {partner:.2f}/day.")
    if need_from_cold <= 0:
        print(f"  Partners alone clear the target — no cold email required.")
    else:
        print(f"  Need {need_from_cold:.2f}/day more from cold email")
        print(f"  = ~{emails_needed:.0f} fresh sends/day "
              f"(at {a.reply_rate:.1%} reply x {a.reply_close:.0%} close).")
    print()


def main() -> None:
    p = argparse.ArgumentParser(description="Go Legit Local funnel / operating model")
    p.add_argument("--price", type=float, default=299)
    p.add_argument("--delivery-min", type=float, default=20)
    # cold email channel
    p.add_argument("--emails-per-day", type=float, default=120)
    p.add_argument("--reply-rate", type=float, default=0.02, help="positive reply rate (0.02 = 2%)")
    p.add_argument("--reply-close", type=float, default=0.40, help="reply -> close rate")
    # referral channel
    p.add_argument("--partners", type=float, default=4)
    p.add_argument("--intros-per-partner", type=float, default=2, help="warm intros/partner/week")
    p.add_argument("--partner-close", type=float, default=0.60)
    # exit framing
    p.add_argument("--sde-margin", type=float, default=0.85)
    # solve mode
    p.add_argument("--target", type=float, default=None,
                   help="solve: cold emails/day needed to hit this sales/day, given --partners")

    a = p.parse_args()
    report(a)
    if a.target is not None:
        solve_target(a)


if __name__ == "__main__":
    main()
