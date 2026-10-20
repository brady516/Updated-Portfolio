---
title: "I Spent Two Years Trying to Beat the VIX. The VIX Didn't Notice."
issue: special-01
access: free   # whole issue free and unpaywalled; it's the trust piece and the referral magnet
date: TBD      # release alongside the WONDEROUS INSANITY episode on the same story
---

# I Spent Two Years Trying to Beat the VIX. The VIX Didn't Notice.

*A special issue. Free, unpaywalled, and about the one call I've graded hardest: my own.*

## Intro

Every week this newsletter grades somebody else's call against what actually happened. That's the deal. It only works if the scorecard has no exemptions, so this issue grades the author.

For about two years I built an instrument I called the Entropy Gauge. The thesis was simple and, I was sure, important: disorder in the market can be measured, and a good enough measure of it would flag risk before Wall Street's favorite fear index did.

I pre-registered the test. I wrote down the rules, the metrics, and the bar before I ran a single number, specifically so I couldn't talk my way around the answer afterward.

The VIX won. At every horizon I tested. I retired the gauge the same day.

This is the autopsy, including the part where I was briefly a genius.

## Signal vs. Noise

> **The Noise:** "Our proprietary model, calibrated on two centuries of market history, flags risk months before the VIX."

That isn't a quote from a hedge fund pitch deck. It's a fair paraphrase of me, in the spring of this year.

I want to be precise about what made it noise, because it wasn't the ambition and it wasn't the math. It was the order of operations. I wrote the claim before I had run the test that could kill it. I'd fit an instrument to 200-plus years of data, admired how well it described the past, and let that admiration stand in for evidence about the future.

That's the most common sentence in finance wearing a lab coat. Every strategy looks brilliant on the data it was built on. A model trained on two centuries of history has two centuries of opportunities to memorize what already happened, and memorizing is not the same as knowing.

> **The Signal:** a claim about the future is worth exactly as much as the test it survived. If it hasn't been tested on data it never saw, against the toughest available benchmark, under rules written in advance, it's a story. Mine was a story.

## The Number

**0.955.**

That's the p-value from the final, clean test at one of my three forecasting horizons. The other two came back at 0.690 and 0.647.

In plain English: the test asked whether adding my gauge to a standard volatility forecast made the forecast measurably better. A p-value that close to 1 means the forecasts with and without my gauge were statistically indistinguishable. Two years of work, and the cleanest number I produced says the model added nothing you could detect.

What would change its meaning: a failed test is limited by its data. "No evidence it helps" is not the same as "proven useless at everything." That's true, and I'll come back to why it's also the most dangerous sentence a failed model's owner can say.

*Results from my own pre-registered backtests, 2026. Historical and hypothetical; not a forecast and not a trading record.*

## The build

The idea arrived years earlier, at a wirehouse desk, as a hunch: markets get disorderly before they get dangerous, and disorder is measurable. Physicists have a word for it. I borrowed the word.

The hunch sat for a while. Then the tools showed up, and I poured all of them at it.

The gauge I eventually built scraped Reddit for sentiment and ran it through a language model trained on financial text. It pulled macro data from the Federal Reserve's public database. It fed an ensemble of machine-learning models every scrap of market history I could reasonably afford, including a free S&P 500 dataset that reaches back to the early 1800s. Out came a reading, a regime label, and a comparison against the VIX, updated live.

I also wrote a book arguing the thesis. I was not, it's fair to say, hedging.

## The win

Then came the afternoon that nearly ruined me, in the slow and pleasant way.

The market was on a hollow rally: up big, on no news I could find. The gauge ticked up with it, reading disorder underneath the green. I sold an index put, betting on how the next day would go, and closed it the next morning for a 6.8% gain.

I'd cracked it. I'd seen what nobody else saw.

