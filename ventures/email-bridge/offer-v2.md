# Offer v2 — "You filed the paperwork. Now look like a real company."

**This is the offer.** Pricing mechanics and COGS live in `offer-post-gmail.md`; don't
re-litigate them here. This doc defines *who it's for, what we promise, what's in it, and
why they say yes.*

**Supersedes `offer.md`.** That doc sold a $299 one-time setup to *established* trades
businesses, delivered by forwarding + Gmail "Send mail as," framed as a bridge with a
sunset. Three of those four things change.

---

## 1. The pivot in one line

> The problem was never "Gmail is going away." The problem is **@gmail.com is not
> professional** — and that problem is permanent, renewing, and arrives on a schedule.

Google retiring "Send mail as" (Jan 2027) changes **how we deliver**, not **what we sell**.
The old mechanism is dying. The job-to-be-done isn't.

---

## 2. The customer changes — and that is what makes the mechanism change free

**Old target:** established trades business already running on freemail. Found via the
Places API in `leadfinder.py` — real, trading, proven revenue.

**New target:** a business that filed **0–90 days ago.** Nationally that is **~535,000
business applications/month**, of which **~147,000 are Census "high-propensity"** — the
ones whose characteristics predict they will actually become employer businesses
(Sept 2026). Pick a geography and a trade out of that flow; see §9.

This is not a small retarget. It is the thing that makes the whole pivot work:

| | Established business | **Newly filed business** |
|---|---|---|
| Inbox habit | 5+ years in one Gmail inbox | **none yet** |
| What Send-As was for | preserving that habit ("nothing changes") | **nothing — no habit to preserve** |
| Owns a domain | often | **usually not** |
| Cost of giving them a real mailbox | a behaviour change they resist | **zero — it's what they assumed they were buying** |
| Proven revenue | yes | unproven |

**The Send-As deprecation only hurts the entrenched customer.** The whole reason the hack
existed was to avoid asking someone to change inboxes. A business three weeks old has
nothing to change *from*. So the mechanism that Google is killing was never load-bearing
for this customer — which means the deprecation doesn't shrink this business, it **shifts
the optimal channel toward new filings.**

### The flow-vs-stock property (why this is durable)

The freemail list in `leadfinder.py` is a **stock** — finite, and it depletes as you work
it. New filings are a **flow** — ~445 every month, replenishing forever. A flow-based lead
source means the business doesn't decay as you sell into it. That is the structural
difference between a campaign and an income line.

---

## 3. The wedge: lead with the domain, not the email

A business that just filed has **picked a name and not yet bought the domain.** That is
the opening, and it's far stronger than the old "noticed you're using a gmail address."

> **"mikesdrywall.com is still available. Want me to grab it before someone else does?"**

Why this works where the old opener didn't:

- **Specific to them** — their actual name, checked, not a template.
- **Real urgency, honestly** — domains do get taken. No manufactured scarcity (holds the
  integrity bar in `offer.md`).
- **It's a favour before it's a pitch** — you did free work before asking for anything.
- **Email is the natural second sentence**, not the cold open. Nobody wakes up wanting
  email. They do want their name.

The domain is the hook. The professional email is the product. Register it for them —
fold the old `+$50 domain` add-on into the base offer and remove the decision.

---

## 4. The offer

**"Your own name on your email. Live in 48 hours, flat fee, done for you."**

- **Promise:** `you@yourbusiness.com` — your domain, your mailbox, set up on your phone
  and your computer, sending and receiving cleanly, not landing in spam.
- **Turnaround:** live within **48 hours**, plus one short call to set up your phone.
- **Guarantee:** *"If it isn't sending and receiving cleanly, you don't pay."* Unchanged —
  it's the single best line in the old offer. Scope it to the term (see
  `offer-post-gmail.md`).
- **Price:** per `offer-post-gmail.md`. Lead with crew pricing; the structural cost
  advantage only pays on crews.

### What's included

- **The domain**, registered in their name (or connected if they own it).
- **A real mailbox** at that domain — owned by the business, not borrowed from a Google
  feature.
- **Up to N mailboxes** for the crew (see pricing tiers) — not per-seat.
- **Set up on their phone and their computer**, in the mail app they already use.
- **Deliverability records — SPF, DKIM, DMARC** — so bids don't land in spam.
- **A clean signature** (name, title, phone, logo if they have one).
- **A one-page cheat sheet**, and we don't hang up until mail sends both ways.

