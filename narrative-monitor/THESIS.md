# Narrative Breakdown as Market Microstructure

*Design thesis for the Narrative Monitor engine.*

## 1. The premise

Markets do not price filings. They price **narratives about filings**, and those
narratives are manufactured and propagated by a small, tightly-coupled population:
management sets a frame on the call, the sell-side repeats it, the media amplifies
it. Call it the parrot layer. Most of the time the parrots are approximately right
and the narrative and the reporting agree.

The edge is in the moments they **diverge** — when the reported microstructure of a
company's own filing contradicts the frame everyone is still repeating. That gap,
and specifically the interval before the parrots capitulate, is the tradeable
object. This is not an earnings-surprise engine. It is a **narrative-breakdown
detector**: it measures the distance between what is being said and what was
reported, weighted by how confidently and uniformly it is being said.

## 2. The object is the divergence, not the deterioration

"FCF fell 11%" is not a signal — the tape saw the same statement you did.
Deterioration is only one *channel* through which a narrative breaks. The signal is:

> **A confident, low-entropy consensus asserting one thing while the reporting
> microstructure shows another.**

Define, at the moment *t* of a filing/narrative event:

| Symbol | Meaning |
|---|---|
| **N_t** | the narrative distribution — the frames from management + sell-side + media, and how concentrated they are |
| **R_t** | the reporting microstructure — the as-filed financial evidence |
| **D(N_t, R_t)** | divergence — how far the reporting is from what the narrative implies (signed) |
| **H(N_t)** | narrative entropy — low = everyone parroting the same frame |
| **H(R_t)** | reporting entropy — high = the filing itself is obfuscated / withholding |

The breakdown signal:

```
S_t  ∝  D(N_t, R_t)  ×  benign_alignment(N_t)  ×  (1 − H(N_t))
```

Biggest when the reporting strongly contradicts the frame **and** the frame is a
tight, benign, low-entropy consensus — many parrots, all aligned, all on the wrong
side. Crucially, `S_t ∝ D`: **if the reporting does not diverge, the score is zero
no matter how loud the narrative.** A headline can never create a signal on its own.
That invariant is load-bearing.

## 3. Why this dissolves the three failure modes — by construction

These are the failure modes that kill fundamental-signal systems. The divergence /
entropy framing does not *mitigate* them; it makes most of them structurally
inapplicable.

### Look-ahead bias → gone, because the signal is contemporaneous
N_t and R_t are **both dated to the same instant** — the filing and the narrative
around it are timestamped at emission. The signal is a relationship between two
things known *now*, not a comparison of today's data to a restated-later truth. A
forward-return prediction needs the future to score itself; a divergence does not.
The only remaining leak is using **restated** financials, so the contract is
absolute: **as-filed values only, keyed to `reported_at`.** Restated numbers are the
one way the future gets in, and they are banned.

### Alpha decay → parameterized, not feared
A 10-Q screen decays because everyone runs it and arbitrages it out. Here the crowd
*is* the narrative — the parrots are the counterparty holding the wrong side.
Crowding normally destroys an edge; in this framing the crowding is what **creates
and sustains** it. And the persistence is legible: decay half-life scales with
narrative stickiness ≈ `(1 − H(N_t))`. A tight, unanimous consensus takes longer to
capitulate, so the low-entropy setups are both the highest-conviction *and* the
slowest-decaying. **You forecast your own decay from the entropy** and size/hold
against it instead of being surprised by it.

### Data completeness → a channel, not a gate
Incompleteness is `H(R_t)`. A company that drops a segment, reclassifies a line
item, or floods the release with fresh non-GAAP metrics is **raising the entropy of
its own disclosure** — and doing so while the narrative stays confident is itself
divergence. Obfuscation is a tell. So missing/withheld data *increases* the signal
for that name rather than disqualifying it. Completeness stops being a bias against
sparse filers and becomes an axis of the microstructure you are reading. (It does,
correctly, *lower confidence* even as it raises divergence — that tension is real
and is kept explicit, not averaged away.)

