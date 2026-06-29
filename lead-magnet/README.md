# Lead magnet — North de Noise Valuation Lab (a Claude skill)

The free incentive that grows North de Noise's email list: a **Claude skill** that
values any stock with a licensed analyst's framework — a two-stage **DCF** (with
reverse-DCF) and a **DDM** — using a *hybrid* flow (fetch the inputs, let the user
confirm/override, then compute). It's educational, outputs ranges not verdicts, and
ends every analysis by pointing to the store models and the paid newsletter.

```
valuation-lab/
├── SKILL.md                    # the skill: workflow + guardrails
├── scripts/valuation.py        # deterministic DCF / DDM / reverse-DCF math (stdlib only)
└── references/methodology.md    # the "why" behind every input
```

## Why a skill (not a PDF)

- It demonstrates expertise by *doing*, and people keep using it.
- It self-selects your buyer: people comfortable installing a Claude skill are
  exactly the tool-forward audience most likely to pay $49/mo.
- It funnels: the free Lab is a taste; the **store** DCF/Monte-Carlo/dividend
  models are the paid upgrade, and **North de Noise** is the recurring research.

## How to distribute it as a lead magnet (email-gated)

The skill is the reward for joining the free list:

1. **Zip the skill folder** (`valuation-lab/`).
2. In Substack (or Beehiiv), set up the **free signup** so new subscribers receive
   a welcome email containing the download link (host the zip on the site, a
   Dropbox/Drive link, or a GitHub release).
3. On `insights.html`, the free tier's CTA promises the Valuation Lab on signup —
   keep that promise in the welcome email.
4. Optional upsell ("Both" strategy): publish a basic version openly for reach and
   keep an extended version (more models / the deeper guide) behind the signup.

> Compliance note: the skill is educational and never gives advice — keep it that
> way in any marketing copy. Don't imply you're a current registered adviser.

## How a recipient installs it (include this in your welcome email)

**Claude Code:** unzip into your skills directory, e.g.
`~/.claude/skills/valuation-lab/` (or a project's `.claude/skills/`).
Then ask: *"value AAPL with the Valuation Lab"* or *"what does NVDA's price imply?"*

**Claude.ai / Claude Desktop:** add it as a custom skill where skills are supported,
then invoke it the same way.

The skill calls `scripts/valuation.py` (Python 3, no dependencies) for the math, so
the numbers are reproducible and auditable rather than guessed.

## Test it yourself

```bash
python3 valuation-lab/scripts/valuation.py --model all --json '{
  "ticker":"DEMO","fcf0":1000,"high_growth":0.10,"years":10,
  "terminal_growth":0.025,"wacc":0.09,"shares":500,"net_debt":200,"current_price":45,
  "dividend0":2.0,"required_return":0.09
}'
```