[Brady: one or two sentences here, in your words, on what that evening actually felt like. I'm not going to fake it for you.]

*A single historical trade, held overnight. One trade is not a track record, and selling puts carries real risk: if the market had fallen hard instead, the loss could have been many times the gain.*

Hold that thought. We'll come back for it.

## The first test passed

Here's the part that should have worried me more than it did.

An early round of testing came back four for six. On the surface, the gauge beat the VIX at predicting forward volatility at all three horizons I checked, plus a 21-day drawdown measure. It missed on two shorter drawdown windows. Four out of six against the most famous risk gauge in finance felt like vindication.

It was an in-sample result. The gauge was being graded on data that looked a lot like the data it was built on, using a scoring method that almost always flatters a model when you add one more input. Adding a variable to a regression and watching the fit improve is not discovery. It's arithmetic.

So I did the thing I'd been telling readers to do. I wrote the harder test down first.

## The second test failed, everywhere

The pre-registration locked in four things before I saw a result:

1. **The baseline.** Not the VIX alone, which would have been a strawman, but the VIX plus a standard model built from recent realized volatility. If the gauge was useful, it had to add something the market's own recent behavior didn't already tell you.
2. **The scoring rule.** A loss function built for volatility forecasts, so big misses during calm stretches couldn't hide behind small misses during chaos.
3. **The statistical test.** One designed to compare forecasts out of sample, on data the model hadn't been tuned on.
4. **The verdict rules.** What counts as a pass, what counts as a fail, and a promise that secondary results couldn't rescue a failed primary one.

Then I ran it, and the scorecard looked like this:

| Test | What it asked | Result |
|---|---|---|
| Forecast improvement, three horizons | Does adding the gauge beat the baseline out of sample? | p = 0.690, 0.647, 0.955. No detectable improvement at any horizon. |
| Explained variance | How much more of future volatility does the gauge explain? | 0.001 or less, at every horizon. A rounding error. |
| Signal-to-noise vs. the baseline | Single-asset and five-asset versions | −0.10 and −0.06. Slightly worse than not using it. |
| Stress detection, 1 month | How well does it separate stress from calm? | 0.742, behind the VIX. Gap not statistically significant on a small event count. |
| Stress detection, 3 and 6 months | Same question, longer horizons | 0.557 and 0.538, barely better than a coin flip. The VIX was significantly better. |

*Scores from my own pre-registered backtests. Stress-detection figures are AUC: 0.5 is a coin flip, 1.0 is perfect. All results historical and hypothetical.*

Read across the rows and they tell one story. The gauge never beat the market's own number. Not on the near horizons, where the VIX is supposed to be strong, and not on the long ones, where the VIX is supposed to fade. The ranking never flipped.

And that 6.8%? The rally had no justification. It reversed when the sellers showed up. I was never right about the market. I was on the right side of one trade, for one night, for reasons that had nothing to do with the instrument I credited.

## Why the VIX wins

The VIX looks like a statistic. It isn't one.

It's derived from what people are actually paying for S&P 500 options right now: a 30-day, forward-looking estimate of volatility, set by traders putting real money behind their view of risk. Some of the best-funded, best-informed participants in finance are in that market every day. If anything they know changes their view, it shows up in what they're willing to pay, quickly.

My gauge was computing disorder from public data: prices, posts, macro series. Every one of those traders had already seen that data, acted on it, and priced it in before my model finished reading it.

I wasn't measuring the information. I was measuring the wake it left after the informed money had already gone by.

That's the real lesson, and it's bigger than my model. When you try to out-forecast a market price, you're not competing against a number. You're competing against everyone whose money set it. I picked the single most efficient risk arena in public markets to prove I was smarter than it, and it didn't notice I'd entered.

## The trapdoor I didn't take

Remember "no evidence it helps isn't proof it's useless"? Here's why that sentence is dangerous.

It's true, and it's also exactly how failed models survive. The gauge failed at forecasting volatility, so you say it was really built to detect crashes. It fails at that, so it was really a regime classifier. Then a fragility indicator. Each new job is untested, so each one keeps the dream alive a little longer, and the model never has to die.

I know because I took the first step through that door. After an earlier negative result I argued, reasonably, that the gauge was built for slow, rare crises and had been tested on the wrong clock. That reframe was honest, and I pre-registered the harder version anyway. When that failed too, the only honest move left was to stop moving the goalposts.

A negative result is only worth something if you don't relocate it. So I didn't. Retired, same day.

## The parts bin

Two years didn't evaporate. They got disassembled.

- **The trading layer came out.** The gauge doesn't get a vote on any position. It isn't a quiet input somewhere either. It's off.
- **The governance went to work.** The pre-registration discipline (rules written first, a version ledger so I can't quietly swap methods, a requirement to publish failures alongside wins) didn't need the gauge to be right. It now runs inside an operating system I'm building for small businesses, where "write the rule before you see the result" turns out to be extremely useful for things far less glamorous than beating the VIX.
- **The question survived.** Entropy was the terrain. What actually decided the contest was who knew what, and when. That's a better question than the one I started with, and you'll be hearing more about it.

The most expensive research I've ever done produced one finding and one habit. The finding is that the market's own price is a brutally hard benchmark. The habit is that I now write down how I'll know I'm wrong before I let myself believe I'm right.

## What to ask anyone showing you a backtest

You'll see a lot of beautiful charts this year. Before you're impressed by any of them, including mine, ask:

1. **Was the test written down before the results came in?** If the rules arrived after the chart, the chart is a sales tool.
2. **What was the baseline?** Beating "doing nothing" is easy. Beating the market's own pricing of risk is the test that matters.
3. **Is this in-sample or out-of-sample?** If the model was graded on data it was built from, you're looking at a description of the past.
4. **What happened to the versions that failed?** Every shop has a drawer of dead models. Ask to see it. The answer tells you how the surviving ones were chosen.
5. **What would prove it wrong?** If nobody can answer, nobody has tried.

I'd add a sixth, for anyone who's ever built something they loved: **would you publish the result if it went the other way?**

I did. This is it.

---

**Disclosures**

*North de Noise is published for educational and informational purposes only. It is not individualized investment, tax, or legal advice, and nothing in it is a recommendation or solicitation to buy or sell any security.*

*The author, Brady Gallagher, MBA, is a former financial advisor (FINRA CRD 6510444, verifiable on BrokerCheck). He is not currently registered with any broker-dealer or investment adviser and does not act as an advisor to any reader. Reading or subscribing creates no client relationship.*

*Past performance is historical and does not guarantee future results. All investing involves risk, including the loss of principal. Opinions are the author's own as of the publication date and may change without notice. Data comes from sources believed reliable, but its accuracy is not guaranteed.*

*The author may hold positions in securities discussed and will disclose any such position inline where relevant. Consider your own circumstances, and consult a qualified professional before making any financial decision.*

**The only thing we'll guarantee: someone, somewhere, will say "this time is different."**
