# North de Noise — launch playbook

A week-by-week ramp from zero to paying subscribers. The whole strategy: **prove
quality for free first, then put the deep work behind a paywall.** Don't charge
before you've shown the goods.

---

## Phase 0 — Pre-launch (before week 1)

**Goal: be ready to publish, and have a reason for people to subscribe.**

- [ ] Create the publication on **Substack** named **"North de Noise"** (handle
      `northdenoise`), tagline
      *"Institutional-grade research. No minimums. No noise."*
- [ ] Write the **About page**: who you are, the verifiable record (link FINRA
      BrokerCheck / CRD 6510444), the standard you hold yourself to, what readers
      get. Reuse the manifesto in `issues/01-signal-not-noise.md`.
- [ ] Set up **payments** in Substack (connect Stripe) but keep everything free
      for now. Pre-configure the tiers: **$49/mo**, **$550/yr**, and a
      **founding-member $399/yr** offer (you'll switch this on in Phase 2).
- [ ] **Lead magnet — built ✓:** the **Valuation Lab**, a free Claude skill that
      runs a DCF + DDM on any stock (`../lead-magnet/`). Zip the skill folder,
      host it, and deliver the download link in the free-list welcome email. See
      `../lead-magnet/README.md` for the gating + install steps.
- [ ] **Wire the site:** `insights.html` is already set with the name, price, and
      teaser cards — paste your real Substack URLs into the `__SUBSTACK_URL__` /
      `__SUBSTACK_PAID_URL__` placeholders and the embed box.
- [ ] Issues are drafted — **all 12 are in `issues/`** (a full ~90-day ramp). Add
      dates and a fresh Word Salad quote per issue, then schedule.
- [ ] **Pre-sell / waitlist page (before issue #1):** stand up a simple landing page
      (Substack's built-in landing page works) that captures emails with the
      **Valuation Lab** as the hook plus a **3-question segmentation quiz** ("what's
      your biggest finance frustration?"). Two wins: it builds the launch list, and
      the answers tell you which issues to lead with. (See *Growth engine* below.)

---

## Phase 1 — Free ramp (weeks 1–4)

**Goal: publish consistently, prove the standard, grow the list. No paywall yet.**

- [ ] **Week 1:** lead with `13-theyre-selling-you-a-payment.md` (the four-square
      teardown) — show, don't tell; it demonstrates the brand in action and is the
      most shareable piece. Pin `01-signal-not-noise.md` (the manifesto) as the
      "Start here" post / About. Announce everywhere you have a presence.
- [ ] **Week 2:** publish `02-the-10x-teardown.md` (flagship *Signal vs. Noise*).
      This is your most shareable issue — make it the one you push hardest.
- [ ] **Week 3:** publish a fresh issue from the calendar (e.g. #3 *position
      sizing*).
- [ ] **Week 4:** publish `03-what-a-dcf-can-and-cant-tell-you.md` — but show the
      free/paid split: free intro + method, "deep model walk-through goes to paid
      subscribers starting next week."
- [ ] **Distribution each week:** repurpose the *Signal vs. Noise* segment as a
      LinkedIn post (you have the audience there) and an X/Twitter thread that
      links back to the full issue. Seed the first 50–100 subs from your network.
- [ ] **Track:** open rate (aim >40%) and subscriber growth. Reply to every
      comment — early engagement compounds.

---

## Phase 2 — Switch on paid (week 5)

**Goal: convert the warm list, protect the deep work.**

- [ ] Announce the **founding-member offer** ($399/yr, capped seats, time-limited).
      Scarcity + reward-the-early-believers is what drives launch conversions.
- [ ] From now on, **paywall the deep section** of each issue: free above the fold
      (intro + *Signal vs. Noise* + *The Number*), paid below (*The Read* +
      models + Q&A).
- [ ] Send a dedicated launch email explaining exactly what paid gets, with the
      advisor-fee / terminal-cost comparison (premium pricing needs justification).
- [ ] Keep the free funnel alive — never stop publishing genuinely useful free
      content, or list growth stalls.
- [ ] **Turn on paid amplification (optional, once something converts organically):**
      install a conversion pixel on the free-list signup, set a **small daily test
      budget you're comfortable losing**, and run credibility-led ads (real CRD, zero
      promises) that grow the **free** list — let free→paid do the monetizing. Optimize
      on *cost-per-free-subscriber*, double down on what works. (See *Growth engine*.)

---

## Phase 3 — Ongoing rhythm

- [ ] **Weekly issue**, same format, every week.
- [ ] **Monthly flagship** — a longer paid research report (deeper than a normal
      issue). This is the anchor that justifies $49/mo.
- [ ] **Quarterly:** review churn, open rate, and free→paid conversion; survey
      paid subscribers on what they want more of.
- [ ] Cross-sell the [store](../store.html) models and the
      [course](../course.html) to engaged readers (subscriber discount).

## Growth engine — steal the mechanics, refuse the hype

Adapted from the AI "vibe marketing" playbooks. The *execution loop* is genuinely
strong; the "printing millionaires" promise and the invented "12,000 on the waitlist"
social proof are exactly the noise North de Noise exists to mock. So we take the loop
and refuse the lie — and the refusal is a feature, because credibility is a thing the
grifters can't fake and we can prove.

**The loop, adapted honestly:**

1. **Validate demand with data, not vibes.** Before over-investing, look at what finance
   questions actually resonate — search trends, comment sections, what people keep
   asking and nobody answers straight. The underserved "hot category": smart people who
   want signal and can't find it. Confirm the angle before scaling it.
2. **Pre-sell before you fully launch.** A waitlist/landing page (Substack's works)
   capturing emails with the Valuation Lab hook + a short **segmentation quiz.** You get
   a launch list *and* first-party intel on which pains to lead with. (Deliver the lead
   magnet on signup — Phase 0.)
3. **Organic first — the teardown *is* the viral unit.** Your honest equivalent of the
   "before/after" format is the **Signal vs. Noise teardown** and **Word Salad.**
   Repurpose every issue's segment to LinkedIn/X with a link back. This is the primary,
   near-free channel early, and it compounds credibility.
4. **Then amplify with paid — carefully, and only what already converts.** Conversion
   pixel on the free-list signup → small daily test budget → let the platform find
   lookalikes of your *best* subscribers → optimize on cost-per-free-subscriber. AI can
   draft ad variants; every one must clear the firewall below.
5. **Make it self-improving.** Weekly, pull the best-performing content/ads, double down,
   kill the losers, iterate. The compounding is real (Issue #46) — the same effect the
   video sells, minus the fabrication.

**The integrity firewall (non-negotiable — this is the moat):**

| Take (the mechanics) | Refuse (the hype) |
|---|---|
| Data-validated demand; pre-sell landing page + quiz | Fabricated waitlist counts / fake reviews / invented social proof |
| Conversion pixel, lookalike targeting, test budgets | "Get rich" / "printing millionaires" / income or return promises |
| AI-assisted ad *drafts*, measured and iterated | AI-*written claims* nobody verified (the human owns every claim — see #15) |
| Real scarcity (the capped founding-member offer) | Manufactured urgency / fake countdowns |
| **Verifiable credentials (CRD 6510444) as the hook** | Anonymous authority, rented-Lamborghini theatrics |

Note the presenter herself refused the fake social proof — that's the line, and it's
ours too. For a *finance* audience the firewall isn't just ethics: income/return
promises are also a regulatory landmine. The ad angle no competitor can copy is the one
thing they don't have — *a real name and a record you can check.*

## Sell before you build — the validate-first loop (Origami/Finn, adapted)

The store waitlist we shipped *is* this playbook: prove demand before spending a
month building the wrong model. The transferable mechanics — and the two places a
finance brand must draw a harder line than a generic SaaS founder.

**Take (the mechanics):**

- **Validate demand before building.** A no-charge waitlist / letter-of-intent
  beats intuition every time. Build the models in the order the list votes for —
  the `?model=` tags on the store form *are* that vote. Don't build model #2 until
  the list asks for model #2.
- **Deliver manually first, then productize.** Finn shipped lead spreadsheets by
  hand before the software existed, and the manual work became the product spec.
  Brady's equivalent already exists: the **custom-advisory** card. Hand-build the
  DCF / Monte-Carlo model as a bespoke engagement for the first few buyers, learn
  what they actually change and need, *then* turn the repeated request into the
  productized template. The manual version writes the spec for the product.
- **Booked demand is leverage.** A committed waitlist and signed LOIs are what you
  point at to justify the build, bring in help, or price with confidence — even
  before a dollar is realized.
- **B2B pays; consumers nickel-and-dime.** See the strategic note below.

**Refuse (the finance-specific landmines Finn can use and we can't):**

- **No "risk-free / pay-only-if-it-works" on investment outcomes.** For a SaaS
  lead-gen tool a performance guarantee is a great offer. For anything touching
  investing it is a **guarantee / performance promise** — the exact Rule 2210
  landmine the brand refuses. A satisfaction guarantee on a *deliverable* ("don't
  pay until the model's in your hands and it runs") is fine; a guarantee on
  *returns* is never.
- **Never take money for a product you imply is finished.** Validating at a stated
  future price with *no charge* — what the store does now — is clean. Pre-selling
  is only honest if you then actually deliver (manually is fine; vaporware is not).
  The brand's whole premise is anti-vaporware; don't trip on it chasing momentum.

## The B2B lever (the biggest under-used idea in this plan)

Finn's hardest-won lesson: broke consumers killed his college tool at a $1.99
paywall; businesses paid $500–$5,000/mo for the same *type* of work. North de
Noise currently points mostly at retail investors ($49/mo). The higher-margin,
more-defensible revenue is **B2B**: RIAs and financial advisors who'd pay for
white-label models, planners who want the Monte-Carlo engine, research desks and
fintechs that want the analysis. The **Business-Plan/GTM kit ($2,500)** and the
**custom-advisory** card are already B2B-priced — lean into that lane. One advisor
contract can be worth 100 retail subscribers, and businesses don't churn over a
dollar. Worth a dedicated waitlist track and some direct outreach.

## Benchmarks to sanity-check yourself

- Free→paid conversion of **2–5%** is healthy for a premium newsletter.
- At $550/yr, **even 100 paid subscribers ≈ $55k/yr.** The math works at small
  scale *because* the price is premium — which is exactly why the content has to
  earn it.

## Standard

Every issue meets the educational/not-advice, no-guarantees, risk-balanced,
conflicts-disclosed bar. That discipline is the brand.
