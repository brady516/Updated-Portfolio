# Narrative Monitor

A **research and signal-gating engine**, not a headline-to-order engine. It reads
a market narrative ("IBM down 23% overnight on soft guidance") and answers three
*separate* questions before anything is allowed near a trade:

1. **What is the narrative?** — the claim management or the tape is making.
2. **Has that narrative appeared in the reported financials?** — measured, not asserted.
3. **Is the evidence strong enough for an automated strategy to consume?** — a hard gate.

It writes machine-readable signals to JSONL so a separate trading process can pick
them up — and it refuses to mark anything executable until the numbers, not the
story, confirm deterioration.

**The full model is in [`THESIS.md`](THESIS.md).** In short: the signal is the
*divergence* between a confident, low-entropy narrative and the reporting
microstructure — not deterioration on its own. That framing is what makes it
look-ahead-free (both sides are contemporaneous), decay-resistant (the crowd *is*
the narrative), and completeness-native (obfuscation feeds the signal instead of
disqualifying the name).

Stdlib-only Python 3.11+ (no installs, no API keys). Run the demo:

```bash
cd narrative-monitor
python3 run_demo.py
python3 -m unittest discover -s tests -v
```

## The one design decision everything hangs on

**Do not let NLP determine direction. Use NLP only to identify the claim being made.**

```
Narrative:  "AI investment temporarily depressed results."
                     │  (narrative_monitor.py extracts the *claim*: ai_investment)
                     ▼
Financial test (signal_engine.py decides the *direction*):
  • Did capex intensity increase?
  • Did organic revenue slow?
  • Did FCF conversion decline?
  • Did gross margin weaken?
The engine then rules the claim: unsupported / partially visible / confirmed / contradicted.
```

A management explanation, an analyst's framing, or one seasonally-weak quarter can
**never** become a position on its own.

## The states

| State | Meaning |
|---|---|
| `narrative_only` | A story exists; the financials do not confirm it. |
| `early_evidence` | 1–2 comparable-period criteria confirm. Watch, don't trade. |
| `confirmed_deterioration` | ≥3 of 7 criteria confirm. The only executable state. |
| `improving` | The comparable-period evidence points the other way. |
| `inconclusive` | Nothing material triggered. |

## The score: divergence × narrative entropy (comparable-period, never sequential)

Every comparison is **year-over-year comparable-period** (Q4/Q4, Q3/Q3) or
**trailing-twelve-month** — because a Q4→Q1 free-cash-flow drop is *seasonality*,
not deterioration, and that seasonal trap is the single most common way a narrative
gets mistaken for a fact.

```
breakdown_score  =  D_report  ×  (0.5 + 0.5·benign_alignment)  ×  (0.5 + 0.5·(1 − H(N)))
```

**`D_report`** is the reporting divergence: seven microstructure channels, each
scored *continuously* to a [0,1] magnitude and combined by **noisy-OR** (weak
channels compound; a missing channel simply drops out — that is the completeness
behavior). The channels:

1. Trailing-twelve-month FCF declines.
2. FCF margin declines for two consecutive comparable periods.
3. Gross margin contracts (>100 bps floor, saturates at 300 bps).
4. Receivables grow faster than revenue (10 ppt floor).
5. Capex / capitalized development rises while organic revenue slows.
6. Full-year FCF guidance is reduced.
7. Previously delayed deals fail to appear in subsequent revenue.
   *(plus an 8th: disclosure withdrawal — segments dropped / non-GAAP proliferating
   / a line that was reported a year ago now blank — the H(R) obfuscation channel.)*

**`benign_alignment`** is how much the narrative *denies* weakness; **`H(N)`** is
the parrot layer's entropy. A benign, unanimous (low-`H(N)`) consensus contradicted
by the reporting is the breakdown — and low entropy also implies **slow
capitulation**, reported as `expected_decay`.

Invariant: `score ∝ D_report`, so with **zero reporting divergence the score is
zero** no matter how loud the narrative.

