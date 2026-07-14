"""filing_ingestor — filings / statements -> normalized FundamentalSnapshot.

Real deployments wire this to a data stack (SEC EDGAR company-facts for the
raw filings, Bloomberg/FactSet for pre-normalized fundamentals). Write one
`FilingSource` subclass per provider; the rest of the pipeline only ever sees
FundamentalSnapshot, so swapping providers never touches the signal engine.

Ships with a stdlib CSV loader so the demo runs with zero credentials. The CSV
header is the normalized schema every provider adapter must emit.

Stdlib only.
"""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from .models import FundamentalSnapshot

# Numeric columns that map straight onto FundamentalSnapshot floats.
_FLOAT_FIELDS = (
    "revenue",
    "free_cash_flow",
    "operating_cash_flow",
    "capex",
    "gross_margin",
    "operating_margin",
    "software_growth",
    "receivables",
    "deferred_revenue",
    "stock_compensation",
    "fy_fcf_guidance",
)


def _opt_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def _opt_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _opt_bool(value: str | None) -> bool | None:
    if value is None or value.strip() == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _flag(value: str | None) -> bool:
    return bool(value) and value.strip().lower() in {"1", "true", "yes", "y"}


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


# columns the loader maps to typed fields; everything else numeric -> line_items
_RESERVED = frozenset(
    {"ticker", "period", "reported_at", "delayed_deals_recovered",
     "reported_segments", "non_gaap_metric_count", "restated", "sector"}
    | set(_FLOAT_FIELDS)
)


class FilingSource(ABC):
    """Provider adapter contract. Implement `fetch` for EDGAR, Bloomberg, etc."""

    @abstractmethod
    def fetch(self, ticker: str) -> Sequence[FundamentalSnapshot]:
        ...


class CsvFilingSource(FilingSource):
    """Loads normalized snapshots from a CSV whose header matches the schema.

    Required columns: ticker, period, revenue, free_cash_flow,
    operating_cash_flow, capex. Everything else is optional and left as None
    when blank — the engine simply won't test criteria it lacks inputs for.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch(self, ticker: str) -> list[FundamentalSnapshot]:
        rows = self.load_all()
        return [row for row in rows if row.ticker == ticker]

    def load_all(self) -> list[FundamentalSnapshot]:
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            snapshots: list[FundamentalSnapshot] = []
            for row in reader:
                kwargs = {
                    field: _opt_float(row.get(field)) for field in _FLOAT_FIELDS
                }
                # required floats must be present; let float() raise if not
                for required in (
                    "revenue",
                    "free_cash_flow",
                    "operating_cash_flow",
                    "capex",
                ):
                    kwargs[required] = float(row[required])
                # any numeric column not reserved above is a sector line item
                line_items = {
                    key: float(val)
                    for key, val in row.items()
                    if key not in _RESERVED and val not in (None, "")
                    and _is_number(val)
                }
                snapshots.append(
                    FundamentalSnapshot(
                        ticker=row["ticker"].strip(),
                        period=row["period"].strip(),
                        reported_at=row.get("reported_at", "").strip(),
                        delayed_deals_recovered=_opt_bool(
                            row.get("delayed_deals_recovered")
                        ),
                        reported_segments=_opt_int(row.get("reported_segments")),
                        non_gaap_metric_count=_opt_int(
                            row.get("non_gaap_metric_count")
                        ),
                        restated=_flag(row.get("restated")),
                        sector=(row.get("sector") or "industrial").strip(),
                        line_items=line_items,
                        **kwargs,
                    )
                )
            return snapshots
