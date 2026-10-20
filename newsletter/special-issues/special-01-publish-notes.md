# Special 01: publish notes

Companion to `special-01-i-spent-two-years-trying-to-beat-the-vix.md`.

## Placement

- Not issue 1. Run it after two or three pundit scorecards so readers have seen the grading before they see the author graded.
- Tease it in the welcome email / issue 1: *"I'll grade my own calls too. One of them was a two-year model that lost to the VIX at every horizon. That story's coming."*
- Release it the same week as the WONDEROUS INSANITY episode on the same story. Free and unpaywalled: it's the trust piece and the most shareable thing in the backlog.

## Subject lines

1. I spent two years trying to beat the VIX. The VIX didn't notice.
2. Grading my own homework: F
3. The model I killed the same day it failed

## Social cut-downs

**1.**
I spent two years building a model to beat the VIX. I pre-registered the test so I couldn't wriggle out of the answer.
The VIX won at every horizon. I retired the model the same day.
The full autopsy, including the night I thought I was a genius, is free this week.
*Educational only, not investment advice. Past performance is not indicative of future results.*

**2.**
The VIX looks like a statistic. It isn't one.
It's what traders are paying for protection right now, with real money behind it. Out-forecasting it means out-forecasting all of them.
I learned that the expensive way.
*Educational only, not investment advice. Past performance is not indicative of future results.*

**3.**
Five questions to ask anyone showing you a beautiful backtest:
1. Was the test written before the results?
2. What was the baseline?
3. In-sample or out-of-sample?
4. Where are the versions that failed?
5. What would prove it wrong?
*Educational only, not investment advice. Past performance is not indicative of future results.*

## Chart spec (optional, for The Number or the scorecard)

- Bar chart: stress-detection AUC by horizon (1 month 0.742, 3 months 0.557, 6 months 0.538), with a dashed reference line at 0.5 labeled "coin flip." Add VIX AUC at each horizon as a second series once pulled from the June test output.
- Source line: "Author's pre-registered backtests, 2026. Historical and hypothetical."

## Before publishing: questions for Brady

1. **The feeling slot.** "The win" section has a bracketed placeholder for how that evening actually felt. Only you can write it.
2. **Horizons.** You described testing at 1, 3, and 5 days, 1 month, 6 weeks, 2 months, and 3 months. The results found in the June test records cover three forecast-improvement horizons (p = 0.690 / 0.647 / 0.955) and stress detection at 1, 3, and 6 months. Confirm which horizon each p-value belongs to, and add any horizons whose numbers you have, so the table matches what you'll say on camera.
3. **The VIX AUC values.** The table says the VIX beat the gauge at each stress-detection horizon (significantly at 3 and 6 months), but doesn't list the VIX's own scores. Pull them from the test output if you want them in the table.
4. **The 6.8% trade.** Written as "I sold an index put" from your account. Confirm the instrument (index, expiry) and that the gauge reading and the trade direction are described the way you remember them. Selling a put is a bet the market won't fall, so the story should make clear why the gauge reading led you there.
5. **The Signal vs. Noise quote.** It's labeled a "fair paraphrase" of your spring-2026 claim (calibrated on two centuries of data, flags risk months before the VIX). If you have the exact wording from the Regime Desk material, using it verbatim is stronger.
6. **"An operating system I'm building for small businesses."** That's the governance layer now in Novissimo. It's left unnamed on purpose. Name it if you want the plug.
7. **"You'll be hearing more about it."** This teases the information-asymmetry question (and the *Beyond Control* rewrite). Cut the line if you'd rather not commit to it yet.
8. **Two years.** Used as your framing. The idea predates the build, and the build ran roughly 2023–2026; adjust if you want a more precise span.

## Compliance pass (self-imposed Rule 2210)

- Educational and impersonal throughout; no recommendations.
- The 6.8% trade is labeled as a single historical trade, paired with the risk of selling puts, and explicitly called luck.
- All test figures labeled as the author's own historical/hypothetical backtests, with dates.
- No "licensed," no "analyst" title, no firm named negatively.
- Disclosures footer reproduced verbatim (checked by script against the skill's canonical text).

## Skill note

The `north-de-noise-issue` skill still lists the old pricing ($49/month, $550/year, $399 founders). Current pricing is $790/year and $250/month. This issue doesn't mention pricing, but the skill should be updated before the next paid issue.