The IBM demo lands on **`early_evidence`**: reporting divergence is 0.47 (TTM FCF
fell; FCF margin fell YoY two quarters running), but the parrot layer isn't
unanimous — five sources echo management's benign frame and one analyst dissents
(`H(N)` = 0.65), so the score is **0.29** — below the 0.60 confirmed bar,
`execution_eligible: false`. Formally cutting full-year FCF guidance adds the
guidance channel and pushes it past 0.60 into `confirmed_deterioration` — `tests/`
proves that transition, and proves that a *unanimous* benign narrative over the same
reporting scores higher (and decays slower) than a split one.

## The parrot layer

`H(N)` is only meaningful over a *corpus*. `narrative_ingestor` assembles the whole
layer — the management frame plus every sell-side note and media piece that echoes
or dissents — and measures its propagation:

```
sources: 5 benign / 1 admit
originated by: ibm_earnings_call (management)
dominant frames: deal_timing, ai_investment
H(N) narrative entropy: 0.65   expected_decay: medium
first dissent (capitulation) after 6.3h
```

Entropy is **source-weighted**: each source contributes weight 1 split by its own
stance mix, so one analyst repeating a frame five ways can't masquerade as a
five-source consensus. `expected_decay` reads off `H(N)` — near-unanimous is `slow`
(the highest-conviction, longest-lived breakdown), a lone dissenter is `medium`, a
genuinely divided narrative is `fast`.

## The output the trading system consumes

`publish_signal` appends one JSON line per evaluation to `fundamental_signals.jsonl`:

```json
{
  "ticker": "IBM",
  "state": "early_evidence",
  "breakdown_score": 0.29,
  "divergence": 0.47,
  "narrative_entropy": 0.65,
  "reporting_entropy": 0.0,
  "expected_decay": "medium",
  "confidence": 0.92,
  "execution_eligible": false,
  "confirmed_criteria": ["ttm_fcf_decline", "fcf_margin_two_period_decline"],
  "reasons": ["TTM free cash flow fell to 11.70 from 12.60.", "..."]
}
```

Your order-management process must reject anything not explicitly eligible. The gate
re-checks every condition itself — it does not trust the `execution_eligible` flag
alone, so a malformed or hand-edited line can't slip a position through:

```python
def execution_gate(signal: dict) -> bool:
    return (
        signal.get("execution_eligible") is True
        and signal.get("state") == "confirmed_deterioration"
        and float(signal.get("confidence", 0)) >= 0.75
    )
```

## The four services

Each is a module in `narrative_monitor/`; the pipeline only ever passes the typed
models in `models.py` between them, so any stage can be swapped without touching the
others.

| Service | Job |
|---|---|
| `filing_ingestor.py` | Filings → normalized `FundamentalSnapshot`. Ships a CSV loader; subclass `FilingSource` per provider. |
| `edgar.py` | Live `FilingSource` over SEC EDGAR company-facts (XBRL) — ticker → CIK → as-filed, point-in-time snapshots. |
| `narrative_ingestor.py` | Raw feeds → the parrot layer of `NarrativeEvent`s (management / sell-side / media), plus propagation analytics. Ships a JSONL loader. |
| `narrative_monitor.py` | News / transcripts → structured `NarrativeClaim`s + source-weighted narrative entropy. Identifies the claim and its stance, never the direction. |
| `signal_engine.py` | The breakdown model — continuous channels, divergence, entropy weighting, state + gate. |
| `execution_adapter.py` | Paper/live broker interface behind hard limits. Dry-run by default. |
| `entropy.py` | Information-theoretic primitives (noisy-OR, Shannon entropy, ramps) — no domain knowledge, trivially testable. |
| `backtest.py` | Forward-calibration harness — walks the panel point-in-time and grades each signal against a realized forward return. |
| `channels.py` | Per-sector `ChannelSet`s (industrial / financial / reit) — the microstructure the truth is denominated in. Add a sector without touching the engine. |

**Point-in-time contract:** the engine trusts **as-filed data only**. A snapshot
marked `restated=True` can raise a state but can *never* be `execution_eligible` —
restated numbers are the one way the future leaks into a contemporaneous signal.

## Wiring it to real infrastructure

The provider adapters are the integration seam — write them around your own stack:

