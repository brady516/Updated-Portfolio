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
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

# SIC code ranges -> our ChannelSet sector. First match wins; else "industrial".
_SIC_SECTOR: list[tuple[int, int, str]] = [
    (6020, 6079, "financial"),   # depository / banks
    (6300, 6399, "insurance"),   # insurance carriers
    (6798, 6798, "reit"),        # real estate investment trusts
    (6726, 6726, "bdc"),         # investment offices (many BDCs)
    (6141, 6199, "lender"),      # personal credit / finance services
    (1311, 1311, "energy"),      # crude petroleum & natural gas
    (1381, 1389, "energy"),      # oil & gas field services
    (7370, 7374, "saas"),        # computer / prepackaged software services
]


def sector_from_sic(sic: int | None) -> str:
    for lo, hi, name in _SIC_SECTOR:
        if sic is not None and lo <= sic <= hi:
            return name
    return "industrial"

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
    # SaaS: total remaining performance obligation (contracted backlog)
    "crpo": ["RevenueRemainingPerformanceObligation"],
}


class EdgarClient:
    """Proxy- and CA-aware HTTP client for SEC EDGAR. Read-only, polite."""

    def __init__(self, email: str, *, min_interval: float = 0.2,
                 cafile: str | None = None, cache_dir: str | None = None) -> None:
        # SEC requires a User-Agent that identifies you with a contact address.
        self.user_agent = f"narrative-monitor {email}"
        self.min_interval = min_interval
        self._last = 0.0
        self._ticker_cik: dict[str, int] | None = None
        # optional on-disk cache of raw responses (skip re-downloading on re-runs)
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
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
        cache_path = None
        if self.cache_dir:
            import hashlib
            key = hashlib.sha1(url.encode()).hexdigest()
            cache_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as fh:
                    return fh.read()
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
                    if cache_path:
                        with open(cache_path, "wb") as fh:
                            fh.write(data)
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

    def all_tickers(self) -> list[str]:
        """Every ticker in SEC's map (~10k+ filers), deduplicated and sorted."""
        if self._ticker_cik is None:
            raw = json.loads(self._get(TICKER_MAP_URL))
            self._ticker_cik = {
                row["ticker"].upper(): int(row["cik_str"]) for row in raw.values()
            }
        return sorted(self._ticker_cik)

    def company_facts(self, cik: int) -> dict:
        return json.loads(self._get(COMPANY_FACTS_URL.format(cik=cik)))

    def company_sic(self, cik: int) -> int | None:
        """The filer's SIC industry code (from the submissions API)."""
        try:
            sub = json.loads(self._get(SUBMISSIONS_URL.format(cik=cik)))
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
            return None
        sic = sub.get("sic")
        return int(sic) if sic not in (None, "") else None


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


def _saas_line_items(periods: list[str], dur: dict, inst: dict) -> dict[str, dict]:
    """Derive the SaaS microstructure the engine needs from XBRL facts.

    The leading indicators are derivable from standard tags:
      billings = revenue + (deferred_revenue_end - prior deferred_revenue_end)
      cRPO     = RevenueRemainingPerformanceObligation
      sbc %    = ShareBasedCompensation / revenue
    Net revenue retention and S&M efficiency are NOT structured XBRL, so those
    channels stay dark (missing input = untestable, never a false positive).
    """
    def v(series, field, period):
        af = series.get(field, {}).get(period)
        return af.val if af else None

    out: dict[str, dict] = {}
    for i, period in enumerate(periods):
        rev = v(dur, "revenue", period)
        deferred = v(inst, "deferred_revenue", period)
        prev_deferred = v(inst, "deferred_revenue", periods[i - 1]) if i else None
        items: dict[str, float] = {}
        if rev is not None and deferred is not None and prev_deferred is not None:
            items["billings"] = rev + (deferred - prev_deferred)
        if deferred is not None:
            items["deferred_revenue"] = deferred
        crpo = v(inst, "crpo", period)
        if crpo is not None:
            items["crpo"] = crpo
        sbc = v(dur, "stock_compensation", period)
        if sbc is not None and rev:
            items["sbc_pct_revenue"] = sbc / rev
        out[period] = items
    return out


# sectors whose microstructure the live XBRL adapter can populate today
_LIVE_SECTOR_DERIVERS = {"saas": _saas_line_items}


class EdgarFilingSource(FilingSource):
    """Live FilingSource over SEC EDGAR company-facts.

    Routes each filer to its ChannelSet by SIC code and populates the sector's
    line items where XBRL supports it. Today that is `industrial` (FCF/margins,
    every filer) and `saas` (billings/RPO/deferred/SBC, derived from standard
    tags). Other sectors are routed correctly but read `inconclusive` until their
    concept maps are wired — estimate-heavy metrics (REIT FFO, insurer combined
    ratio, BDC PIK) are non-GAAP supplemental disclosures, not structured XBRL,
    so they need a filing-text or vendor layer, not just more tags.
    """

    def __init__(self, email: str, client: EdgarClient | None = None,
                 sector: str | None = None, detect_sector: bool = True) -> None:
        self.client = client or EdgarClient(email)
        self.sector = sector            # explicit override; else detect by SIC
        self.detect_sector = detect_sector

    def fetch(self, ticker: str) -> list[FundamentalSnapshot]:
        cik = self.client.ticker_to_cik(ticker)
        if self.sector is not None:
            sector = self.sector
        elif self.detect_sector:
            sector = sector_from_sic(self.client.company_sic(cik))
        else:
            sector = "industrial"
        facts = self.client.company_facts(cik)
        return self.normalize(facts, ticker, sector)

    def normalize(self, facts: dict, ticker: str,
                  sector: str = "industrial") -> list[FundamentalSnapshot]:
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
        deriver = _LIVE_SECTOR_DERIVERS.get(sector)
        line_items_by_period = deriver(periods, dur, inst) if deriver else {}

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
                sector=sector,
                line_items=line_items_by_period.get(period, {}),
            ))
        return snapshots
