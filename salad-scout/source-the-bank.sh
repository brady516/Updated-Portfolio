#!/usr/bin/env bash
# Source real, attributable Word Salad for each North de Noise theme.
# Run locally (or on the NAS) — SEC EDGAR blocks sandbox proxies, not your machine.
#
#   1. Set UA below to your real name + email (SEC requires it).
#   2. Run the whole thing:        bash source-the-bank.sh
#      ...or copy a single block you want.
#   3. Results land in ./output/ (dated .txt). Pick a sentence, paste it VERBATIM
#      into the issue with attribution (company, form, date) + link. Never invent one.
#
# EDGAR full-text search covers FILINGS (10-K/10-Q MD&A, 8-K press releases, fund
# prospectuses/letters). Earnings-call transcripts and Fed statements aren't on
# EDGAR — see the `url`/`score` notes at the bottom for those themes.

set -euo pipefail
UA="Brady Gallagher brady@northdenoise.com"   # <-- EDIT THIS
PY="python3 salad_scout.py"
COMMON="--days 90 --max-docs 12 --per-doc 4 --top 15 --ua \"$UA\" --out output"

run () { echo; echo "### $1"; shift; eval "$PY edgar $* $COMMON"; }

# 02 — pitch-speak (growth/momentum filings)
run "02 pitch-speak"        --forms 10-K,10-Q --terms 'optionality,asymmetric,inflection,long runway'

# 03 — concentration-as-strategy (fund shareholder letters)
run "03 concentration"      --forms N-CSR     --terms 'high-conviction,concentrated,our edge'

# 04 — valuation hand-waving (MD&A / segment notes)
run "04 valuation"          --forms 10-K,10-Q --terms 'sum-of-the-parts,premium multiple,embedded optionality'

# 05 — bad-quarter spin (earnings press releases) — GOLD MINE
run "05 bad-quarter spin"   --forms 8-K       --terms 'non-recurring,unfavorable timing,headwinds,operational discipline'

# 06 — the pre-cut dividend (press releases / 10-K) — add --entity "<high-yielder>" to target one
run "06 dividend"           --forms 8-K,10-K  --terms 'committed to returning capital,sustainable dividend,well-covered'

# 07 — covered-call dressing (fund prospectuses / fact sheets)
run "07 covered call"       --forms 497,485BPOS --terms 'income overlay,monetize volatility,covered call,enhanced income'

# 08 — panic in a suit (fund manager commentary letters)
run "08 panic"              --forms N-CSR     --terms 'tactically,constructive,risk-off,nimble'

# 09 — fake diversification (fund prospectuses)
run "09 diversification"    --forms 497,485BPOS --terms 'multi-asset,broad opportunity set,diversified solution'

# 10 — overfit-as-genius (quant/AI fund docs + asset-manager 10-Ks)
run "10 backtests/AI"       --forms 497,10-K  --terms 'proprietary,AI-driven,rigorously backtested,risk-adjusted'

# 12 — process theater (fund letters / prospectuses)
run "12 process theater"    --forms N-CSR,497 --terms 'disciplined process,repeatable,robust framework'

cat <<'NOTE'

### 11 — rates / Fed hedging  (NOT on EDGAR — public-domain, easiest win)
Grab the latest FOMC statement straight from the source:

  python3 salad_scout.py url \
    "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm" \
    --ua "Brady Gallagher brady@northdenoise.com" --top 8

(Swap the URL for the newest statement. Fed text is public domain — quote freely,
 just cite the date.)

### Earnings-call transcripts (great for 02/03/06 named quotes)
EDGAR doesn't host transcripts. Save one as a .txt and score it:

  python3 salad_scout.py score --input acme-q3-call.txt --top 10

Then attribute: "— Company, Qn FYxx earnings call, <date>."
NOTE