- **Filings / fundamentals:** `EdgarFilingSource` (built — SEC EDGAR company-facts,
  as-filed) is the reference implementation; Bloomberg or FactSet adapters are the
  same `FilingSource.fetch` seam for pre-normalized metrics.
- **Narrative:** point one or more `NarrativeSource` adapters at your transcript /
  news / sell-side feeds → `NarrativeEvent`s → `extract_claims`. The keyword
  `CLAIM_LEXICON` is deterministic but has **no negation handling** ("not deal
  timing" still matches `deal_timing`) — swap it for a model-backed extractor for
  production; the `NarrativeClaim` contract stays the same. Breadth of sources is
  what makes `H(N)` meaningful, so wire management, sell-side, and media distinctly.
- **Execution:** Interactive Brokers or another OMS behind `execution_adapter.consume`.
  It stays a dry run until you attach a broker with position sizing and hard limits —
  the correct default for a research engine.

## Every sector has microstructure — the truth is just denominated differently

There is no sector without a cash-vs-story axis; only industrials denominate it in
FCF and gross margin. Banks and REITs report *management estimates* — loan-loss
reserves, fair-value marks, straight-line rent, FFO adjustments — so the narrative
has **more** room to diverge from cash, not less. They are the richest hunting
ground, not an exception to gate off.

A **`ChannelSet`** (see `channels.py`) maps each sector onto the same seven-slot
structure. `SignalEngine` selects it by `snapshot.sector`; the divergence × entropy
math, the state machine, the gate, and the backtest are **identical** across
sectors.

| Generic slot | Industrial | Financial (bank) | REIT | Broker | Insurance |
|---|---|---|---|---|---|
| primary cash | free cash flow | net income | AFFO | net income | net income |
| cash decline | TTM FCF | reserve build < charge-offs | TTM AFFO | TTM net income | combined ratio ↑ ×2 |
| margin ×2 | FCF margin | NIM compression | same-store NOI | NII compression | loss ratio |
| quality wedge | gross margin | allowance coverage | FFO→AFFO wedge | NII share of pretax | accident-yr vs reported |
| accrual outrunning cash | receivables vs revenue | NPAs vs loans | straight-line rent vs NOI | float erosion (cash sorting) | premiums grow into rising losses |
| capitalization / carry | capex + rev slowing | coverage ↓ + charge-offs ↑ | cap. interest + NOI slowing | rate-cut earnings exposure | underwriting loss masked by investment income |
| guidance | FY FCF | NII | AFFO | NII | combined ratio (↑ = worse) |
| the tell | delayed deals | reserve releases that reverse | dividend > AFFO | rate carry dressed as franchise | reserve releases / adverse development |
| H(R) obfuscation | segments/non-GAAP | AFS→HTM / AOCI vs equity | stale cap-rate marks | non-GAAP proliferation | "adjusted" combined ratio |

```bash
python3 run_sector_demo.py   # a bank and a REIT: benign narrative, broken filing
```

```
Bank   (financial)  confirmed   channels: reserve_release_below_chargeoffs,
            allowance_coverage_decline, npa_outrun_loans, nim_two_period_compression …
REIT   (reit)       confirmed   channels: ttm_affo_decline, affo_wedge_widening,
            dividend_above_affo, same_store_noi_two_period_decline …
Broker (broker)     confirmed   channels: nii_reliance_high (NII = 168% of pretax),
            nii_two_period_compression, customer_float_erosion, rate_cut_earnings_exposure …
Insurer(insurance)  confirmed   channels: combined_ratio_two_period_rise,
            underwriting_loss_masked, accident_year_worse_than_reported, adverse_reserve_development …
Lender (lender)     confirmed   channels: origination_growth_into_rising_delinquency
            (+53% originations while delinquency rose), vintage_early_delinquency_rising,
            roll_rate_rising, reserve_release_below_chargeoffs …
SaaS   (saas)       confirmed   channels: revenue_up_billings_rolling_over
            (+19% revenue while billings -3%), net_revenue_retention_declining (to 98%),
            deferred_revenue_decline, crpo_growth_below_revenue …
Energy (energy)     confirmed   channels: reserve_replacement_falling (to 75%),
            outspending_cash_flow, netback_two_period_compression, negative_reserve_revisions …
BDC    (bdc)        confirmed   channels: pik_income_share_rising, nav_per_share_decline,
            dividend_above_nii, non_accrual_rate_rising …
```

The broker case started as a checking-account grievance: a "durable franchise"
narrative over a P&L where **net interest income is rising as a share of pretax** —
a rate carry on customer float taking over. The engine flags it not as fraud (the
number is disclosed) but as earnings that evaporate on the first cut. The lender and
SaaS cases are *conditional* inversions: fast loan growth is fine until the newest
vintages rot, and decelerating GAAP revenue is fine until billings/RPO/NRR roll over
underneath it.

Nine sectors ship today — industrial, financial, reit, broker, insurance, lender,
saas, energy, bdc. Several are *inverse, conditional* microstructures where growth
or a headline number moves opposite to the cash truth:

- **lender** — originations growth is celebrated, but growth **while the newest
  vintages deteriorate** is the breakdown. Growth alone never fires
  (`test_fast_growth_with_clean_credit_does_not_fire`).
- **saas** — GAAP revenue is *lagging* (recognized from backlog), so it keeps rising
  while **billings, cRPO, NRR, and deferred revenue** roll over underneath. Revenue
  up + billings down is the tell; billings *out*growing revenue never fires.
- **broker** — the P&L is a rate carry on customer float; the divergence is NII
  reliance **rising**, not merely being high (a known, priced level).
- **energy** — "reserves growing, production up" while **F&D cost rises, the reserve
  base shifts to undeveloped barrels, and the company outspends cash flow**; PV-10
  marked at a stale trailing SEC price hides it.
- **bdc** — "income growing, NAV stable" while income is increasingly **PIK
  (non-cash), non-accruals rise, and the dividend runs above what's earned** on a
  book the manager marks itself.

Adding another is a new `ChannelSet` and a registry entry — the engine never
changes. Snapshots carry sector line items in `line_items` (the CSV loader routes
any non-reserved numeric column there), so no schema churn per sector.

## Calibrating it without lying to yourself

The score is only worth trusting if it predicts *forward* returns out of sample.
`backtest.py` is the harness for that, and it enforces the three disciplines from
[`THESIS.md`](THESIS.md) §6 in code:

- **As-filed only** — a `restated=True` row, or one whose `reported_at` is after the
  evaluation date, is invisible at that date.
- **Score forward, don't fit backward** — `S_t` uses only `≤ t` data; the realized
  return over `[t, t+h]` grades it and is never fed back.
- **Stratify by `H(N)`** — the report puts the low- vs high-entropy forward returns
  side by side, so the thesis's own prediction (low-entropy breakdowns persist
  longer) can be *refuted*.

