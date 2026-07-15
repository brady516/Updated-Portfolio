"""edgar — a live FilingSource backed by SEC EDGAR company-facts (XBRL).

Turns a ticker into as-filed, point-in-time FundamentalSnapshots straight from
SEC's free, public XBRL API — no key, just a declared User-Agent (SEC rule):

    https://www.sec.gov/files/company_tickers.json          ticker -> CIK
    https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json   the facts

Two disciplines the whole engine depends on are enforced here:

  * AS-FILED ONLY. company-facts returns every value ever filed for a period
    (original 10-Q/10-K plus later amendments/restatements). For each period we
    keep the EARLIEST-filed value — the number that existed on the filing date —
    and use its `filed` date as `reported_at`. Restatements are never used.
  * DISCRETE QUARTERS. XBRL flow facts come as 3-month, 6/9-month YTD, and
    annual durations. We take the discrete calendar-quarter facts (SEC `frame`
    like "CY2023Q3") and DERIVE Q4 = annual - (Q1+Q2+Q3), so comparable-period
    and TTM logic see clean quarters.

Stdlib only. Network egress to sec.gov must be permitted by the environment.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from .filing_ingestor import FilingSource
from .models import FundamentalSnapshot

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

_FRAME_Q = re.compile(r"^CY(\d{4})Q([1-4])$")     # discrete calendar quarter (duration)
_FRAME_QI = re.compile(r"^CY(\d{4})Q([1-4])I$")   # calendar quarter-end (instant)
_FRAME_FY = re.compile(r"^CY(\d{4})$")            # calendar year (duration)

# normalized field -> ordered us-gaap concept fallbacks
_DURATION_CONCEPTS: dict[str, list[str]] = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues", "SalesRevenueNet"],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities",
                            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"],
    "stock_compensation": ["ShareBasedCompensation"],
}
_INSTANT_CONCEPTS: dict[str, list[str]] = {
    "receivables": ["AccountsReceivableNetCurrent"],
    "deferred_revenue": ["ContractWithCustomerLiabilityCurrent",
                         "DeferredRevenueCurrent"],
}


class EdgarClient:
    """Proxy- and CA-aware HTTP client for SEC EDGAR. Read-only, polite."""

    def __init__(self, email: str, *, min_interval: float = 0.2,
                 cafile: str | None = None) -> None:
        # SEC requires a User-Agent that identifies you with a contact address.
        self.user_agent = f"narrative-monitor {email}"
        self.min_interval = min_interval
        self._last = 0.0
        self._ticker_cik: dict[str, int] | None = None
        ctx = ssl.create_default_context()
        cafile = cafile or os.environ.get("SSL_CERT_FILE")
        if not cafile and os.path.exists("/root/.ccr/ca-bundle.crt"):
            cafile = "/root/.ccr/ca-bundle.crt"
        if cafile and os.path.exists(cafile):
            ctx.load_verify_locations(cafile)
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler(urllib.request.getproxies()),
            urllib.request.HTTPSHandler(context=ctx),
        )

    def _get(self, url: str, retries: int = 4) -> bytes:
        for attempt in range(retries):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
            })
            try:
                with self._opener.open(req, timeout=30) as resp:
                    self._last = time.monotonic()
                    data = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        import gzip
                        data = gzip.decompress(data)
                    return data
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(f"EDGAR request failed after {retries} attempts: {url}")

    def ticker_to_cik(self, ticker: str) -> int:
        if self._ticker_cik is None:
            raw = json.loads(self._get(TICKER_MAP_URL))
            self._ticker_cik = {
                row["ticker"].upper(): int(row["cik_str"]) for row in raw.values()
            }
        try:
            return self._ticker_cik[ticker.upper()]
        except KeyError:
            raise KeyError(f"Ticker {ticker!r} not found in SEC ticker map.")

    def company_facts(self, cik: int) -> dict:
        return json.loads(self._get(COMPANY_FACTS_URL.format(cik=cik)))


@dataclass
class _AsFiled:
    """The earliest-filed value for a period, with its filing date."""
    val: float
    filed: str


def _pick_as_filed(existing: _AsFiled | None, val: float, filed: str) -> _AsFiled:
    """Keep the earliest-filed datapoint — the number that existed on the wire."""
    if existing is None or filed < existing.filed:
        return _AsFiled(val, filed)
    return existing


def _first_present(facts: dict, concepts: list[str]) -> list[dict] | None:
    """Return the USD unit datapoints for the first concept that exists."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for concept in concepts:
        node = us_gaap.get(concept)
        if node:
            units = node.get("units", {})
            for unit_key in ("USD", "USD/shares"):
                if unit_key in units:
                    return units[unit_key]
    return None


