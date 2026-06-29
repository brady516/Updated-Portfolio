# Salad Scout

Finds **Wall Street word salad** for the *North de Noise* paid segment. Ranks the
most jargon-dense sentences in public, quotable text and prints them with
citations — so picking the "Wall Street Word Salad of the Week" is a 10-minute job,
not a 24-hour CNBC marathon.

Stdlib-only Python 3 (no installs, no API keys). One file: `salad_scout.py`.

## Why these sources (not a news scraper)

Word salad is densest exactly where it's also **free and legal to quote**:

- **SEC EDGAR full-text search** — public-domain government data, official free API.
  10-K/10-Q "MD&A" and risk sections are buzzword swamps.
- **Earnings-call transcripts / IR pages** — companies publish these to be quoted.
- **Fed / FOMC statements & speeches** — public domain.

Avoid scraping Bloomberg / WSJ / Seeking Alpha: paywalled, ToS-restricted, and
copyright-heavy. You don't need them. And quoting a *short* sentence to critique it
is textbook **fair-use commentary** — just attribute it (company, form/call, date).

## Commands

```bash
# 1) Score text you already have (a transcript you saved)
python3 salad_scout.py score --input transcript.txt --top 10
cat transcript.txt | python3 salad_scout.py score --stdin

# 2) Score any public URL (Fed statement, IR transcript page, press release)
python3 salad_scout.py url "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240131a.htm" --top 10

# 3) Search SEC EDGAR full-text, fetch filings, rank the salad
python3 salad_scout.py edgar \
  --forms 10-K,10-Q,8-K --days 14 --max-docs 8 --per-doc 5 --top 15 \
  --ua "Brady Gallagher brady@northdenoise.com" --out output
```

SEC requires a declared User-Agent — pass `--ua "Your Name your@email"` for the
`edgar` command (and ideally for `url` on sec.gov).

Global flags (work on any command): `--top N`, `--format text|json|csv`,
`--lexicon FILE`.

**Target one company** (for a named, attributable quote): add `--entity` to the
`edgar` command, e.g. `--entity "Ford Motor Co"` (EFTS entityName filter).

**Source the whole newsletter bank at once:** `bash source-the-bank.sh` runs a
tuned search for each Word Salad theme (set your UA at the top first). See
`../newsletter/word-salad-bank.md` for the theme→source map.

## Output

Ranked candidates with a **salad score**, the matched **buzzwords**, the
**sentence**, and a **source** citation (for `url`/`edgar`). You pick one and write
the *Translation* + *What it's hiding*. Example:

```
#1  salad score 25.94  [accretive, best-in-class, flywheel, synergies, ...]
    “Our best-in-class flywheel unlocks accretive synergies and we will continue
     to double down on mission-critical, scalable initiatives with strong conviction.”
```

## Tuning the lexicon

The default weighted lexicon lives in `salad_scout.py` (`DEFAULT_LEXICON`).
Extend it without touching code via a file (`term,weight` per line):

```
# my-salad.txt
flywheel,3
operationalize,3
data-dependent,1
```
```bash
python3 salad_scout.py edgar --lexicon my-salad.txt ...
```

## Cron it (weekly stockpile)

`edgar --out output` writes a dated file (`output/salad-YYYY-MM-DD.txt`). Run it
weekly and you'll always have a backlog to pick from:

```cron
# Mondays 6am — fresh salad candidates for the week's issue
0 6 * * 1 cd /path/to/salad-scout && /usr/bin/python3 salad_scout.py edgar \
  --days 7 --max-docs 12 --top 20 --ua "Brady Gallagher brady@northdenoise.com" --out output
```

## Notes

- Be polite to SEC (the script already sleeps between fetches; keep `--max-docs`
  modest).
- This finds *candidates*; the judgment — which one's funniest, what it's hiding —
  is yours. That's the part readers pay for.