```bash
python3 run_backtest_demo.py   # SYNTHETIC data — validates the harness, not the thesis
```

```
By state:            n   mean_fwd   hit_rate
  confirmed_deterioration  8   -13.63%      100%
  early_evidence        8     0.00%        0%     <- high-entropy: fast decay, no edge
Deterioration by narrative entropy (thesis test):
  low           8   -13.63%                        <- unanimous benign consensus persists
  high          8     0.00%
Information coefficient (score vs -fwd return): +0.85
Execution-eligible mean forward return: -14.48%
```

The demo bakes a known effect into fabricated data so you can watch the harness
*recover* it — it validates the machinery and its point-in-time discipline. Real
validation needs real as-filed filings, a real parrot-layer feed, and real prices
(`CsvPriceSource` loads `ticker,date,close`). The harness is sector-aware — each
observation is scored through its own `ChannelSet` — so a broad-universe run reads
a bank on reserves and a REIT on AFFO, not on FCF.

### The whole system wired together

`run_multisector_backtest.py` runs **all nine sectors through one pipeline** — for
each, a benign low-entropy name (persistent decline), a split high-entropy name
(mean-reverts inside the horizon), and a healthy name (drifts up):

```
By state:                 n   mean_fwd   hit_rate
  confirmed_deterioration 40   -13.21%      100%
  early_evidence          60    -0.27%        8%
  inconclusive            73     0.02%        0%
Deterioration by narrative entropy:
  low                     47   -12.07%              <- unanimous benign consensus persists
  high                    40     0.00%              <- split narrative decays fast
Information coefficient:  +0.88
Execution-eligible mean forward return:  -14.21%
Confirmed: BDCLO, BROKLO, ENERLO, FINALO, INDULO, INSULO, LENDLO, REITLO, SAASLO
```

