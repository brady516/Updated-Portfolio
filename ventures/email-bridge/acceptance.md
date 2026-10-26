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
| **2** | Gmail app, **pro mailbox only**; personal Gmail removed from the app and forwarded in | small — he opens a browser for personal mail | Ambiguity eliminated structurally: one account cannot default wrong. Often the right answer. |
| **3** | Apple Mail or Outlook, per-account default sender | one app change | Default sender is explicitly configurable. Real behaviour change; expect friction. |
| **4** | Google Workspace, native Gmail account | **$7/seat/mo, paid by the customer** | No IMAP ambiguity at all. **This is the escape hatch, and it destroys the per-account cost advantage** (`offer-post-gmail.md` §2). Price the job accordingly, or decline it. |

**Tier 2 deserves more credit than it looks like.** The cheapest way to guarantee a default
is to remove the alternative. Most of these customers check personal mail on a browser
anyway.

**Tier 4 is the hedge, and it is not free.** If Part 0 forces most customers to Tier 4, the
structural margin story in `offer-post-gmail.md` is wrong and the price card has to be
rebuilt. **Find that out before you sell, not after forty installs.**

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

That is a concrete, inspectable thing arriving on a schedule. It is worth $5–10/mo in a way
that standby support is not.

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

## Open

- [ ] **Fill in Part 0 from real devices.** Still the blocking item. Everything above is
      a template until that table has real results in it, and the fallback tier it forces
      determines whether the pricing in `offer-post-gmail.md` survives.
- [ ] Decide whether Tier 2 (pro mailbox only in the app) should be the *default*
      recommendation rather than a fallback. It eliminates the failure mode structurally
      instead of relying on a setting.
- [ ] Turn Part 3 into a fillable one-pager with the business's name on it — the version
      the customer keeps.
