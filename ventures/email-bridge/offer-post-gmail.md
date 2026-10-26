# Offer v2 — Go Legit Local, designed around the Gmail shutdown

**Supersedes the pricing and scope in `offer.md`.** That doc framed this as a bridge with a
sunset and a $299 one-time fee. Both are now wrong: the Gmail change kills the $299
mechanism *and* removes the free DIY competitor, which is what turns this from a bridge
into an income line.

Read `rates.md` for the pricing philosophy (price on value, hours only set the floor and
prove the margin). That philosophy still holds. The numbers below replace the rate card's
email tier.

---

## 1. What changed

Google ends Gmail **"Send mail as" for third-party addresses in January 2027**. That is
the exact mechanism `offer.md` sells in its included scope ("'Send as' from their pro
address in the inbox they already use"). Cloudflare Email **receiving** is unaffected —
only the sending half breaks.

Three consequences, in order of importance:

**a) The old offer has a dated liability.** One-time fee, no recurring revenue, an
explicit "no ongoing support retainer," and a deliverable guarantee — against a mechanism
with a published expiry. Every install sold on Send-As breaks on *one date*, not
gradually. That is a **correlated** failure, not an idiosyncratic one: the whole book
calls at once, with no revenue stream funding the remediation.

**b) The free competitor dies with it.** Today a customer can self-serve Cloudflare +
Send-As for $0, which is what caps the price at $299. After January 2027 that path is
gone. The cheap DIY alternative disappears from the comparison set.

**c) Recurring revenue becomes honest.** You cannot credibly charge monthly to maintain a
free forward. You *can* charge monthly for a real mailbox that you host and monitor,
because now there is real recurring COGS and real ongoing service. The Gmail change is
what makes the MRR layer in `rates.md` legitimate rather than a tacked-on fee.

**But the monthly deliverable is re-verification, not support.** He will never call
support. The configuration *drifts* — app updates reset send-from defaults, OS upgrades
migrate accounts, he re-adds his personal Gmail, a Business Profile edit gets reverted, a
new phone restores from a backup. A single install is a point measurement of a moving
system. The quarterly re-verify in `acceptance.md` Part 5 is a concrete, inspectable thing
arriving on a schedule, and that is what the $5–10/mo is actually for.

**The deadline is also real urgency.** `offer.md` sets an integrity bar of "no fake
scarcity." This scarcity is not manufactured — it is a published date. That is the best
honest sales environment this offer will ever have.

---

## 2. The structural advantage (this is the whole design)

> **Your cost is per-account and seat-independent. Google's cost is per-seat.**

Real mailbox hosts in this class (Migadu, Purelymail, MXroute) bill a **flat fee per
account with unlimited addresses and domains**. Limits apply to the *account* (storage,
messages/day), not to each mailbox. Google Workspace bills **$7/user/month**.

Therefore: **price per business, include unlimited crew mailboxes.** On any crew of two
or more you cannot be beaten by Google on price, structurally, forever.

**This inverts the current rate card.** `offer.md` charges *"$199/seat for 3+ mailboxes."*
That is per-seat pricing on top of a flat cost — it prices like Google while costing like
Migadu. It caps your order value, punishes your best customers (crews), and throws away
the one advantage the cost structure hands you. Kill it. Unlimited seats included is
simultaneously the better customer offer **and** the better margin.

---

## 3. Verified COGS

| Host | Price | Shape | Binding limit |
|---|---|---|---|
| Cloudflare Email Routing | **free** | receiving only | unaffected by the Gmail change |
| Purelymail | ~**$10/yr** | no hard user/domain cap | soft limits → metered past ~$10 resources |
| Migadu Micro | ~**$19/yr** | unlimited addresses | **20 outgoing/day**, 5 GB |
| MXroute Small | ~**$59/yr** | priced by storage, not users | 10 GB |
| Migadu Mini | ~**$90/yr** | unlimited addresses | 100 outgoing/day, 30 GB |
| Migadu Standard | ~**$290/yr** | unlimited addresses | 500 outgoing/day, 100 GB |
| *(anchor)* Google Workspace Starter | **$7/user/mo** annual | **per seat** | — |