Every sector's low-entropy inversion confirms and prints a negative forward return;
the high-entropy versions decay to zero; the healthy names drift up — the thesis
reproduced across all nine microstructures through a single gated, calibrated
engine.

## Live data — SEC EDGAR

`edgar.py` is a real `FilingSource` over SEC's free, public XBRL company-facts API
(no key, just a declared User-Agent). It turns a ticker into as-filed,
point-in-time `FundamentalSnapshot`s:

```bash
EDGAR_EMAIL="you@example.com" python3 run_live_demo.py IBM AAPL NVDA
```

```python
from narrative_monitor import EdgarFilingSource, SignalEngine
snaps = EdgarFilingSource(email="you@example.com").fetch("IBM")   # ticker -> CIK -> facts
signal = SignalEngine().evaluate(snaps, claims=[])                # same engine, real numbers
```

Two disciplines are enforced in the normalizer, because both are ways live data
lies to you:

- **As-filed only.** company-facts returns every value ever filed for a period
  (original 10-Q/10-K *and* later amendments). For each period it keeps the
  **earliest-filed** value — the number that existed on the filing date — and uses
  that `filed` date as `reported_at`. Restatements are never used. This is the same
  point-in-time contract the backtest depends on, now enforced at ingestion.
- **Discrete quarters.** XBRL flow facts arrive as 3-month, 6/9-month YTD, and
  annual durations. The normalizer takes the discrete calendar-quarter facts (SEC
  `frame` `CY2023Q3`) and **derives Q4 = annual − (Q1+Q2+Q3)**, so comparable-period
  and TTM logic see clean quarters. `tests/test_edgar.py` verifies all of this
  offline against a recorded fixture of the real EDGAR schema.

The live adapter emits the **industrial** concept set (revenue, FCF, gross margin,
receivables) — the tags every filer reports. Sector-specific XBRL (bank
`AllowanceForLoanAndLeaseLosses`, REIT FFO, insurer reserves) is a follow-on
concept map; the normalization in `edgar.py` is the seam where it plugs in.

> Note: this adapter needs outbound HTTPS to `sec.gov`. Some sandboxes (including
> the one this was built in) block that egress at the proxy — `run_live_demo.py`
> reports it clearly. Run where SEC is reachable, or have an admin allowlist
> `data.sec.gov` and `www.sec.gov`.

### Scanning the whole universe

`run_universe_scan.py` runs every US filer (~10k+ tickers from SEC's map) through
the engine and ranks the biggest breakdowns:

```bash
python3 run_universe_scan.py --limit 100      # quick trial first
python3 run_universe_scan.py --cache .edgar   # full run (~30-60 min), cache raw facts
python3 run_universe_scan.py --rank-only      # re-rank an existing run
```

It is **paced** (under SEC's 10 req/s), **resumable** (skips tickers already in the
output file, so a re-run continues), and **Ctrl-C safe** (writes each hit as it
goes). Only actionable states are recorded; the run ends with a ranked table:

```
Top 25 breakdowns (of 214 deteriorating / 1,340 actionable):
ticker  state                    score  exec  latest   channels
ACME    confirmed_deterioration   0.82  True  2026-Q1  ttm_fcf_decline, gross_margin_contraction
...
```

**One honest caveat at scale:** the live adapter reads the *industrial* concept set,
so every name is scored on FCF/margins. A bank or REIT scanned this way is read on
the wrong microstructure — treat non-industrial confirmations as candidates to
verify, not signals, until the sector XBRL concept maps (bank reserves, REIT FFO,
…) are wired into `edgar.py`. That concept map is the next build.

## Not investment advice

This is research tooling. It produces *evidence states*, not recommendations, and it
is deliberately built to say "not yet" far more often than "go." Past performance
does not indicate future results; verify every input independently.
