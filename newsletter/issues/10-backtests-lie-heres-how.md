---
title: "Backtests lie — here's how"
issue: 10
access: split
date: TBD
---

# Backtests lie — here's how

Every strategy looks brilliant in the backtest. That's not because strategies are
brilliant; it's because backtests are easy to fool and even easier to fool *with*.
A curve that goes up and to the right is the single most overrated artifact in
finance. Here's how the lie gets made — so you can spot it in someone else's pitch,
and refuse to build it in your own.

## Signal vs. Noise — "this system returned 200% in the backtest" *(free)*

> **The Noise:** a gorgeous equity curve as proof. "Up 200%, Sharpe of 3, look at
> the chart."

A backtest is a hypothesis tested on data you already know the answer to. Of course
it worked — you tuned it until it did. The only test that counts is the one on data
the strategy has never seen.

> **The Signal:** assume a great backtest is overfit until proven otherwise. The
> burden of proof is on the curve, not on your skepticism.

## The Number — out-of-sample or it didn't happen *(free)*

Split your data: build on one period, test on a *separate, untouched* period. If the
magic only exists in the data you optimized on, it was never a strategy — it was a
very expensive way to describe the past.

## Wall Street Word Salad of the Week *(paid)*

**This week's salad:** *"Our proprietary, AI-driven model has been rigorously
backtested to deliver consistent, market-beating risk-adjusted returns."*

**Translation:** "We fit a curve to old data and the chart looks amazing."

**What it's hiding:** "rigorously backtested" is doing the heavy lifting and meaning
nothing — backtesting is where overfitting *lives.* "Proprietary" means "we won't
show you," and "AI-driven" in 2026 is the new "quantitative." Ask for out-of-sample
and live results, then watch the confidence evaporate.

## The Read — the four ways a backtest flatters you *(paid)*

1. **Look-ahead bias.** Using information the strategy couldn't have had at the time
   (restated earnings, end-of-day data acted on at the open). Quiet, deadly, common.
2. **Survivorship bias.** Testing only on companies that *still exist* — silently
   deleting the bankruptcies. Your universe should include the dead.
3. **Overfitting.** Enough parameters and you can backtest a strategy that buys on
   days the CEO wore blue. More knobs = more flattery, less signal.
4. **Ignoring costs.** Commissions, spreads, slippage, taxes, market impact. A
   strategy that trades constantly can be a genius gross and a loser net.

The honest workflow — out-of-sample testing, realistic costs, walk-forward
validation, and a healthy assumption that you fooled yourself — is exactly what the
[course](../../course.html) drills. Not because it's fun, but because it's the
difference between a system and a screenshot.

## What I'd Watch

Next time someone shows you a backtest, ask three questions: *Out-of-sample? Net of
costs? Any live track record?* If the answer to all three is a subject change,
you've found the noise.

*(Educational, not individualized investment advice. Algorithmic trading involves
substantial risk.)*

---

*North de Noise is for educational and informational purposes only and is not
individualized investment, legal, or tax advice, nor a recommendation to buy or
sell any security or strategy. Algorithmic trading involves substantial risk,
including the rapid loss of capital. Backtested results are hypothetical, have
inherent limitations, and do not indicate or guarantee future performance. Brady
Gallagher is not currently a registered representative or investment adviser.
Conflict disclosure: this issue references the author's own course sold via the site.*