**The 20/day cap on Micro is the trap.** A 5-person crew at ~10 sends each is 50/day —
Micro breaks, and you need Mini ($90/yr) or MXroute ($59/yr). So COGS is **not** flat
across customer size, and the tiers below reflect that. A flat $8/mo price against a
$7.50/mo Mini cost is roughly zero margin.

*All host and Workspace prices are from third-party comparison sites, not the vendors'
own pricing pages — see §8. Confirm before committing to a price.*

---

## 4. One account per customer, not a shared one

A single Migadu Standard account ($290/yr, unlimited domains) could carry ~50 customers
at ~$0.48/customer/month. **Don't.** The limits and the sending reputation are
account-wide: one customer's compromised mailbox or one spam blast burns deliverability
and eats the daily cap for *every* customer on that account. That rebuilds exactly the
correlated, whole-book-fails-at-once exposure the old offer is being redesigned to escape.

Isolated per-customer accounts cost ~$19–59/yr instead of ~$6/yr. **The de-correlation
premium is roughly $20–50 per customer per year and the blast radius drops from the whole
book to one.** At these prices, buy it without thinking about it.

**Who owns the account:** the customer. Their billing, their name, you hold delegated
admin. This keeps you from becoming the mail operator of record (abuse liability,
reputation exposure), and it makes good on the "they own it, no lock-in" promise that
`rates.md` uses as its anchor against agencies. You charge for provisioning, management
and monitoring — not for reselling mailboxes at a markup.

---

## 5. Pricing

### The term-matching principle

The old offer's real defect was not the price, it was a **duration mismatch**: one-time
revenue against an open-ended promise. January 2027 is simply the first time that
mismatch gets called.

The fix is to **match the term of the revenue to the term of the promise.** Sell a defined
24-month term. The obligation expires with the payment, and every renewal is a
re-underwriting moment where you reprice against whatever Google and the hosts have done
since. That bounds the tail instead of leaving it open and uncompensated.

### Your two candidate structures, modelled

24-month contribution per solo customer. COGS $38 (Migadu Micro × 2yr), Stripe 2.9% + $0.30.

| Structure | Collected | Stripe | COGS | **Contribution** | Churn exposure |
|---|---|---|---|---|---|
| $300 + $5/mo | $420 | $19.68 | $38 | **$362** | 24 months of it |
| $300 + $8/mo | $492 | $21.77 | $38 | **$432** | 24 months of it |
| $300 + $10/mo | $540 | $23.16 | $38 | **$479** | 24 months of it |
| $300 + $129/yr | $558 | $17.08 | $38 | **$503** | 2 renewal points |
| **$599 / 24 mo prepaid** | **$599** | **$17.67** | **$38** | **$543** | **none in term** |

**Your $599/24-month instinct is correct and it dominates every monthly variant** — on
contribution, on cash timing, and on churn. Two reasons it wins by more than the table
shows:

- **Small monthlies are fee-destroyed.** Stripe's $0.30 fixed fee is brutal at this size:
  a $5/mo charge loses **8.9%** to fees, $8/mo loses 6.7%, $10/mo loses 5.9%. One $599
  charge loses **2.9%**. Billing monthly at these amounts donates 3–6 points of margin to
  Stripe and adds dunning labour.
- **Monthly carries churn you haven't priced.** If average life is 14 months rather than
  24, the $300+$10/mo option drops to ~$385 contribution. Involuntary churn alone (expired
  cards) is significant at $9/mo, and chasing a failed $9 payment costs more than the
  payment.

### Recommended rate card

| Tier | Scope | Price |
|---|---|---|
| **Solo / owner-only** | 1 domain, up to 2 mailboxes, 24 months hosted + monitored | **$499 / 24 mo** |
| **Crew** | 1 domain, **up to 10 mailboxes**, 24 months hosted + monitored | **$899 / 24 mo** |
| **Payment-plan door** | same as Solo, for buyers who flinch at one number | $300 setup + $9/mo, 12-mo minimum |
| **Hand-over-and-gone** | setup only, customer owns + pays host, no monitoring, 30-day guarantee | **$399 one-time** |

Add-ons unchanged from `offer.md`: domain purchase +$50. **Delete the $199/seat crew
rate** (see §2).

