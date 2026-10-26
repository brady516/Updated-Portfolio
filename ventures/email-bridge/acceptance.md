# Identity Migration — Acceptance Standard

**Status:** delivery standard. This is the artifact that turns §5 of `offer-v2.md` into a
repeatable service, the evidence behind the guarantee, and the document you train someone
else from.

**The acceptance test is binary:**

> **Does the customer, on their own phone, using their normal habits, send as the business
> by default?**

If no, **the install has failed** — regardless of whether DNS, SPF, DKIM and DMARC are
perfect. Provisioning is a prerequisite, not a deliverable. Nothing below closes a ticket
except Part 2 and Part 3.

---

## Part 0 — Platform qualification (do this ONCE, before you sell)

**Do not standardise on a mail app until this table is filled in from real devices.** The
assumption that adding an IMAP account to the Gmail app makes it the default sender is
*untested*, and it is the single load-bearing assumption in the offer. It may hold in
compose and fail in reply-from-notification. Test every flow separately.

Run on **a real iPhone and a real Android**, with two accounts in the app: a personal
`@gmail.com` and the pro IMAP mailbox.

| # | Flow | iOS result | Android result |
|---|---|---|---|
| 1 | Compose new message from inside the app | | |
| 2 | Reply to a message received **at the pro address** | | |
| 3 | Reply to a message received at the **old gmail and forwarded in** | | |
| 4 | Reply launched **from a push notification** | | |
| 5 | Forward an existing message | | |
| 6 | Compose from **outside** the app — share sheet, "email this photo" | | |
| 7 | All of 1–6 again **after a force-quit and cold start** | | |
| 8 | All of 1–6 again **after an app update** | | |

Record for each: device model, OS version, Gmail app version, and the **From** address
that appeared *without the user touching the picker*.

**Pass criterion, per flow:** the pro address is pre-selected. **Not** "selectable."
*Available is not default.*

**Flow 6 is the one that will bite you.** Trades customers send job photos from the camera
roll, not from the mail app. A share-sheet compose that defaults to the personal account
sends @gmail.com to the customer holding the quote.

**Flow 3 is the second one.** Mail forwarded in from the old Gmail may carry a reply
context that pulls the old identity back in.

### If a flow fails — the fallback ladder

Work down. Stop at the first tier that passes Part 2, and **record which tier the customer
is on** — it is a support and re-verification fact.

| Tier | Configuration | Cost of the change | Trade-off |
|---|---|---|---|
| **1** | Gmail app, pro mailbox added over IMAP, pro set as default | none — zero behaviour change | Best case. Only valid if **every** flow in Part 0 passes. |
| **2** | Gmail app, **pro mailbox only**; personal Gmail removed from the app and forwarded in | small — he opens a browser for personal mail | Ambiguity eliminated structurally: one account cannot default wrong. **Introduces its own failure modes — qualify against Part 0b before offering it, let alone defaulting to it.** |
| **3** | Apple Mail or Outlook, per-account default sender | one app change | Default sender is explicitly configurable. Real behaviour change; expect friction. |
| **4** | Google Workspace, native Gmail account | **$7/seat/mo, paid by the customer** | No IMAP ambiguity at all. **This is the escape hatch, and it destroys the per-account cost advantage** (`offer-post-gmail.md` §2). Price the job accordingly, or decline it. |

**Tier 2 deserves more credit than it looks like** — and more scrutiny. The cheapest way to
guarantee a default is to remove the alternative. But **eliminating the wrong choice is
only a solution if you haven't eliminated something he needs.** It trades one failure mode
for a different one, and the new one is harder to see because it shows up in his personal
life, not his business. Part 0b qualifies it.

**Tier 4 is the hedge, and it is not free.** If Part 0 forces most customers to Tier 4, the
structural margin story in `offer-post-gmail.md` is wrong and the price card has to be
rebuilt. **Find that out before you sell, not after forty installs.**

---

## Part 0b — Tier 2 qualification (run before Tier 2 is offered, never mind defaulted)

Tier 2 removes the competing sender identity from the app. It also removes his personal
inbox from the app. **Those are not the same trade, and the second one is on him, not on
you.** Run the full Part 2 matrix *plus* these. A Tier 2 install that passes Part 2 and
fails here has not passed.

