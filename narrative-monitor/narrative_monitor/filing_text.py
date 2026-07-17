"""filing_text — pull the non-GAAP tells out of filing TEXT, auditably.

The estimate-heavy sectors hide their truth in supplemental disclosures that
are not structured XBRL: REIT FFO/AFFO, energy PV-10 / reserve replacement, BDC
PIK income and NAV. Those live in 10-K/10-Q tables, MD&A, and 8-K earnings
exhibits as free text.

This is a DETERMINISTIC, AUDITABLE extractor: for each metric it finds the
labeled value nearest a known phrasing and returns the number *with the source
text it came from*, so every value can be checked. It is rule-based on purpose
(a regex can't hallucinate a number that isn't on the page); swap in an
LLM-backed extractor behind the same `Extraction` contract for coverage. The
accuracy ceiling is the extractor's, and it is honest about misses — an absent
or ambiguous metric yields nothing, never a guess.

Stdlib only.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from html.parser import HTMLParser

from .models import FundamentalSnapshot

# a money/number token: optional $, optional parens (negative), digits, decimals
_NUMBER = r"\$?\(?-?[\d,]+(?:\.\d+)?\)?"
_NUMBER_RE = re.compile(_NUMBER)
_SCALE = {"thousand": 1e3, "million": 1e6, "billion": 1e9}


@dataclass(frozen=True)
class Extraction:
    """One labeled value, with the source text that justifies it."""
    metric: str
    value: float
    unit: str        # "usd" | "usd_per_share" | "ratio" | "percent"
    context: str     # the surrounding text, for audit


@dataclass(frozen=True)
class MetricSpec:
    metric: str
    label: str       # regex for the label preceding the value
    unit: str
    window: int = 140  # chars after the label to search for the value


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data) -> None:
        if not self._skip:
            self.parts.append(data)


def to_text(html: str) -> str:
    """Strip HTML to whitespace-collapsed plain text (SEC filings are .htm)."""
    if "<" not in html:
        text = html
    else:
        stripper = _Stripper()
        stripper.feed(html)
        text = " ".join(stripper.parts)
    return re.sub(r"\s+", " ", text).strip()


# a "clean" number: not glued to a letter/hyphen (so "-10" inside "PV-10" is skipped)
_CLEAN_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9\-])\$?\(?-?[\d,]+(?:\.\d+)?\)?%?")
# a value that PRECEDES a per-share phrase: "$1.85 per diluted share"
_BEFORE_PER_SHARE_RE = re.compile(
    r"(\$?[\d,]+(?:\.\d+)?)\s*(?:,?\s*or)?\s*per\s+"
    r"(?:diluted\s+|common\s+|limited\s+partnership\s+)*(?:share|unit)", re.IGNORECASE)


def _parse_number(token: str, scale_window: str, unit: str) -> float | None:
    negative = token.strip().startswith("(")
    digits = (token.replace("$", "").replace(",", "")
              .replace("(", "").replace(")", "").replace("%", ""))
    if not re.match(r"^-?\d", digits):
        return None
    value = float(digits)
    if negative:
        value = -abs(value)
    if unit == "percent":
        return value / 100.0
    if unit in ("usd", "usd_per_share"):
        low = scale_window.lower()
        for word, mult in _SCALE.items():
            if word in low:
                value *= mult
                break
    return value


def _find_value(after: str, unit: str) -> float | None:
    # per-share values often trail the total ("$412.5M, or $1.85 per share")
    if unit == "usd_per_share":
        m = _BEFORE_PER_SHARE_RE.search(after)
        if m:
            return _parse_number(m.group(1), "", "usd_per_share")
    for m in _CLEAN_NUMBER_RE.finditer(after):
        value = _parse_number(m.group(), after[m.end():m.end() + 20], unit)
        if value is not None:
            return value
    return None


def extract(text: str, specs: list[MetricSpec]) -> list[Extraction]:
    """Return one Extraction per spec whose label + a parseable value are found.

    For each spec it scans every label occurrence and keeps the first that yields
    a value in the window after it. Per-share metrics prefer a "$X per share"
    phrase; everything else takes the first clean number (one not glued inside a
    token like "PV-10").
    """
    out: list[Extraction] = []
    for spec in specs:
        label_re = re.compile(spec.label, re.IGNORECASE)
        for m in label_re.finditer(text):
            after = text[m.end():m.end() + spec.window]
            value = _find_value(after, spec.unit)
            if value is None:
                continue
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 15):m.end() + 80]).strip()
            out.append(Extraction(spec.metric, value, spec.unit, ctx))
            break
    return out


# -------------------------------------------------- per-sector metric specs
# "per share" specs precede the total ones so the negative lookahead binds right.
REIT_METRICS = [
    # per-share values trail the total ("$412.5M, or $1.85 per share"), so these
    # use the bare metric label and the "$X per share" finder picks the right one
    MetricSpec("ffo_per_share", r"(?:core |normalized )?funds from operations",
               "usd_per_share"),
    MetricSpec("affo_per_share", r"adjusted funds from operations|AFFO",
               "usd_per_share"),
    MetricSpec("dividend_per_share",
               r"dividends?(?: declared)? per (?:common )?share", "usd_per_share"),
    MetricSpec("ffo", r"(?:core |normalized )?funds from operations", "usd"),
    MetricSpec("affo", r"adjusted funds from operations|AFFO", "usd"),
    MetricSpec("same_store_noi",
               r"same[- ]store (?:cash )?net operating income", "usd"),
    MetricSpec("occupancy",
               r"(?:portfolio |same[- ]store )?occupancy(?: rate)?(?: was| of| ended at)?",
               "percent"),
]

ENERGY_METRICS = [
    MetricSpec("pv10",
               r"PV-?10|standardized measure of discounted future net cash flows",
               "usd"),
    MetricSpec("reserve_replacement_ratio", r"reserve replacement ratio(?: of| was)?",
               "percent"),
    MetricSpec("netback_per_boe", r"(?:cash )?netback per boe(?: was| of)?",
               "usd_per_share"),
]

BDC_METRICS = [
    MetricSpec("nav_per_share", r"net asset value per share(?: was| of)?",
               "usd_per_share"),
    MetricSpec("nii_per_share", r"net investment income per share(?: was| of)?",
               "usd_per_share"),
    MetricSpec("pik_income",
               r"(?:payment[- ]in[- ]kind|PIK)[^.]{0,15}?income(?: of| was| totaled)?",
               "usd"),
    MetricSpec("non_accrual_rate",
               r"non[- ]accruals?(?: were| represented| of| at)?", "percent"),
]

SECTOR_METRICS = {
    "reit": REIT_METRICS,
    "energy": ENERGY_METRICS,
    "bdc": BDC_METRICS,
}


def extract_line_items(sector: str, text: str) -> dict[str, float]:
    """Text -> the `line_items` a sector ChannelSet reads. Keys match the sector
    line-item names used in channels.py; absent metrics are simply omitted."""
    specs = SECTOR_METRICS.get(sector)
    if not specs:
        return {}
    return {e.metric: e.value for e in extract(text, specs)}


def apply_text_line_items(
    snapshots: Sequence[FundamentalSnapshot],
    texts_by_period: dict[str, str],
) -> list[FundamentalSnapshot]:
    """Merge text-extracted line items into each snapshot from its own filing.

    `texts_by_period` maps 'YYYY-Qn' -> that quarter's filing text. XBRL-derived
    line items already on the snapshot are preserved; text values fill the gaps.
    Keeps comparable-period integrity: each quarter is enriched from its own
    filing, never a later one.
    """
    out: list[FundamentalSnapshot] = []
    for snap in snapshots:
        text = texts_by_period.get(snap.period)
        if text:
            merged = {**extract_line_items(snap.sector, text), **snap.line_items}
            out.append(replace(snap, line_items=merged))
        else:
            out.append(snap)
    return out