### What's explicitly NOT included

- ❌ Website, logo, branding. (Separate tiers in `rates.md`.)
- ❌ Inbox management, email writing, spam triage. We build it; you run it.
- ❌ Migrating years of old mail from their personal Gmail. Old mail stays where it is and
  stays reachable. *(Possible paid add-on later — it's real work and it's where scope
  creep will come from.)*
- ❌ Email marketing, newsletters, cold-outreach infrastructure. **Say no to this hard** —
  it puts your sending reputation in someone else's hands.

---

## 5. Why a real mailbox is a better product (not a consolation prize)

This matters: the new mechanism is an **upgrade**, and for a brand-new business it's the
*correct* architecture. Sell it that way.

- **The business owns its email from day one** — not trapped inside the founder's personal
  Google account.
- **Business and personal mail are separate from the start** — same discipline as a
  separate bank account. Easier at tax time, and it's the thing they'll wish they'd done.
- **It survives the founder's Gmail.** Lose that account, lose the password, lose the
  phone — the business email is unaffected.
- **You can hand a mailbox to a bookkeeper or a new hire** without handing over a personal
  account.
- **It transfers.** If they bring on a partner or sell, the email goes with the business.
  A Send-As on a personal Gmail does not.
- **It scales to the crew.** Real mailboxes per tech, not aliases on one person's inbox.

> **The line:** *"Your business should own its email, same as it owns its bank account.
> Not borrowed from your personal Gmail."*

That reframe is why you can charge more than $299 honestly — and it has no expiry date,
unlike anything built on the January 2027 deadline.

---

## 6. Objections (feed these into `phone-close.md`)

| They say | You say |
|---|---|
| "Gmail works fine." | It does — for you. It's on every bid you send. The customer comparing you to a competitor whose email matches their company name doesn't tell you that's why. |
| "I'll do it myself." | You can. It's a domain, MX records, a mailbox, then SPF, DKIM and DMARC so you don't land in spam. Most people get the first half done and don't find out the second half is missing until a bid goes unanswered. |
| "Do I need another app?" | No. It goes in the mail app already on your phone. Same place, your name on it. |
| "What if the business doesn't make it?" | You own the domain. Cancel anytime, nothing locked up. |
| "Can my guys get one?" | That's the better version of this — real mailboxes for the crew, priced per business, not per person. |
| "Why not Google Workspace?" | You can, at $7 per person per month, and you set it up yourself. We're one fee, every mailbox included, done for you. |
| "$X is a lot." | One bid. That's the whole math. |

---

## 7. Delivery checklist (revised — replaces step 3 in `offer.md`)

1. Collect: business name, domain (check availability / register), the crew's mailbox
   names, name/title/phone/logo for signature, what phone and computer they use.
