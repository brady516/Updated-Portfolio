# Operating model — the funnel (demand-limited, not capacity-limited)

The business is capped by **how many people say yes today**, not by delivery hours.
So the real model is a funnel: *top-of-funnel outreach → replies → calls → closes.*
Delivery (20 min, mostly automated) is a strength, not the constraint. This doc sizes
the top of the funnel needed to hit **2 sales/day** (covers the nut) and **4/day**
(channel humming).

> ⚠️ **Every rate below is a starting estimate — replace with YOUR real numbers after
> the first 200 emails / first 10 calls.** The whole point is to let data set the
> model, not optimism. `funnel.py` recalculates when you plug in actuals.

---

## The three channels (ranked by efficiency)

### 1. Referral partners — the efficient, compounding engine
People who already see the bad gmail on trades' invoices: **bookkeepers,
accountants, local web designers, business-formation services.** Warm intro = high
trust = high close. Pay a **$50 kickback per closed deal.**

- Est. **2 intros/week per active partner**, **~60% close** (warm) = ~1.2 sales/week
  = **~0.24 sales/day per partner.**
- **8 active partners ≈ 2 sales/day.** That's the medium-term engine — fewer moving
  parts than blasting thousands of cold emails, and it compounds (partners refer
  partners).

### 2. Cold email (leadfinder list) — volume, lower conversion
CAN-SPAM compliant, hyper-relevant (you name their exact gmail problem), cheap offer.

- Est. **positive reply ~2%**, **reply→close ~40%** = **~0.8 sales per 100 emails**
  (call it **~1 sale per 100–150 sends** once dialed).
- **2/day ≈ 200–300 fresh sends/day.** Doable with leadfinder, but it's a grind and
  deliverability caps how hard you can push. Best as *fill* while partners ramp.

### 3. Trade communities / referrals-from-customers — bonus
FB groups, subreddits, and every happy customer's crew + network. Unpredictable to
model, real over time, near-zero cost. Treat as upside, not the plan.

---

## What it takes to hit the targets

Realistic early answer: **no single channel does it alone — blend.**

| Target | Blend that gets you there |
|---|---|
| **2/day** (~$600/day, ~$12–13k/mo) | 4 active referral partners (~1/day) **+** ~120 cold sends/day (~1/day) |
| **4/day** (~$1,200/day, ~$25k/mo) | 8 partners (~2/day) **+** ~250 cold sends/day (~2/day) **+** community upside |

**Two a day covers your nut.** You do not need the 7.5/day fulfillment ceiling — that
number is just your *"raise price or hire the VA"* trigger, not a revenue target.

---

## The honest ramp (weeks, not day one)

1. **Weeks 1–2 — dial the funnel.** Send the first 200 cold emails, take every call,
   and *measure your actual reply and close rates.* Land your first 3–5 customers.
   Goal here is data + proof, not volume.
2. **Weeks 3–4 — plant the efficient channel.** Sign 2–4 referral partners (the
   bookkeepers/web designers). One good partner beats a thousand cold emails.
3. **Month 2 — hit 2/day** on the blend. Cashflow problem solved.
4. **Month 3+ — push toward 4/day and the fulfillment ceiling.** When you're
   consistently near 7.5/day of delivery, **hand delivery to a VA** (runbook +
   provision.py make this a clean handoff) and keep selling. That's also the moment
   the asset becomes sellable.

---

## Unit economics (the numbers that impress an operator)

- **$299** revenue, **~20 min** delivery → **~$900/hour** effective delivery labor.
- **Near-zero COGS** (domain reg is passed through / client-paid).
- **~80% automatable**, VA-deliverable.
- **MRR layer** ($15–25/mo Email Care) turns one-time cash into recurring — the lever
  that moves the exit from ~2x to ~3.5x SDE.

Lead with *these*, not with a daily run-rate. Structure beats fantasy.

---

## Track these weekly (replace the estimates)

| Metric | Est. | Your actual |
|---|---|---|
| Cold emails sent | — | |
| Positive reply rate | 2% | |
| Reply → close | 40% | |
| Active referral partners | — | |
| Intros/partner/week | 2 | |
| Partner close rate | 60% | |
| **Sales/day** | target 2 | |

Feed your actuals into `funnel.py` and it tells you the volume required and the
revenue/exit implied. The model is only as good as the day you start replacing
guesses with data — that's the operator's discipline, and the un-dunkable answer to
"you don't even know what you're selling."
