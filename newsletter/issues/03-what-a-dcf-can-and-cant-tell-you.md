---
title: "What a DCF can and can't tell you"
issue: 4
access: flagship   # monthly fully-paid research report
date: TBD
---

# What a DCF can and can't tell you

*Monthly flagship — the long one.*

A discounted cash flow model is the most respected and most abused tool in
finance. Respected because it's the honest definition of value: a thing is worth
the cash it will produce, discounted for time and risk. Abused because — and I say
this with love — torture the assumptions long enough and a DCF will confess to
anything. This issue is a field guide to using it without fooling yourself, plus a
walk-through of the model from the [store](../../store.html).

*(Educational. Generic figures used for illustration — not a recommendation on any
security.)*

---

## Signal vs. Noise — "fair value is $X" *(free)*

> **The Noise:** "My DCF says fair value is $187. It's 30% undervalued."

A single point estimate from a DCF is false precision. The model's output is
*exquisitely* sensitive to two inputs you cannot know — the discount rate and the
terminal growth rate. Change each by one percentage point and your "$187" becomes
a range from $120 to $300.

> **The Signal:** a DCF gives you a **range and a set of required beliefs**, not a
> price tag. If someone shows you the point and hides the sensitivity, they don't
> understand their own model.

## The Number — the terminal value problem

In a typical 10-year DCF, **60–80% of the total value** sits in the *terminal
value* — the part after year 10 that you're guessing hardest about. Most of your
"answer" is the part you know least. Respect that.

---

## The Read — using a DCF honestly *(paid)*

### The three engines (and where each lies to you)

1. **Cash flows.** Forecasting 5–10 years of free cash flow. *The lie:* smooth,
   ever-rising lines. Real businesses are lumpy and cyclical. Build a base case
   you'd defend to a skeptic, not the one that justifies the price.
2. **Discount rate (WACC).** What return the cash must clear to be worth waiting
   for. *The lie:* a precise-looking number built on a guessed equity risk
   premium and a beta that changes with your data window. Treat it as a *range*.
3. **Terminal value.** Everything after the forecast. *The lie:* a terminal
   growth rate north of long-run GDP — which quietly assumes the company
   eventually becomes the economy. Keep it ≤ long-run nominal GDP.

### Walk-through with the store model

Using the [DCF model](../../store.html), here's the disciplined process:

- **Start with the sensitivity table, not the output.** The model's two-way table
  (WACC × terminal growth) is the real product. The single cell in the middle is
  the least interesting number on the page.
- **Triangulate terminal value two ways** — Gordon growth *and* an exit multiple.
  If they disagree wildly, your assumptions are inconsistent. The model flags it.
- **Reverse it.** Set the price to today's market price and solve for the implied
  growth/margin. Now you're not asking "what's it worth?" but "what does the
  market already believe, and do I believe more or less?" This is the single most
  useful way to run a DCF.
- **Stress the base case.** Knock 200bps off revenue growth and 100bps off
  terminal margin. If the thesis only works in the rosy case, you don't have a
  margin of safety — you have a hope.

### What a DCF is genuinely good for

- **Disciplining a story** into explicit, checkable assumptions.
- **Comparing your beliefs to the market's** (the reverse DCF).
- **Finding the breakpoints** — which assumption the whole thesis hangs on.

### What a DCF cannot do

- Tell you *when* value is realized (it's silent on timing and catalysts).
- Value businesses whose worth is mostly optionality or pre-cash-flow.
- Replace judgment. It's a structured way to *organize* judgment, not a substitute.

## Wall Street Word Salad of the Week *(paid)*

**This week's salad:** *"Our price target reflects a sum-of-the-parts valuation
that captures the embedded optionality of the platform at a justified premium
multiple."*

**Translation:** "We added up the pieces and then picked a big multiple to get the
number we wanted."

**What it's hiding:** "justified premium multiple" is the entire ballgame, stated
as if it were a fact instead of the single most sensitive assumption in the model
(see the terminal-value problem above). "Embedded optionality" is the analyst's way
of valuing things that don't produce cash yet — fine, but say so. A real number
shows its WACC and terminal growth; salad hides them behind adjectives.

## What I'd Watch

Pick one company you think you understand. Run a **reverse DCF**: what growth does
today's price imply? You'll often find the "cheap" stock is pricing heroic
assumptions, and the "expensive" one is pricing the obvious. That gap — between
the market's beliefs and yours — is where research actually lives.

*(Educational walk-through, not individualized investment advice or a
recommendation. Model outputs depend entirely on the assumptions you enter.)*

---

*North de Noise is for educational and informational purposes only and is not
individualized investment, legal, or tax advice, nor a recommendation to buy or
sell any security. Brady Gallagher is not currently a registered representative or
investment adviser. Past performance does not indicate or guarantee future
results. Investing carries risk, including loss of principal. Conflict disclosure:
this issue references the author's own DCF model sold via the site's store.*
