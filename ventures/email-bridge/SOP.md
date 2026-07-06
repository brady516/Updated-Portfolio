# SOP — running the email-bridge system end to end

The operating manual for the whole machine: source → outreach → close → deliver →
upsell → get paid → repeat. Written so **anyone (you today, a VA tomorrow, a buyer at
exit) can run it from this page.** If a step here needs you *specifically*, it's a bug
in the process — fix the process.

**Brand:** Go Legit Local — **golegitlocal.com** (registered, Cloudflare). **Everything
remote. Never drive anywhere.**

---

## 0. One-time setup (do once, before the first lead)

- [ ] **Domain** (~$10, Cloudflare Registrar) — separate from North de Noise.
- [ ] **Separate business bank account + separate Stripe.** Non-negotiable — clean
      books are what let you sell this (buyers must verify SDE). Never commingle.
- [ ] **Stripe Payment Links:** $299 core, +$50 domain, $199 crew-seat, $899 bundle.
- [ ] **Formspree** form for the landing page → `__FORMSPREE_TRADES__`; contact email
      → `hello@golegitlocal.com`.
- [ ] **Landing page** live on its own domain (Cloudflare Pages/Worker).
- [ ] **Calendly** — a 15-min "Email activation call" slot type.
- [ ] **Google Cloud** Places API key → `PLACES_API_KEY`. **Cloudflare** API token →
      `CF_API_TOKEN` + `CF_ACCOUNT_ID` (for `provision.py`).
- [ ] **Saved text snippets:** cold email, partner email, intake text, cheat sheet,
      signature block, voicemail.
- [ ] **A tracker** (one Google Sheet, tabs: Leads · Customers · Partners · Money).

---

## 1. The system at a glance

```
 SOURCE            OUTREACH           CLOSE            DELIVER           GROW
 leadfinder.py  →  cold email     →  phone-close  →  provision.py  →  crew upsell
 partners.sh    →  partner email  →  (Stripe pay) →  runbook.md    →  referral ask
                                                                    →  partner payout
```
Targets from `funnel-model.md`: **2 sales/day covers the nut; 4/day is humming.**
Run `funnel.py` with your real numbers to size the top of funnel.

---

## 2. Daily operating rhythm (time-blocked, ~2–3 hrs)

| Block | Time | What |
|---|---|---|
| **Sell** | 45–60 min | Work replies + booked calls first (hottest). Run the `phone-close.md` script. Send Stripe links to every yes. |
| **Deliver** | 30–60 min | Provision paid clients (`provision.py`), run booked activation calls (`runbook.md`), send cheat sheets. |
| **Fill funnel** | 30–45 min | Send the day's cold emails (from `leadfinder` list) + 1–2 partner-recruit touches. |
| **Admin** | 10 min | Pay any partner payouts owed (within 48h), update the tracker. |

Rule: **replies before prospecting.** A warm reply is worth 100 cold sends — never let
new outreach crowd out closing what's already interested.

## 3. Weekly rhythm

- [ ] **Monday:** refresh the lead list — run `leadfinder.py` for new city/trade; run
      `partners.sh` if recruiting partners.
- [ ] **Wed:** partner check-ins (2-min touch to active partners; keep them warm).
- [ ] **Friday:** update `funnel.py` with the week's **actual** reply/close rates;
      review sales/day vs. target; reconcile Stripe → bank; note SDE run-rate.

---

## 4. The pipeline, stage by stage

### Stage 1 — Source
- **Trades (cold):** `python3 leadfinder.py places -q "<trade> in <city>" -o targets.csv`
  then `harvest -i targets.csv -o leads.csv --leads-only`. Freemail rows = leads.
- **Partners (warm engine):** `bash partners.sh` → recruit from `partner-outreach.md`.
- *Output:* `leads.csv` (trades), `partners_contacts.csv` (partners).

### Stage 2 — Outreach
- **Cold email** (CAN-SPAM: real from/subject, physical address, working unsubscribe).
  Template in `leadgen.md`. **Email only — never cold-text (TCPA).**
- **Partner email** → book a call → sign them (`partner-outreach.md`).
- *SLA:* reply to any inbound within a few hours (speed wins trades deals).

### Stage 3 — Close
- Lead replies → **call them** using `phone-close.md`. Talk less than half; let the
  guarantee close. Segment by gap: has-site/bad-email → email offer; no-site → website
  (productized only).