| # | Flow | Result | Notes |
|---|---|---|---|
| 1 | He **replies to a forwarded personal message** — to a friend, his kid's school | From shows…? | **The mirror failure.** Personal mail now leaves as the business. |
| 2 | **Google account mail** — security alerts, 2FA codes, recovery, Play receipts — still reaches him | | These are addressed to the Gmail account he no longer opens. A delayed or spam-foldered forward means a missed security code. |
| 3 | **Google Business Profile notifications** still reach him | | Often tied to the Google account, not the business mailbox. |
| 4 | Forwarded mail **arrives complete and in the inbox** — not spam, not clipped | | Forwarding breaks SPF alignment; some senders spam-folder or bounce on the second hop. |
| 5 | **Can the Gmail account even be removed from the app** on his Android without disturbing the device-level Google account | | Untested assumption. On Android the app account and the system account may not separate cleanly. |
| 6 | Where does he **read and send personal mail** now — and will he actually go there | | If the answer is "I'll just add it back," Tier 2 is already undone. |
| 7 | Gmail-native behaviour he relies on and loses: labels, categories, filters, search history | | |

**Tier 2 acceptance additionally requires a recorded consent line:**

> *"Personal mail moves out of this app and into the browser. Replies to personal messages
> will go out from your business address unless you send them from the browser. Google
> security codes still go to your Gmail — here's where to find them."*

- [ ] Trade-off stated in these terms, out loud
- [ ] Customer accepted it: ☐ yes ☐ no → if no, go to Tier 3
- [ ] Recorded, with date

**The reason this matters commercially, not just ethically:** a customer who re-adds his
Gmail to the app in week two silently reverts to the exact failure the offer exists to
prevent, and you will not find out until the quarterly re-verify. **Tier 2's control is
only as durable as his agreement with it.**

---

## Part 1 — Provisioning verification (prerequisite, not acceptance)

Technical. Necessary. **Guarantees nothing to the customer.**

- [ ] Domain registered **in the business's name**, or connected if owned.
- [ ] Mailbox(es) live at the host; **account owned by the customer** (`offer-post-gmail.md` §4).
- [ ] MX records resolving; inbound mail delivered.
- [ ] **SPF** present and correct.
- [ ] **DKIM** signing, verified on a real received message's headers.
- [ ] **DMARC** published.
- [ ] Test message to an **external** mailbox (not your own domain) — **lands in inbox, not
      spam or promotions**. Check at least one Gmail and one Outlook recipient.
- [ ] Old Gmail forwarding into the new mailbox, confirmed with a live message.
- [ ] Signature installed on phone **and** computer.

---

## Part 2 — Adoption acceptance (ON THE CALL, ON THEIR DEVICE)

**The customer holds the phone. You do not touch it.** If you drive, you have tested your
own competence, not his configuration.

| # | Test | Pass = | Result | Notes |
|---|---|---|---|---|
| 1 | He composes a new message to you | From shows the **pro address**, untouched | | |
| 2 | You email his pro address; he replies | Goes out **from pro** | | |
| 3 | You email his **old gmail**; it forwards in; he replies | Goes out **from pro** | | |
| 4 | You email him; he replies **from the notification** | Goes out **from pro** | | |
| 5 | He sends you a **photo from his camera roll** | Goes out **from pro** | | |
| 6 | He force-quits the app, reopens, composes | Goes out **from pro** | | |
| 7 | Notifications fire for the pro account, on his device, observed | Yes | | |
| 8 | He finds the pro inbox **without being told where** | Yes | | |
| 9 | His personal Gmail still works | Yes — **demoted, not deleted** | | |

**Record the tier** from Part 0 that this customer ended on: ____

**Any FAIL in 1–6 = the install has failed.** Move down the fallback ladder and re-run the
whole table. Do not close with a workaround the customer has to remember — *"just tap the
From line each time"* is not a pass. It is the failure mode the offer exists to prevent.

**Test 8 matters more than it looks.** If he cannot find it unaided on day one, he will not
find it in week three, and the mailbox becomes the thing he never checks.

---

## Part 3 — Surface register (the guarantee's evidence)

Every surface is **enumerated, changed, and independently verified**. What is not on this
register is not guaranteed. This register *is* the scope of the guarantee, and a copy goes
to the customer as the verification report.

### Google Business Profile — treat as critical, never cosmetic

This is where customers actually find him. **Fix the mailbox and leave the Business Profile
on gmail, and nothing has been solved where it costs bids.**

| Field | Value |
|---|---|
| Profile URL / listing name | |
| Email shown **before** | |
| Email shown **after** | |
| Date changed | |
| Published and re-checked on (date) | |
| Verified by | logged-out view / incognito / screenshot |

**Verification is a second visit, not the moment you click save.** Business Profile edits
can sit in review, can be rejected, and can be altered later by Google or by a third-party
"suggest an edit." **Re-check after it publishes, from a logged-out browser, and keep the
screenshot.** Saving is not changing; changing is not published; published is not verified.

