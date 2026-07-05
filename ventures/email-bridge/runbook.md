# Remote delivery runbook — LookLegit Email

Every setup happens from your desk. The client can be in any state. Total hands-on
time per client once you've done a few: **~20 minutes** (was 45 — the script eats
the middle).

**The shape of it:** two texts, one script run, one 10-minute call.

---

## 0. One-time setup (yours, once)

- [ ] Cloudflare **API token** (My Profile → API Tokens): Zone.Zone edit, Zone.DNS
      edit, Email Routing edit. Export as `CF_API_TOKEN`; grab `CF_ACCOUNT_ID` from
      any zone Overview page.
- [ ] A **Calendly** link with a 15-minute "Email activation call" slot type.
- [ ] A **Stripe Payment Link** for $299 (+$50 domain variant, $199 crew-seat).
- [ ] Templates saved as text snippets (below): the intake text, the call-booking
      text, the cheat sheet, the signature block.
- [ ] Google Meet (or plain speakerphone) for the screenshare.

---

## 1. Lead comes in (form → your phone)

Formspree emails you the order: name, business, phone, current email, domain status.

**Same day, text them** (trades answer texts, not email):

> "Hey [name], it's Brady — you filled out the LookLegit form for [business]. Two
> quick questions and I can have you set up in 48 hrs: 1) If you own your web
> address, who did you buy it from (GoDaddy/Namecheap/etc.)? 2) What should the new
> email say — hello@, mike@, office@? I'll text you a payment link once we're set."

Decision point:
- **They own a domain** → you need registrar access for one thing only: pointing
  nameservers at Cloudflare. Easiest: a 2-minute part of the activation call where
  *they* log in and read you the screen / you talk them through pasting two values.
  Never store their password.
- **No domain (+$50)** → you register it (any registrar; Cloudflare Registrar keeps
  everything in one place) in *their* name/business, on the order. It's theirs.

Send the Stripe link when they confirm. **Payment before provisioning.**

---

## 2. Provision (the script — ~2 minutes)

```bash
export CF_API_TOKEN=... CF_ACCOUNT_ID=...
python3 provision.py setup --domain mikesdrywall.com \
    --address mike --forward-to mikesdrywall1987@gmail.com
```

The script: creates the zone, enables Email Routing, adds the forwarding route,
registers their inbox as a destination (Cloudflare emails them a **verification
link**), and writes merged SPF + DMARC. It then prints exactly which human steps
remain.

**Text #2 — book the call:**

> "[Name] — your professional email is built. Two things left, both easy: 1) check
> your inbox for a Cloudflare verification email and click the link. 2) Grab a
> 10-minute slot here and we'll switch it on together: [calendly]. That call is the
> last step — you'll send your first email as [mike@mikesdrywall.com] on it."

---

## 3. The activation call (10–15 min, screenshare or speakerphone)

The only part that can't be scripted — it's inside *their* Google account. Walk them
through, in order:

1. **Nameservers** (only if they own the domain elsewhere): they log into their
   registrar, you dictate the two Cloudflare nameservers. 2 minutes.
2. **Verification link** clicked? (If not, do it now — mail doesn't flow until.)
3. **Gmail send-as:** myaccount.google.com → Security → 2-Step Verification on →
   App passwords → create one → Gmail Settings → Accounts → "Send mail as" → add
   `mike@mikesdrywall.com` → SMTP `smtp.gmail.com`, port 587, username = their
   gmail, password = the app password → Google sends a confirmation code **to the
   new address**, which forwards right back into their inbox → paste code. Done.
4. Set **"Reply from the same address the message was sent to."**
5. **Live test on the call:** you email their new address; they watch it arrive;
   they reply; you confirm it came back as the pro address. The magic moment —
   let them feel it.
6. **Install the signature** (paste your templated block: name, company, phone,
   license # if applicable).

**Before hanging up (the two sentences that pay):**
> "If you've got techs or office staff, matching addresses are $199 each — makes
> every estimate look like one company. And if you know one other [trade] still on
> a gmail address, send them my link — you're now the guy with the pro email."

## 4. Close out (5 min, async)

- [ ] Run `python3 provision.py check --domain mikesdrywall.com` — everything green.
- [ ] Send from your address to theirs + confirm reply lands (belt and suspenders).
- [ ] Text the **cheat sheet** (one page: how to send from the new address on
      phone/desktop, what to do if something looks off, your break-fix rate).
- [ ] Mark the order done. **No lingering.** Break-fix later = separate paid booking.

---

## Scale path (when volume shows up)

The runbook *is* the automation: every step is scripted or templated, so the whole
delivery can be handed to a **VA on Zoom** the day volume justifies it — you keep
sales texts and nothing else. That's also the sunset ramp: VA takes delivery →
you take the margin → RIA revenue crosses the line → hand it off or kill it.

## The one rule

Never drive anywhere. If a step seems to need your physical presence, the process
is wrong — fix the process. Every dashboard in this business has a URL.
