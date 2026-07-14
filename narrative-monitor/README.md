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

## Confirmation: at least three of seven (comparable-period, never sequential)

Every comparison is **year-over-year comparable-period** (Q4/Q4, Q3/Q3) or
**trailing-twelve-month** — because a Q4→Q1 free-cash-flow drop is *seasonality*,
not deterioration, and that seasonal trap is the single most common way a narrative
gets mistaken for a fact.

`confirmed_deterioration` requires **at least three** of:

1. Trailing-twelve-month FCF declines.
2. FCF margin declines for two consecutive comparable periods.
3. Gross margin contracts by more than 100 bps.
4. Receivables grow at least 10 percentage points faster than revenue.
5. Capex / capitalized development rises while organic revenue slows.
6. Full-year FCF guidance is reduced.
7. Previously delayed deals fail to appear in subsequent revenue.

The IBM demo lands on **`early_evidence`**: the narrative is loud (soft guidance, AI
infrastructure, deal timing, budget reallocation — six claims, intensity 1.0), but
only **two** criteria confirm (TTM FCF fell; FCF margin fell YoY two quarters
running). So `execution_eligible` is **false**. Formally cutting full-year FCF
guidance would add the third criterion and flip it to `confirmed_deterioration` —
`tests/` proves exactly that transition.

## The output the trading system consumes

`publish_signal` appends one JSON line per evaluation to `fundamental_signals.jsonl`:

```json
{
  "ticker": "IBM",
  "state": "early_evidence",
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
| `filing_ingestor.py` | SEC/company filings → normalized `FundamentalSnapshot`. Ships a CSV loader; subclass `FilingSource` per provider. |
| `narrative_monitor.py` | News / transcripts → structured `NarrativeClaim`s. Identifies the claim, never the direction. |
| `signal_engine.py` | Evidence scoring and state transitions — the 7 criteria and the gate. |
| `execution_adapter.py` | Paper/live broker interface behind hard limits. Dry-run by default. |

## Wiring it to real infrastructure

The provider adapters are the integration seam — write them around your own stack:

- **Filings / fundamentals:** SEC EDGAR company-facts for raw filings; Bloomberg or
  FactSet for pre-normalized metrics. Implement `FilingSource.fetch`.
- **Narrative:** news and transcript feeds → `NarrativeEvent`s → `extract_claims`.
  Swap the keyword `CLAIM_LEXICON` for a model-backed extractor; the
  `NarrativeClaim` output contract stays the same.
- **Execution:** Interactive Brokers or another OMS behind `execution_adapter.consume`.
  It stays a dry run until you attach a broker with position sizing and hard limits —
  the correct default for a research engine.

## Not investment advice

This is research tooling. It produces *evidence states*, not recommendations, and it
is deliberately built to say "not yet" far more often than "go." Past performance
does not indicate future results; verify every input independently.