### All other surfaces

| Surface | Where / URL | Old value | New value | Changed | Verified how | Evidence |
|---|---|---|---|---|---|---|
| Website contact page | | | | | | |
| Website form **destination** | | | | | | |
| Invoicing / estimating software | | | | | | |
| Quote & estimate templates | | | | | | |
| Email signature (phone + desktop) | | | | | | |
| Facebook / social profiles | | | | | | |
| Voicemail script | | | | | | |
| Supplier & trade accounts | | | | | | |
| Cards / truck / yard signs | | | | | | |

**Website form destination is a separate line from the contact page on purpose.** The page
can display the new address while the form still delivers to gmail. Submit the form and
confirm where it arrives.

**Cards, truck and signs are flagged, not fixed** — they are the next print run. Record
them as *known outstanding, customer-acknowledged*. Enumerated and excluded beats
unenumerated.

**Anything found and not changed goes on the register as outstanding, with a reason.** An
unrecorded surface is an unmeasured state, and the guarantee cannot cover what was never
counted.

---

## Part 4 — The guarantee, as it is actually written

Distinguish the **marketing promise** from the **contractual guarantee**. They are not the
same sentence, and conflating them is how a good offer becomes an unwinnable argument.

**Marketing promise (the headline):**

> *"Nobody sees @gmail.com from you again."*

**Contractual guarantee (what you will defend):**

> Your business address sends by default on your own phone, verified in front of you across
> every flow on this report. Every surface on the attached register is changed and
> verified. **If anything on this register is wrong, we fix it free.** If we cannot make
> your phone send from your business address by default, **you don't pay.**

You guarantee **the verified configuration and the enumerated surfaces** — bounded,
auditable, and entirely within your control. You do not guarantee that he will never type
his old address into a form in 2028, that a supplier won't resurrect it from an old record,
or that a customer with the old address in their phone won't use it. **Say that out loud on
the call.** A bounded guarantee you always honour is worth more than an absolute one you
have to argue about.

**Two cure rights, deliberately asymmetric:** register errors get **fixed free** — cheap,
fast, and it keeps the relationship. The default-sender failure is the only
**money-back** trigger, because it is the one thing that means the product didn't work at
all.

### The promise and the service cadence must agree

**"Nobody sees @gmail.com from you again" implies continuous compliance. Quarterly checks
are not continuous compliance.** If the promise and the cadence disagree, the gap is a
future argument you will lose.

Split it by what can actually be watched:

| What | Can it be monitored continuously? | What you may claim |
|---|---|---|
| Domain expiry, MX, SPF, DKIM, DMARC | **Yes** — machine-pollable, cheap | Continuous. Alert on break. |
| Website form destination, Business Profile value | **Partly** — scriptable fetch, needs care | Periodic, on the stated cadence |
| **Default sender on his phone** | **No.** Requires his device | **Point-in-time: verified at install, re-verified on the cadence** |

So the defensible wording is: **verified at install, re-verified every quarter, monitored
continuously on the records; between checks the configuration is yours to leave alone.**
Say it that way and the promise survives contact with reality. Claim continuous on the
one thing you cannot see and it doesn't.

---

## Part 5 — Re-verification (and why it is the recurring revenue)

The configuration **drifts**. App updates reset defaults. OS upgrades migrate accounts.
He re-adds his personal Gmail. A Business Profile edit gets reverted. Someone sets up a new
phone from a backup.

A single install is a point measurement of a system that keeps moving. **That is the honest
argument for the monthly line in `offer-post-gmail.md` — not "support," which he will never
call about.**

**Quarterly re-verify — the deliverable:**

- [ ] Re-run Part 2, tests 1–6, on his current phone.
- [ ] Re-check Business Profile from a logged-out browser.
- [ ] Re-check the website form destination.
- [ ] Re-run one external deliverability test (inbox, not spam).
- [ ] Confirm DKIM still signing and the domain hasn't lapsed.
- [ ] Re-issue the register with dates.

That is a concrete, inspectable thing arriving on a schedule, in a way standby support is
not. **But it has to clear its own cost, and at these prices the room is thin.**

### What a verification cycle can cost

Per customer per year, against `offer-post-gmail.md` COGS. Stripe is 2.9% + $0.30, which
on small monthly charges is punitive.

