"""Data models shared across the narrative-monitor services.

The whole design rests on one separation: a *narrative* is a claim someone
made ("AI investment temporarily depressed results"); *evidence* is what the
reported financials actually show. These dataclasses keep the two apart so no
service can quietly turn a headline into a direction.

Stdlib only. Python 3.11+ (StrEnum).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum


class SignalState(StrEnum):
    """The five states the engine is allowed to emit.

    Only CONFIRMED_DETERIORATION is ever executable, and even that requires a
    confidence and history check downstream (see execution_adapter).
    """

    NARRATIVE_ONLY = "narrative_only"
    EARLY_EVIDENCE = "early_evidence"
    CONFIRMED_DETERIORATION = "confirmed_deterioration"
    IMPROVING = "improving"
    INCONCLUSIVE = "inconclusive"


# Quarterly periods look like "2026-Q1". Everything comparable-period lives or
# dies on parsing these correctly, so it is centralized here.
_PERIOD_RE = re.compile(r"^(?P<year>\d{4})-Q(?P<quarter>[1-4])$")


@dataclass(frozen=True, order=True)
class Period:
    """A fiscal quarter, orderable and comparable-period aware.

    "Comparable period" means the *same quarter one year earlier* — Q4/Q4,
    Q3/Q3 — never the sequentially prior quarter. Sequential comparison is the
    seasonality trap this whole engine exists to avoid.
    """

    year: int
    quarter: int

    @classmethod
    def parse(cls, text: str) -> "Period":
        match = _PERIOD_RE.match(text.strip())
        if not match:
            raise ValueError(
                f"Period must look like '2026-Q1', got {text!r}."
            )
        return cls(int(match["year"]), int(match["quarter"]))

    def prior_year(self) -> "Period":
        """The comparable period: same quarter, one year earlier."""
        return Period(self.year - 1, self.quarter)

    def __str__(self) -> str:
        return f"{self.year}-Q{self.quarter}"


@dataclass(frozen=True)
class FundamentalSnapshot:
    """One quarter of normalized statement data for one ticker.

    Optional fields default to None so a partial filing still ingests; the
    signal engine simply can't test a criterion whose inputs are missing
    (it counts that criterion as "not supported", never as "supported").
    """

    ticker: str
    period: str  # "YYYY-Qn"
    revenue: float
    free_cash_flow: float
    operating_cash_flow: float
    capex: float
    gross_margin: float | None = None
    operating_margin: float | None = None
    software_growth: float | None = None
    receivables: float | None = None
    deferred_revenue: float | None = None
    stock_compensation: float | None = None
    # Full-year FCF guidance management stood behind *as of* this quarter.
    # A cut across quarters is criterion #6.
    fy_fcf_guidance: float | None = None
    # Tri-state: True  = deals management said were "timing" showed up later,
    #            False = they did not (supports deterioration, criterion #7),
    #            None  = not yet knowable.
    delayed_deals_recovered: bool | None = None
    # Disclosure microstructure — the reporting-entropy H(R) channel. A drop in
    # reported segments or a jump in non-GAAP metrics is obfuscation, and
    # obfuscation while the narrative stays confident is itself divergence.
    reported_segments: int | None = None
    non_gaap_metric_count: int | None = None
    reported_at: str = ""
    # POINT-IN-TIME CONTRACT: True means this row reflects a later restatement.
    # Restated data is the one way the future leaks into a contemporaneous
    # signal, so the engine refuses to make a restated row executable.
    restated: bool = False
    # Which microstructure the truth is denominated in. Selects the ChannelSet
    # (industrial | financial | reit | ...). The divergence x entropy math is
    # identical across sectors; only the line items being read change.
    sector: str = "industrial"
    # Sector-specific line items keyed by name (e.g. "net_charge_offs",
    # "affo", "same_store_noi"). Keeps FundamentalSnapshot from growing a field
    # per sector — a ChannelSet reads exactly the keys it needs and treats a
    # missing key as untestable, never as "supported".
    line_items: dict[str, float] = field(default_factory=dict)

    @property
    def parsed_period(self) -> Period:
        return Period.parse(self.period)

    @property
    def fcf_margin(self) -> float:
        if self.revenue == 0:
            return math.nan
        return self.free_cash_flow / self.revenue

    @property
    def capex_intensity(self) -> float:
        if self.revenue == 0:
            return math.nan
        return self.capex / self.revenue

    @property
    def cash_conversion(self) -> float:
        if self.operating_cash_flow == 0:
            return math.nan
        return self.free_cash_flow / self.operating_cash_flow


@dataclass(frozen=True)
class NarrativeEvent:
    """A raw claim: a headline, transcript passage, or press release.

    Direction is NEVER read from this. narrative_monitor extracts *which claim*
    is being made; the signal engine decides whether the financials support it.
    """

    ticker: str
    event_time: str
    headline: str
    body: str
    source: str
    # Where in the parrot layer this sits. The frame originates with
    # "management" and is echoed by "sell_side" and "media"; measuring that
    # propagation is how narrative entropy and decay are estimated.
    source_type: str = "other"  # management | sell_side | media | other


@dataclass(frozen=True)
class NarrativeClaim:
    """A structured claim extracted from a NarrativeEvent.

    `label` is a management-explanation category (e.g. "ai_investment"). The
    engine maps each claim to the financial tests that would confirm or
    contradict it, and reports whether the data does either — the claim itself
    carries no bullish/bearish sign.
    """

    ticker: str
    label: str
    phrase: str
    source: str
    # The claim's stance toward the reporting, NEVER its market direction:
    #   "benign" = the frame asserts nothing is really wrong (timing, AI
    #              investment, temporary headwind, pipeline intact),
    #   "admit"  = the frame concedes weakness (guidance cut, demand softness),
    #   "neutral" = no stance.
    # A benign consensus contradicted by the reporting is the breakdown setup.
    stance: str = "neutral"


@dataclass(frozen=True)
class Signal:
    """The engine's output. `execution_eligible` is the only field the trading
    process is allowed to trust as a go/no-go."""

    ticker: str
    state: SignalState
    score: float
    confidence: float
    generated_at: str
    reasons: list[str]
    metrics: dict[str, float | str | None]
    execution_eligible: bool
    claims: list[str] = field(default_factory=list)
    confirmed_criteria: list[str] = field(default_factory=list)
    # Breakdown model (see THESIS.md). `breakdown_score` is S_t in [0,1];
    # `divergence` is signed (>0 reporting worse than narrative implies).
    divergence: float = 0.0
    breakdown_score: float = 0.0
    narrative_entropy: float = 0.0
    reporting_entropy: float = 0.0
    # Ordinal capitulation speed derived from narrative entropy:
    # "slow" (tight consensus) | "medium" | "fast" | "n/a".
    expected_decay: str = "n/a"
