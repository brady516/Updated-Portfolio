# North de Noise — Internal SOP

How to run the whole machine end to end. Internal doc; clarity over cleverness.
*Strategic irreverence is for the readers — this file is just the checklist.*

---

## 1. What lives where (architecture)

| Piece | Home | Notes |
|---|---|---|
| Public site | **Cloudflare Pages → northdenoise.com** | Static; deploys the `site/` folder from a **private** GitHub repo on push. Only `site/` is published. |
| Newsletter | **Substack → read.northdenoise.com** | Free + paid ($49/mo · $550/yr · founding $399/yr). |
| Payments | **Stripe** | Payment Links for store + course. Never self-host payments. |
| Store delivery | Stripe receipt / `thank-you.html` redirect | Or a delivery service (SendOwl/Lemon Squeezy) for expiring links. |
| Lead magnet | **Valuation Lab** Claude skill (`lead-magnet/valuation-lab/`) | Delivered via the free-list welcome email. |
| Booking | **Calendly** | Course intro calls + Contact page. |
| Tooling | **Salad Scout** (`salad-scout/`) | Sources Word Salad quotes from SEC/Fed. |
| Vault + backups | **12TB NAS** | Master files, course video, code; 3-2-1 backups. Not a web server. |

Full hosting/DNS detail: `HOSTING.md`.

---

## 2. One-time go-live (do once)

- [ ] **DNS:** apex `northdenoise.com` → GitHub Pages A records; `read` CNAME → Substack. (`HOSTING.md`)
- [ ] **GitHub Pages:** Settings → Pages → deploy from default branch, root. Enforce HTTPS.
- [ ] **Substack:** create publication, set custom domain `read.northdenoise.com`, create the three tiers + founding offer, paste the welcome automation from `newsletter/welcome-email.md`.
- [ ] **Stripe:** create a Payment Link per store product + the course; set each link's post-purchase redirect to `thank-you.html` (or attach the file).
- [ ] **Calendly:** create the intro-call event.
- [ ] **Lead magnet:** zip `lead-magnet/valuation-lab/`, host it, put the link in the welcome email (`__DOWNLOAD_URL__`).
- [ ] **Fill every placeholder:** search the repo for `__` and replace each `__STRIPE_LINK_*__`, `__CALENDLY_URL__`, `__DOWNLOAD_URL__`, `__POST_URL_*__`. (Substack subscribe URLs are already wired.)
- [ ] **Salad Scout:** clone the repo to your machine/NAS, set your UA, run the step-1 offline test (see §6).

---

## 3. Weekly newsletter loop (the core recurring SOP)

Target: one issue/week. Budget ~60–90 min with everything drafted.

1. **Pick the issue.** Next slot in `newsletter/editorial-calendar.md` (all 12 are drafted in `newsletter/issues/`).
2. **Source the Word Salad** (paid issues). Run Salad Scout locally:
   ```
   cd salad-scout
   python -X utf8 salad_scout.py edgar --forms 8-K --days 30 --max-docs 15 --per-company 1 --top 12 --ua "Brady Gallagher blgallag.bg@gmail.com"
   ```
   or `bash source-the-bank.sh` for all themes at once. Pick the best line.
3. **Draft the translation.** Run the decoder for an honest first pass:
   ```
   python translate.py --quote "the exact sentence you picked"
   ```
   It gives you DECODED jargon, a rough literal swap, and the provable TELLS. Then
   **polish in your voice** and drop the quote in verbatim with attribution
   (company, form, date, link), replacing the issue's illustrative placeholder.
4. **Run the integrity checklist** (§5). Non-negotiable.
5. **Final read** in voice (`newsletter/voice-and-brand.md`): smirk + true + compliance-safe.
6. **Schedule in Substack.** Free above the fold; paywall the deep section (from week 5 on).
7. **Distribute.** Repurpose the *Signal vs. Noise* segment to LinkedIn/X as a teaser linking back. Seed engagement.

---

## 4. Monthly / periodic

- [ ] **Flagship issue** (calendar marks 4, 8, 12, then every 4th) — longer paid research report.
- [ ] **Metrics:** open rate (aim >40%), free→paid conversion (2–5% is healthy), churn. Note what resonated.
- [ ] **Backups (3-2-1):** confirm working copy + NAS + offsite; **test a restore.** An untested backup is a hope.
- [ ] **Cross-sell:** point engaged readers to the store models / course (subscriber discount).
- [ ] **Refill the calendar** before the drafted 12 run out; mine `editorial-calendar.md` backlog.

---

## 5. Integrity checklist (every issue — the brand depends on it)

- [ ] **Disclaimer present and straight.** No jokes in the disclosure.
- [ ] **No guarantees / no "this will."** Probabilities and ranges only.
- [ ] **Every Word Salad quote is real, verbatim, and attributed** — never invented, never paraphrased-then-attributed.
- [ ] **Mock the words, not a motive.** Every factual implication is provable from the quoted text. No invented claims about data, intent, or wrongdoing.
- [ ] **Conflicts disclosed inline** when an issue references a store product or the course.
- [ ] **Credentials framed as held/verifiable**, never "currently registered."

If any box is unchecked, it doesn't ship. (Reference: `newsletter/voice-and-brand.md`, `newsletter/word-salad-bank.md`.)

---

## 6. Salad Scout — operating notes

- **Step-1 sanity test (offline, proves the engine):**
  ```
  echo "We remain constructive with significant optionality and asymmetric upside amid a dynamic macro backdrop." | python -X utf8 salad_scout.py score --stdin --top 3
  ```
- **Live sourcing:** `edgar` mode (SEC), `url` mode (Fed statements — public domain), `score` mode (a saved earnings-call transcript .txt).
- **Target one company:** add `--entity "Ford Motor Co"`.
- **Knobs:** `--per-company 1` for ticker diversity; widen with `--days 60` / `--max-docs 25` / `--per-doc 8` if results come back thin.
- **Run it on your machine or NAS** — SEC blocks shared/proxy IPs; your residential IP is fine. Stay under SEC's 10 req/s (the tool already paces itself).
- Detail: `salad-scout/README.md`.

---

## 7. Updating the site

1. Edit the website files in **`site/`** (HTML/CSS/JS). Keep all web files inside
   `site/` — anything outside it is never published.
2. Commit and push.
3. Cloudflare Pages auto-builds in ~1–2 min; hard-refresh to confirm.
4. Keep disclaimers straight and copy in voice (`newsletter/voice-and-brand.md`).

---

## 8. Document map

| Need | File |
|---|---|
| This runbook | `SOP.md` |
| Hosting / DNS / deploy | `HOSTING.md` |
| Brand voice + rules | `newsletter/voice-and-brand.md` |
| Newsletter strategy | `newsletter/README.md` |
| Launch ramp (90 days) | `newsletter/launch-playbook.md` |
| 12-issue plan | `newsletter/editorial-calendar.md` |
| Drafted issues | `newsletter/issues/` |
| Welcome email | `newsletter/welcome-email.md` |
| Word Salad sourcing | `newsletter/word-salad-bank.md` |
| Salad Scout tool | `salad-scout/README.md` |
| Lead-magnet skill | `lead-magnet/README.md` |