| | $5/mo | $10/mo |
|---|---|---|
| Gross | $60.00 | $120.00 |
| Stripe (12 charges) | −$5.34 (**8.9%**) | −$7.08 (5.9%) |
| Mailbox host (Migadu Micro) | −$19.00 | −$19.00 |
| Domain renewal | −$12.00 | −$12.00 |
| **Left for labour, 4 cycles** | **$23.66** | **$81.92** |
| **Per cycle** | **$5.92** | **$20.48** |
| At $30/hr loaded | **≈12 min** | **≈41 min** |

Expected labour per cycle is `base check + (correction rate × correction cost)`. A scripted
base check is maybe 8 minutes. At a 25% correction rate and 25 minutes per correction,
expected cost is ~14 minutes.

**Conclusions:**

- **$5/mo does not fund quarterly verification.** Twelve minutes per cycle, all-in,
  including every customer who needs corrective work. Either drop to **semi-annual** at
  that price, or don't sell it.
- **$10/mo funds it only if the base check is scripted** — DNS, DKIM, domain expiry and
  form destination are machine-checkable; write that once. The hands-on part is the device
  test, and it is the expensive part.
- **Corrections need a bound.** "We fix what the register got wrong, free" is a cure right
  on *your* error. Re-fixing drift he caused — re-added his Gmail, new phone — is a
  different thing. Allow one free, then bill it.
- **A Mini-tier host at $90/yr breaks both columns.** The plan only exists on the cheap
  per-account hosts.
- **The real home for re-verification is the term price, not a monthly line.**
  `offer-post-gmail.md` §5 already shows $599/24mo dominating every monthly variant. Eight
  quarterly cycles at ~14 minutes is ~1.9 hours ≈ $57 against ~$543 contribution. No
  per-charge fee drag, no involuntary churn, no failed-payment chasing. **Bundle it into
  the term and stop selling a $5 line item.**

---

## Part 6 — Sign-off

- [ ] Part 1 complete
- [ ] Part 2 complete, **all of 1–6 PASS**, customer-operated, tier recorded
- [ ] Part 3 register complete — every surface changed+verified or recorded as outstanding
- [ ] Register delivered to the customer
- [ ] Cheat sheet delivered
- [ ] Bounded guarantee **stated verbally** on the call
- [ ] Re-verify date set (if on a plan)

Customer: ____________________  Domain: ____________________

Install date: ____________  Tier: ____  Next re-verify: ____________

**Do not invoice before Part 2 passes.** The money-back trigger is the default sender; if it
hasn't passed, there is nothing to bill for yet.

---

## Part 7 — Measure first-pass acceptance before scaling

One log, kept from the first real install. **This is the number that decides whether this
is a repeatable service or a clever install that needs a specialist every time.**

| Install | Date | Platform | Tier reached | First-pass? | Flows that failed | Minutes on device | Minutes total | Corrections at re-verify |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

**First-pass acceptance rate** = installs passing Part 2 at **Tier 1**, first attempt,
with no client change. Track it from install one, not install forty.

What the number decides:

- **High Tier 1 rate** → 48-hour turnaround holds, the call stays short, the price card in
  `offer-post-gmail.md` stands.
- **Mostly Tier 2/3** → every install carries a behaviour-change conversation and a consent
  step (Part 0b). Longer calls, more friction on the close, more support later. Delivery
  time and conversion both move, not just the technical design.
- **Mostly Tier 4** → per-seat Workspace. **The per-account cost advantage is gone and the
  pricing has to be rebuilt from scratch.** Better to learn this at install three.

Also track **minutes on device** separately from minutes total. It is the part that cannot
be scripted, cannot be delegated cheaply, and sets the floor on what an install can ever
cost. It is also, not coincidentally, the moat.

---

## Open

- [ ] **Fill in Part 0 from real devices.** Still the blocking item. Everything above is
      a template until that table has real results in it, and the fallback tier it forces
      determines whether the pricing in `offer-post-gmail.md` survives.
- [ ] **Qualify Tier 2 against Part 0b before offering it** — in particular whether Google
      account and security mail reaches him reliably through the forward, and whether the
      Gmail account can be removed from the app on Android at all. It eliminates the
      failure mode structurally; it may eliminate something he needs. Only then ask
      whether it should be the default rather than a fallback.
- [ ] **Script the machine-checkable half of the quarterly check** (domain expiry, MX, SPF,
      DKIM, DMARC, form destination). Part 5's economics only work if the base cycle is
      minutes. `provision.py check` is the obvious place.
- [ ] **Start the Part 7 log at install one.** First-pass acceptance rate is the decision
      input for everything downstream — turnaround, price, who can be trained to do this.
- [ ] Turn Part 3 into a fillable one-pager with the business's name on it — the version
      the customer keeps.
