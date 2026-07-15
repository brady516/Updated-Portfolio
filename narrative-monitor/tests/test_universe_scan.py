"""Tests for the universe scanner plumbing — offline, with a fake source.

Verifies the scan loop records actionable hits, skips missing/short names, is
resumable (a re-run adds nothing), and that ranking reads it back. No network.
"""

from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from narrative_monitor import samples

import run_universe_scan as scanner


class _FakeSource:
    """Stands in for EdgarFilingSource: ticker -> snapshots, Exception, or 404."""

    def __init__(self, mapping: dict) -> None:
        self.mapping = mapping

    def fetch(self, ticker: str):
        if ticker not in self.mapping:
            raise urllib.error.HTTPError(ticker, 404, "Not Found", {}, None)
        value = self.mapping[ticker]
        if isinstance(value, Exception):
            raise value
        return value


class ScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()) / "hits.jsonl"
        self.source = _FakeSource({
            "BREAK": samples.industrial("BREAK"),        # confirms
            "SHORT": samples.industrial("SHORT")[:2],    # too few quarters
            "ERRME": urllib.error.URLError("boom"),      # transient error
            # "MISS" absent -> 404 no-data
        })

    def test_records_hits_and_skips_the_rest(self) -> None:
        scanner.scan(["BREAK", "SHORT", "ERRME", "MISS"], self.tmp, self.source)
        rows = {json.loads(l)["ticker"]: json.loads(l)
                for l in self.tmp.read_text().splitlines()}
        self.assertIn("BREAK", rows)
        self.assertEqual(rows["BREAK"]["state"], "confirmed_deterioration")
        self.assertTrue(rows["BREAK"]["execution_eligible"])
        for skipped in ("SHORT", "ERRME", "MISS"):
            self.assertNotIn(skipped, rows)

    def test_resume_skips_already_scanned(self) -> None:
        scanner.scan(["BREAK"], self.tmp, self.source)
        first = self.tmp.read_text()
        scanner.scan(["BREAK"], self.tmp, self.source)   # re-run
        self.assertEqual(self.tmp.read_text(), first)     # nothing appended

    def test_already_done_parses_output(self) -> None:
        scanner.scan(["BREAK"], self.tmp, self.source)
        self.assertEqual(scanner._already_done(self.tmp), {"BREAK"})


if __name__ == "__main__":
    unittest.main()