2. Register or connect the domain.
3. **Provision the real mailbox(es)** at the host. *(Replaces the old "Send mail as +
   app password" step.)*
4. MX for receiving + **SPF, DKIM, DMARC**.
5. **Configure their phone and computer** — the step that didn't exist before and is now
   the one that earns the fee.
6. Build and install the signature.
7. **Test on the call:** send out, receive in, confirm not-spam. Then the cheat sheet.
8. Close the ticket.

**Note the shape change:** the old process was async — you did DNS, they clicked a link.
This one needs a short call. That is a cost *and* the moat: it's the part a self-serve
SaaS competitor cannot do.

---

## 8. The moat, honestly reassessed

`offer.md` claimed the moat is "too unsexy for competent operators to touch." **That is
weakening and you should know it.** The Gmail change is actively spawning self-serve
products for exactly this problem — several are already publishing migration guides and
courting this traffic.

The real moat now is narrower and more defensible:

- **They are self-serve. Your customer will not self-serve.** A drywall contractor who
  filed last month will not configure DNS records. Ever.
- **The call.** A tool cannot sit on the phone and set up an iPhone.
- **The formation moment.** A SaaS waits to be found. You arrive the week they file.
- **Local and trade-specific.** "The email guy for [trade] in [metro]" beats a generic app.

The moat is the **channel and the hand-holding**, not the technical work. The technical
work is commodity and getting more so. Price and position accordingly.

---

## 9. TAM: the number is not the finding — the required share is

**Official figures (Census Business Formation Statistics, September 2026, seasonally
adjusted):**

| Series | Monthly |
|---|---|
| Total business applications | **534,947** |
| **High-propensity** applications (likely to become employers) | **147,331** |

Two things worth knowing about this data. First, **Census publishes the haircut for you** —
"high-propensity" is their own filter for applications that look like real businesses
rather than shells and dormant filings. It runs ~28% of total, which is almost exactly the
25–40% estimate this doc previously guessed at. Use the official series, not a guess.
Second, it is available **weekly, by state and by region** via FRED, so the channel can be
targeted and measured rather than estimated.

### The actual finding

Don't underwrite on TAM. Underwrite on **required market share**, which is where this gets
interesting:

Delivery is ~0.5 hrs of provisioning (`rates.md`) plus the new phone-setup call and the
sales conversation — call it **1–1.5 hrs all-in per install**. One person realistically
closes and delivers **30–50/month** before anything breaks.

| | Figure |
|---|---|
| Installs needed/month (one operator, full) | ~40 |
| As a share of high-propensity applications | **0.027%** |
| As a share of total applications | **0.0075%** |

> **You need roughly 3 in 10,000 of the qualified monthly flow.**

### What that implies (this is the risk conclusion)

**This business cannot die of insufficient demand or of competition.** At 0.03% required
share, every self-serve SaaS competitor in §8 could succeed wildly and it would not
measurably affect your ability to find 40 customers. Market-size variance is irrelevant
here. Three consequences follow, and they should drive the next decisions:

1. **You are supply-constrained, not demand-constrained.** The binding limit is your hours,
   specifically the phone call in delivery step 5. That inverts the engineering priority:
   the highest-leverage build is **making that call shorter or unnecessary** — a tight
   cheat sheet, a guided setup page, `provision.py` doing more — *not* a provisioning
   platform. Capacity is the constraint; automate the constraint.
2. **Narrow hard. It costs you nothing.** When you need 0.03%, picking one trade in one
   metro sacrifices no reachable market and raises conversion, referral density and word
   of mouth. Breadth has negative expected value at this share.
3. **Price up, not down.** Scarce capacity against effectively unlimited demand says raise
   price until capacity clears. This is the quantitative case for the pricing in
   `offer-post-gmail.md` — and the case for never competing with Fiverr on price. Racing
   a commodity provider for a market you need 0.03% of is strictly irrational.

**So the risk is entirely in execution:** channel repeatability (can you reliably source
~40 qualified conversations/month) and delivery throughput. Those are the only two numbers
worth measuring. TAM's only job was to prove the business can't starve — it did that, and
is now a distraction.

*Figures are from Census BFS releases via third-party summaries, not pulled from the
Census tables directly. Census revised the high-propensity definition with the Jan 2026
release, so don't compare against pre-2026 numbers without checking the current series.*

## 10. What this changes elsewhere in the folder

- `offer.md` — superseded. Keep for history; don't sell from it.
- **`leadgen.md` — the cold email is now factually wrong.** It promises *"works in the
  same inbox you already use."* That was the Send-As pitch. Rewrite around the domain
  hook (§3).
- **`leadfinder.py` — needs a `filings` source.** It currently finds established freemail
  businesses (a depleting stock). New filings are the flow. The established list is still
  worth working, just with a different pitch and no "same inbox" promise.
- `runbook.md` / `SOP.md` — step 3 becomes mailbox provisioning; add the phone-setup call.
- `phone-close.md` — fold in §6.
- `faq.md` — needs the "do I need another app," "what if I close the business," and
  "why not Workspace" answers.
- `provision.py` — needs the mailbox-host path; keep it host-agnostic.
- `rates.md` — replace the Tier 1 row; **delete the $199/seat crew rate** (it prices per
  seat against a per-account cost).

## 11. Open items

- [ ] **Pick the geography and pull the real list.** FRED carries high-propensity
      applications weekly by state and region; state Secretary of State offices carry the
      actual filings with business name and address. That list is the channel — build it
      before refining the pitch.
- [ ] **Direct mail is worth testing here.** New filings publish a physical address, and a
      well-designed letter to a brand-new company is on-brand for "look legit" in a way
      cold email isn't. It also sidesteps CAN-SPAM entirely.
- [ ] **Which mail client to standardise on** for step 5 — the delivery process needs one
      default path, not improvisation per customer.
- [ ] Confirm the Jan 2027 scope from Google directly (see `offer-post-gmail.md` §8). It
      doesn't change this offer, but it sets the deadline for migrating the old book.