## 4. Where the alpha actually lives

The initial gap is not the trade. When IBM prints and drops 23% intraday, that
repricing is gone — the tape was not fooled on the number. The edge is in the two
tails around the gap:

1. **Pre-gap** — names where divergence is building but the parrots have not
   capitulated and price has not moved. Hardest, highest value.
2. **Post-gap narrative repair** — "pipeline remains strong" is the parrots trying
   to re-close the gap. When the reporting microstructure says the repair is
   unsupported, the slow capitulation of that consensus is the persistence you hold.

The engine's job is to rank the universe by breakdown score continuously, so both
tails surface as states rather than as a single event alert.

## 5. What "microstructure within the reporting" means — the channels

Divergence and entropy are measured through observable channels:

- **Accrual vs cash divergence** — income-statement framing against cash-flow
  reality (the FCF / margin / conversion criteria).
- **Disclosure-granularity delta** — segment and line-item count shrinking, footnote
  hedging rising, new non-GAAP metrics appearing exactly when the narrative needs
  them. This is the primary `H(R_t)` signal.
- **The non-GAAP wedge** — the gap between the metric the narrative leans on and
  GAAP.
- **Guidance language vs guidance number** — a "soft guidance" *tone* with no formal
  cut is divergence in the language before the number (the IBM `early_evidence`
  case).
- **Parrot propagation** — the transfer of a specific phrase management → sell-side →
  media, and the **time-to-capitulation**. This is `H(N_t)` measured over the parrot
  corpus, and it is what makes the decay forecastable.

## 6. Validating it without lying to yourself

Because the score is contemporaneous, honest validation is possible but demands
discipline:

- **As-filed snapshots only.** Reconstruct each quarter from the filing that existed
  on `reported_at`, never from a later restatement.
- **Score forward, don't fit backward.** `S_t` uses only `≤ t` information; realized
  returns over `[t, t+h]` grade it. Never let the outcome touch the score.
- **Stratify by `H(N_t)`.** The thesis makes a falsifiable prediction: low-entropy
  benign consensus + high divergence should show *longer* return persistence than
  high-entropy setups. If it doesn't, the entropy weighting is decoration and should
  be cut.
- **Sector-gate the channels.** Financials/REITs have no comparable FCF/gross-margin
  microstructure; those channels are skipped, not forced.

## 7. Why this is orthogonal to VIX (the lesson from the last variation)

The earlier microstructure variation competed with VIX and lost, because it was
trying to out-predict a **market-implied consensus instrument on its own turf** —
you cannot beat implied volatility with a slower measure of the same thing. This
angle does not predict the consensus; it measures the consensus's **error**
directly. It is orthogonal to VIX by construction: VIX is the price of the crowd's
fear, this is the distance between the crowd's story and the company's own numbers.
That orthogonality is the whole reason it is a better read on microstructure —
it sidesteps the competition rather than re-entering it.

## 8. What stays deliberately out

- **No direction from NLP.** Language identifies the *claim and its stance* only; the
  reporting decides the sign. Preserved from the base design.
- **No signal without reporting divergence.** `S_t ∝ D`. Non-negotiable.
- **No restated data.** Ever.
- **No execution on `S` alone.** The hard gate (confirmed state + confidence +
  point-in-time completeness) stands between a score and an order.

---

The formalization of this thesis — continuous divergence via noisy-OR over the
channels, Shannon narrative entropy over the parrot stances, reporting entropy from
disclosure microstructure, and an as-filed point-in-time contract — is implemented
in `narrative_monitor/entropy.py` and `narrative_monitor/signal_engine.py`. The
forward-calibration harness that grades it point-in-time and stratifies by `H(N)`
(§6) is in `narrative_monitor/backtest.py`; `run_backtest_demo.py` runs it on a
synthetic panel with a known effect baked in, to prove the machinery recovers what
is there.