**Why $499 and not $599 for solo:** `offer.md`'s thesis is "slam dunk = fast decision, one
number said plainly." $299 proved the willingness to pay. $599 is a materially slower yes
for an owner-only shop, and under-$500 holds the fast-yes while still being a ~67%
increase on the old effective price. Contribution is ~$446 — roughly 1.5× the old $299,
*and* the tail is now bounded. **Test $449 / $499 / $599 once you have a few sales.**

**Lead with Crew.** The structural advantage only pays on crews, and `offer.md` already
spotted it ("the crew rate is the sleeper"). At 10 mailboxes you are **$89.90 per mailbox
per 24 months against Google's $168** — 47% cheaper per seat, setup and management
included. For a solo you are *more* expensive than Workspace on paper and must sell on
done-for-you, not price. Target contractors with techs.

| Crew size | You ($899/24mo) | Workspace ($7/user/mo) |
|---|---|---|
| 3 | $899 | $504 |
| 5 | $899 | $840 |
| 10 | $899 | **$1,680** |

Crossover is ~5 seats, and they still have to configure Workspace themselves.

---

## 6. The migration play

Everyone on Cloudflare + Send-As breaks in January 2027 — your existing customers and
every DIY user who set it up themselves. That is a dated, forced-migration population.

1. **Migrate your existing book first, free, in exchange for a term plan.** They bought a
   working system under a guarantee; honour it. Free migration converted into a 24-month
   plan turns your single largest liability into your conversion engine.
2. **Sell against the deadline honestly.** "Google is switching this off in January 2027.
   Here's what breaks, here's the date, here's the fix." Real deadline, no manufactured
   scarcity.
3. **The DIY population is a lead source.** People who self-served Cloudflare + Send-As
   already demonstrated they want pro email and won't pay Google. They now have a problem
   they cannot fix for free. Trade forums and the subreddits in `leadgen.md` are where
   they'll ask about it.
4. **Start before the panic.** Migrate through 2026 at a calm pace. Arriving in December
   2026 with a book to move is a worse business than arriving in March.

---

## 7. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Host ToS forbids managing client accounts / reselling | **High** | **Verify before selling.** Customer-owned billing (§4) sidesteps most of it |
| Host concentration — one vendor carries the book | High | Keep `provision.py` host-agnostic; know your second host before you need it |
| Shared-account reputation contagion | High | Isolated account per customer (§4) |
| Daily send caps hit as a crew grows | Medium | Size the tier at sale; monitor; upgrade path priced into the renewal |
| 24-month prepay spent in month 1 → unfunded obligation | Medium | Reserve COGS (~$38–180) per sale at the point of sale |
| Google changes terms again | Medium | The 24-month term *is* the hedge — reprice at renewal |
| Jan 2027 scope not confirmed from Google directly | Medium | §8 |

---

## 8. Open items — verify before pricing

Everything below is from third-party reporting, not primary sources. Two of these are
load-bearing.

- [ ] **Google's own Send-As page** — confirm custom domains are in scope. Vendor
      consensus says yes; `sislelabs/mailctl`'s own notes argue the wording "may well
      exclude this case." This is the single most important fact in this document and it
      is not yet confirmed from Google. *(Blocked from the dev container by network
      policy — check from a browser.)*
- [ ] **Host pricing and limits** from Migadu / Purelymail / MXroute pricing pages.
      Sources conflicted on Migadu Standard ($190 vs $290/yr) and MXroute Small ($49 vs
      $59/yr).
- [ ] **Host ToS** on managing client-owned accounts as an agency/admin.
- [ ] **Workspace $7/user/mo** from Google's page; intro discounts reported.
- [ ] **Deliverability test** on the chosen host before selling — this is the product.

## 9. Changes needed in the existing docs

- `offer.md` — remove "bridge / sunset / not a company" framing; replace $299 and the
  included-scope "Send as" line; **delete the $199/seat crew rate**; re-scope the
  guarantee to the 24-month term.
- `rates.md` — replace the Tier 1 "$299 Professional Email" row; the Care-plan MRR rows
  are now superseded by the term pricing above for email.
- `runbook.md` / `SOP.md` — the Gmail Send-As step becomes a mailbox-provisioning step.
- `provision.py` — needs a mailbox-host path. Keep it host-agnostic.
- `faq.md`, `phone-close.md` — need the January 2027 answer.
