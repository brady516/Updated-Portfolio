# Lead generation — finding freemail tradespeople (compliance + workflow)

`leadfinder.py` builds a list of local trades businesses running on a freemail
address (`gmail/yahoo/hotmail/...`). Those are your Go Legit Local leads. This doc is the
rulebook so the list is built *and used* cleanly — your whole brand is "look
legit," so the lead-gen can't be sketchy.

## The line (your ToS instinct, sharpened)

- ✅ **Google Places API (official, paid, has a free tier)** — the sanctioned way to
  ask "every drywall contractor in Toledo with phone + website." This is a door
  Google *built for this.*
- ✅ **Reading a business's own public website** — the contact email they published
  exists to be contacted. No ToS prohibits reading a contact page.
- ❌ **Scraping Google Search / Google Maps results directly** — against Google's
  ToS. Don't. (The Places API is the legitimate substitute.)
- ❌ **Scraping Yelp / Angi / Facebook / Thumbtack** — all prohibit it. Skip.

The tool only does the two ✅ things. It also **respects robots.txt**, uses an
**identified user-agent**, and **rate-limits** so you're a polite guest.

## The inversion that makes it work

Normal lead-scrapers *want* the professional email. **You want the opposite.**
`mike@mikesdrywall.com` = already professional = **disqualified.** `mikesdrywall1987
@gmail.com` = **the lead.** The tool tags every email `LEAD` (freemail),
`already-pro` (their own domain), or `other-domain`, and `--leads-only` keeps just
the freemail businesses. The product *is* the filter.

Bonus signal: businesses the Places step finds with **no website at all** are a
bigger, warmer conversation (they need the whole "look legit online" package). The
`places` command keeps and flags them.

## How to run it

```bash
# 1. build the target list (official API; set your key)
export PLACES_API_KEY="..."
python3 leadfinder.py places \
    -q "drywall contractor in Toledo, OH" \
    -q "electrician in Toledo, OH" \
    -q "welder in Toledo, OH" \
    -o targets.csv

# 2. harvest emails from their own sites; keep only freemail leads
python3 leadfinder.py harvest -i targets.csv -o leads.csv --leads-only
```

`leads.csv` opens straight in Google Sheets or Excel: business, phone, website,
email, status. That's your call/email list.

**Places API cost:** Text Search is billed per request with a monthly free credit
that covers a lot of prospecting; check current Google Cloud pricing before running
thousands. Keep queries tight (trade + city) to stay efficient.

## How you're allowed to CONTACT them (this matters more than the scrape)

- **Email is the channel — under CAN-SPAM.** These are business addresses; cold
  B2B email is legal *if* you follow CAN-SPAM: truthful subject/from, a real
  physical mailing address in the footer, and a working one-click unsubscribe you
  honor promptly. Keep it 1:1 and relevant, not blasted.
- **Do NOT cold-call or cold-text these numbers.** The phone/SMS world is governed
  by **TCPA**, and cold marketing texts to mobile numbers without prior express
  consent carry real per-message statutory penalties. The phone number is for
  *after* they reply and opt in (that's when your runbook's "text #1" applies).
- **Scrub against the National DNC** if you ever phone at all. Simplest: don't
  phone cold. Let email earn the opt-in, then the phone is fair game.

Rule of thumb: **freemail-found list → cold *email* only → they reply → now you can
call/text.** That sequence keeps you on the right side of both CAN-SPAM and TCPA.

## The cold email that fits the brand

Short, specific, honest — mirrors the landing page:

> **Subject:** the email on your website, [Business]
>
> Hi [name] — noticed [Business] is taking inquiries at a gmail address. Nothing
> wrong with it, but on a bid it reads a little less legit than a competitor whose
> email matches their company name. I set tradespeople up with `you@[business].com`
> — done for you, 48 hours, flat fee, works in the same inbox you already use. Want
> me to send the details? — [you], [physical address], unsubscribe: [link]

One ask, their exact situation named, and it routes replies into your runbook.

## Integrity note

Everything here is public data, accessed through sanctioned doors, contacted through
the legal channel. If any step ever feels like it needs to hide, it's the wrong step
— fix it. The list is only worth having if the business built on it is clean.