- *Yes →* text Stripe link. **Payment before provisioning.** No exceptions.

### Stage 4 — Deliver (remote, ~20 min)
1. `python3 provision.py setup --domain <client.com> --address <name> --forward-to <their@gmail>`
2. Text: "click the Cloudflare verification link + book your 10-min activation call."
3. **Activation call** (`runbook.md` §3): nameservers if needed, Gmail send-as, live
   test, install signature.
4. `python3 provision.py check --domain <client.com>` → all green.

### Stage 5 — Grow (before you hang up)
- **Crew upsell:** $199/matching seat.
- **Referral ask:** "know another [trade] on gmail? send 'em my way."
- Text the **cheat sheet**, mark the order done. No lingering support.

### Stage 6 — Partner payout
- Client paid → pay the referring partner **$50 within 48h** (fast pay = repeat
  referrals). Log it. **1099 any partner ≥ $600/yr.**

---

## 5. Metrics — track weekly (replace estimates with actuals)

| Metric | Target | This week |
|---|---|---|
| Cold emails sent | ~120/day | |
| Positive reply rate | 2% | |
| Reply → close | 40% | |
| Active partners (referred in 30d) | 8 | |
| Sales/day | 2 → 4 | |
| Revenue (week) | — | |
| SDE run-rate (annualized) | — | |

Feed these into `funnel.py`. The discipline of replacing guesses with measured numbers
*is* the operating skill — and the un-dunkable proof you know the business.

---

## 6. Compliance guardrails (never skip)

- **Lead-gen:** Places API + reading businesses' own sites only. No scraping
  Google/Yelp/FB. Respect robots.txt. (`leadgen.md`)
- **Outreach:** cold **email** under CAN-SPAM; **no cold SMS/calls** (TCPA) until they
  reply and opt in.
- **Refunds:** honor the 48-hour deliverable guarantee — "not working, don't pay."
- **Taxes:** separate books; 1099 partners ≥ $600; track every payout.
- **Honesty:** real deliverable, no lock-in, no fake scarcity, no claims you can't back.
  The brand is "look legit" — the operation has to *be* legit.

---

## 7. Money & books (this is the exit)

- Separate bank + Stripe from dollar one; reconcile weekly.
- Track **SDE** = profit + your add-backs. That's what the business sells on.
- **Add the MRR layer** (Email Care $15–25/mo) by month 2 — it moves the multiple from
  ~2x to ~3.5x and makes the whole thing worth more the day you sell.

---

## 8. Roles & handoff (you → VA)

Delegable today with this SOP: **Stages 1, 2, 4, 6** (sourcing, outreach sends,
provisioning, payouts) — all scripted/templated. Keep for yourself: **Stage 3
closing** (until a VA proves out on the script). When you're consistently near the
**7.5/day fulfillment ceiling**, hand delivery to a VA and keep selling. That handoff
*is* the moment the asset becomes sellable.

## 9. The end state — sunset / exit

- **Trigger:** when RIA (or newsletter) recurring revenue covers your monthly nut —
  *or* when a strategic offers a fair 2.5–3.5x SDE — you sell or hand off.
- **Best buyer:** a local MSP / web agency / hosting reseller (your $299 customer is
  their $3k website customer). Shop strategics before marketplaces (Acquire.com,
  Flippa, Empire Flippers).
- **Deliverable at sale:** this repo folder *is* the data room — SOP, scripts,
  runbook, funnel model, customer list, clean books. That's what a buyer pays up for.

---

## 10. Quick reference — file → job

| File | Does |
|---|---|
| `offer.md` | the offer, pricing, tiers, exit design |
| `landing/index.html` | conversion landing page |
| `leadfinder.py` | find trades (freemail = lead) |
| `leadgen.md` | lead-gen compliance + cold-email template |
| `partners.sh` | find referral-partner suspects |
| `partner-outreach.md` | recruit & manage partners |
| `funnel-model.md` / `funnel.py` | operating model + calculator |
| `phone-close.md` | the 90-second close |
| `provision.py` | automate Cloudflare setup |
| `runbook.md` | remote delivery, step by step |
| `SOP.md` | **this — run it all end to end** |

**The one rule:** every step here is scripted, templated, or a 10-minute call. If
something feels like it needs *you*, fix the process — that's how a job becomes an
asset.
