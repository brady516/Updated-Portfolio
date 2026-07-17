"""narrative-monitor — a research and signal-gating engine.

Three questions, kept separate on purpose:
    1. What is the narrative?          -> narrative_monitor.extract_claims
    2. Has it shown up in the data?    -> signal_engine.SignalEngine.evaluate
    3. Is the evidence strong enough?  -> Signal.execution_eligible / execution_gate

NLP identifies the *claim*; the financial engine decides the *direction*. A
headline can never create an executable signal.
"""

from __future__ import annotations

from .execution_adapter import consume, execution_gate
from .filing_ingestor import CsvFilingSource, FilingSource
from .models import (
    FundamentalSnapshot,
    NarrativeClaim,
    NarrativeEvent,
    Period,
    Signal,
    SignalState,
)
from .backtest import (
    BacktestReport,
    CsvPriceSource,
    Observation,
    PriceSeries,
    run_backtest,
)
from .edgar import (
    EdgarClient,
    EdgarFilingSource,
    enrich_from_filings,
    sector_from_sic,
)
from .filing_text import (
    Extraction,
    apply_text_line_items,
    extract_line_items,
    to_text,
)
from .channels import (
    CHANNEL_SETS,
    BdcChannels,
    BrokerChannels,
    ChannelSet,
    EnergyChannels,
    FinancialChannels,
    IndustrialChannels,
    InsuranceChannels,
    LenderChannels,
    ReitChannels,
    SaasChannels,
    channel_set_for,
)
from .narrative_ingestor import (
    JsonlNarrativeSource,
    NarrativeSource,
    PropagationSummary,
    parrot_propagation,
)
from .narrative_monitor import (
    benign_alignment,
    extract_claims,
    narrative_entropy,
    narrative_intensity,
)
from .signal_engine import SignalEngine
from .store import SignalStore, publish_signal

__all__ = [
    "CHANNEL_SETS",
    "BacktestReport",
    "BdcChannels",
    "BrokerChannels",
    "ChannelSet",
    "EnergyChannels",
    "CsvFilingSource",
    "CsvPriceSource",
    "EdgarClient",
    "EdgarFilingSource",
    "Extraction",
    "FilingSource",
    "apply_text_line_items",
    "enrich_from_filings",
    "extract_line_items",
    "to_text",
    "FinancialChannels",
    "IndustrialChannels",
    "InsuranceChannels",
    "LenderChannels",
    "ReitChannels",
    "SaasChannels",
    "channel_set_for",
    "FundamentalSnapshot",
    "JsonlNarrativeSource",
    "Observation",
    "PriceSeries",
    "NarrativeClaim",
    "NarrativeEvent",
    "NarrativeSource",
    "Period",
    "PropagationSummary",
    "Signal",
    "SignalEngine",
    "SignalState",
    "SignalStore",
    "benign_alignment",
    "consume",
    "execution_gate",
    "extract_claims",
    "narrative_entropy",
    "narrative_intensity",
    "parrot_propagation",
    "publish_signal",
    "run_backtest",
    "sector_from_sic",
]