def _duration_series(points: list[dict]) -> dict[str, _AsFiled]:
    """period 'YYYY-Qn' -> as-filed value for a flow concept.

    Discrete quarters come from CY####Qn frames; Q4 is derived from the annual
    CY#### frame minus the three earlier quarters of the same year.
    """
    quarters: dict[str, _AsFiled] = {}
    annual: dict[int, _AsFiled] = {}
    for p in points:
        frame = p.get("frame")
        val, filed = p.get("val"), p.get("filed", "")
        if val is None or not frame:
            continue
        mq = _FRAME_Q.match(frame)
        if mq:
            key = f"{mq.group(1)}-Q{mq.group(2)}"
            quarters[key] = _pick_as_filed(quarters.get(key), float(val), filed)
            continue
        my = _FRAME_FY.match(frame)
        if my:
            year = int(my.group(1))
            annual[year] = _pick_as_filed(annual.get(year), float(val), filed)
    # derive discrete Q4 = annual - (Q1 + Q2 + Q3)
    for year, ann in annual.items():
        q4 = f"{year}-Q4"
        parts = [quarters.get(f"{year}-Q{q}") for q in (1, 2, 3)]
        if q4 not in quarters and all(parts):
            derived = ann.val - sum(part.val for part in parts)
            quarters[q4] = _AsFiled(derived, ann.filed)
    return quarters


def _instant_series(points: list[dict]) -> dict[str, _AsFiled]:
    """period 'YYYY-Qn' -> as-filed value for a balance-sheet (instant) concept."""
    out: dict[str, _AsFiled] = {}
    for p in points:
        frame = p.get("frame")
        val, filed = p.get("val"), p.get("filed", "")
        if val is None or not frame:
            continue
        mi = _FRAME_QI.match(frame)
        if mi:
            key = f"{mi.group(1)}-Q{mi.group(2)}"
            out[key] = _pick_as_filed(out.get(key), float(val), filed)
    return out


class EdgarFilingSource(FilingSource):
    """Live FilingSource over SEC EDGAR company-facts.

    Emits the industrial concept set (revenue, FCF, gross margin, receivables) —
    the universal ones every filer reports. Sector-specific tags (bank reserves,
    REIT FFO, …) are a follow-on concept map; the normalization here is the seam.
    """

    def __init__(self, email: str, client: EdgarClient | None = None,
                 sector: str = "industrial") -> None:
        self.client = client or EdgarClient(email)
        self.sector = sector

    def fetch(self, ticker: str) -> list[FundamentalSnapshot]:
        cik = self.client.ticker_to_cik(ticker)
        facts = self.client.company_facts(cik)
        return self.normalize(facts, ticker)

    def normalize(self, facts: dict, ticker: str) -> list[FundamentalSnapshot]:
        dur = {
            field: _duration_series(points)
            for field, concepts in _DURATION_CONCEPTS.items()
            if (points := _first_present(facts, concepts)) is not None
        }
        inst = {
            field: _instant_series(points)
            for field, concepts in _INSTANT_CONCEPTS.items()
            if (points := _first_present(facts, concepts)) is not None
        }

        def val(series: dict[str, dict[str, _AsFiled]], field: str,
                period: str) -> float | None:
            af = series.get(field, {}).get(period)
            return af.val if af else None

        # a snapshot needs the core flow trio present
        periods = sorted(
            p for p in dur.get("revenue", {})
            if dur.get("operating_cash_flow", {}).get(p)
            and dur.get("capex", {}).get(p)
        )
        snapshots: list[FundamentalSnapshot] = []
        for period in periods:
            revenue = val(dur, "revenue", period)
            ocf = val(dur, "operating_cash_flow", period)
            capex = val(dur, "capex", period)
            if revenue in (None, 0) or ocf is None or capex is None:
                continue
            cost = val(dur, "cost_of_revenue", period)
            gross_margin = (revenue - cost) / revenue if cost is not None else None
            reported_at = dur["revenue"][period].filed
            snapshots.append(FundamentalSnapshot(
                ticker=ticker.upper(),
                period=period,
                revenue=revenue,
                operating_cash_flow=ocf,
                capex=capex,
                free_cash_flow=ocf - capex,           # FCF = OCF - capex
                gross_margin=gross_margin,
                receivables=val(inst, "receivables", period),
                deferred_revenue=val(inst, "deferred_revenue", period),
                stock_compensation=val(dur, "stock_compensation", period),
                reported_at=reported_at,
                sector=self.sector,
            ))
        return snapshots
