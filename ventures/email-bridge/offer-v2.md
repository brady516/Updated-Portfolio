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

### Flow vs stock — and why you need both

The freemail list in `leadfinder.py` is a **stock**: finite, and it depletes as you work it.
New filings are a **flow** — replenishing every month, never exhausted. A flow-based source
means the business doesn't decay as you sell into it.

**But the flow alone is too thin to live on in a single niche** (§9: ~5–6 filings/month for
one trade in one metro). The stock is the volume backstop — one metro holds *thousands* of
existing trades businesses already on freemail, available now. Work both: the flow for
timing and a warm opener, the stock for volume. The flow's advantage is the *moment*, not
the size.

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

> **But read §9 before banking on this moat.** It only exists on the local path, and the
> local path caps volume at roughly 5–10 installs/month. The moat and the volume are a
> trade-off, not a package.

---

## 9. TAM: the required-share argument is wrong — use reachable flow

**An earlier version of this section argued that one operator needs only 0.027% of the
national high-propensity flow, and concluded the business therefore cannot fail for lack
of demand. That argument is invalid and has been removed.** It is the "we only need 1% of
a huge market" fallacy: **required share is not attainable share.** Market share is not a
dial. The 147k monthly filings are scattered across 50 states and every industry with no
common channel, so 0.027% of a diffuse national market is not easier to reach than 10% of
a concentrated local one. The only denominator that means anything is **how many qualified
prospects you can put this specific offer in front of in a month.**

### Official figures (Census BFS, September 2026, seasonally adjusted)

| Series | Monthly |
|---|---|
| Total business applications | **534,947** |
| High-propensity (likely to become employers) | **147,331** (~28%) |
| **Construction (NAICS 23)** | **48,078** (~9% of total) |

Useful property: Census publishes the shell/dormant haircut for you via high-propensity,
with weekly state and regional detail on FRED. So reachable flow can be **measured, not
estimated.**

### Reachable flow, worked downward

Construction applications run ~**0.141 per 1,000 people per month** nationally. Scaling by
population:

| Scope | Construction filings/month |
|---|---|
| National | ~48,000 |
| Ohio (~11.8M) | **~1,660** |
| Toledo MSA (~640k) | **~90** |
| Toledo MSA, **one trade** (~6% of construction) | **~5–6** |

Now put the funnel against it. Cold contact-to-close on a new filing is realistically
**2–5%** — call it 3%. Forty installs/month therefore needs **~1,300 qualified contacts
per month.**

| Channel | Monthly flow | Covers 40 installs? |
|---|---|---|
| One trade, one metro | ~5–6 | **No — off by 200x** |
| All construction, one metro | ~90 | No — off by ~15x |
| All sectors, one metro | ~1,020 | Marginally |
| **All construction, statewide** | **~1,660** | **Yes** |

### The real finding, which inverts an earlier conclusion

**"Narrow hard — it costs you nothing" was exactly backwards.** One trade in one metro
yields ~5 prospects/month. Narrowing is the most expensive decision available, not a free
one. To support one full-time operator you need roughly **one sector statewide, or one
metro across all sectors.**

And that creates the actual strategic fork, because **the moat in §8 and the volume needed
here are in direct conflict:**

| | **Local & narrow** | **Wide (statewide, one vertical)** |
|---|---|---|
| Installs/month | ~5–10 | ~40 |
| Revenue at v2 pricing | ~$2.5–5k/mo | ~$20k/mo |
| Moat | intact — local, referral-dense, the call | **gone** — no local credibility |
| Competes with self-serve SaaS | barely | **directly, on their turf** |
| Marketing | word of mouth, partners | real paid acquisition with real CAC |

These are two different businesses. The local one is a solid side income with a defensible
moat. The wide one is a real company that has to win on marketing against funded self-serve
competitors. **Pick deliberately** — this is the decision, not the TAM.

### The gap this exposes in the pricing doc

`offer-post-gmail.md` models contribution with **CAC set to zero.** That is fine for
referral and word-of-mouth volume; it is not fine for the wide path. At $499 with a $150
blended CAC the contribution math is a materially different business, and CAC becomes the
variable that decides viability. **Measure cost per qualified conversation before
committing to the wide path.**

### What to measure instead of TAM

1. **Reachable qualified flow/month** in the exact geography and vertical chosen.
2. **Contact-to-close rate**, by channel — the 3% above is a placeholder.
3. **Cost per qualified conversation.**
4. **Hours per install**, which sets the ceiling.

Those four decide this business. The national figure only ever answered "could this be big,"
which was never the binding question.

*Sector and per-capita figures are calculated from Census BFS releases via third-party
summaries, not pulled from Census tables; the construction share is my arithmetic, not a
figure Census publishes. Census revised the high-propensity definition in Jan 2026.*

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
