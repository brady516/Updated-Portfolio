# Valuation methodology — the "why" behind each input

A reference for the Valuation Lab skill. The goal is to *think clearly about
value*, not to produce a number to act on. Everything here is educational.

## What "intrinsic value" means

A company is worth the cash it will produce for owners over its life, discounted
for time and risk. Both models here are just disciplined ways to estimate that —
and to make your assumptions explicit so you can argue about them.

## The DCF (discounted cash flow)

**Free cash flow (`fcf0`).** Cash left after the business funds its operations and
capital needs — the cash actually available to investors. Use a *normalized* base
(a representative year), not a one-off spike or trough.

**High-growth rate & years (`high_growth`, `years`).** Your explicit forecast
period. Be a skeptic: smooth ever-rising lines are the most common lie in a DCF.
5–10 years is typical.

**Terminal growth (`terminal_growth`).** Growth forever after the forecast. Keep
it **at or below long-run nominal GDP (~2.5–3%)** — a higher number quietly assumes
the company eventually becomes the entire economy.

**Discount rate / WACC (`wacc`).** The return the cash must clear to be worth
waiting for, reflecting risk. It's an estimate, not a fact — treat it as a *range*.
Higher risk → higher WACC → lower value.

**Net debt (`net_debt`).** Total debt minus cash. The model values the whole
enterprise (EV), then subtracts net debt to get equity value for shareholders.
Negative if the company holds more cash than debt.

**The terminal-value problem.** In a 10-year DCF, 60–80% of total value usually
sits in the terminal value — the part you're guessing hardest about. Respect that;
it's why the sensitivity table matters more than the point estimate.

## Reverse DCF — the most useful move

Instead of asking "what's it worth?", set the value to today's market price and
solve for the growth the market is *already pricing in*. Now the question becomes:
**do I believe more or less than the market?** This reframes valuation from
prediction to a comparison of beliefs — far harder to fool yourself with.

## The DDM (dividend discount model)

Only valid for **stable, reliable dividend payers**. Values a stock as the present
value of its future dividends.

**Current dividend (`dividend0`).** Annual dividend per share.

**High growth, years, terminal growth.** Same logic as the DCF, applied to
dividends. Terminal dividend growth must stay below the required return or the math
breaks (and reality would too).

**Required return (`required_return`).** What you need to earn to hold the risk —
your discount rate for the dividends.

**Two-stage vs. Gordon.** The single-stage Gordon model assumes one growth rate
forever; the two-stage version allows a near-term growth phase then a terminal
rate. The Lab shows both so you can see how sensitive the answer is to that choice.

## Common mistakes the Lab guards against

- Treating the point estimate as truth (always read the range).
- Terminal growth ≥ GDP (silently assumes world domination).
- A WACC that's really just "the number that makes my thesis work."
- Forgetting dilution / using the wrong share count.
- Auto-trusting fetched data without confirming it.

## The honest limits

A DCF/DDM cannot tell you *when* value is realized, cannot value businesses whose
worth is mostly optionality, and cannot replace judgment. It organizes judgment;
it does not substitute for it. And none of this is individualized advice.
