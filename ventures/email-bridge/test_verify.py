#!/usr/bin/env python3
"""
test_verify.py — fixture tests for verify.py's parsing and status logic.

No network. A stub resolver returns canned DNS answers so the decisions that
matter can be asserted: that transport failure is UNKNOWN rather than PASS,
that an unconfigured DKIM selector is UNKNOWN rather than PASS, that p=none
is not enforcement, and that long TXT records concatenate instead of being
split in half.

Usage:  python3 -I test_verify.py
"""

import unittest

import verify
from verify import FAIL, PASS, UNKNOWN


class Stub(verify.Resolver):
    """Returns canned answers; records what was asked."""

    def __init__(self, answers, error=None):
        self.name = "stub"
        self.answers = answers          # {(name, rtype): [records]}
        self.error = error
        self.asked = []

    def query(self, name, rtype):
        self.asked.append((name, rtype))
        if self.error:
            return {"status": None, "records": [], "error": self.error}
        key = (name.lower(), rtype)
        return {"status": 0, "records": self.answers.get(key, []), "error": None}


D = "mikesdrywall.com"


class TestTxtConcatenation(unittest.TestCase):
    def test_adjacent_quoted_strings_join_with_no_separator(self):
        # A >255-char DKIM key arrives as two quoted strings. Splitting them
        # or joining with a space corrupts the key.
        raw = '"v=DKIM1; k=rsa; p=AAAA" "BBBBCCCC"'
        self.assertEqual(verify._clean(raw, "TXT"),
                         "v=DKIM1; k=rsa; p=AAAABBBBCCCC")

    def test_mx_is_lowercased_and_root_dot_stripped(self):
        self.assertEqual(verify._clean("10 MX1.Example.COM.", "MX"),
                         "10 mx1.example.com")


class TestTransportFailureIsUnknown(unittest.TestCase):
    """The central rule: learning nothing is never a pass, and never a fail."""

    def test_every_dns_check_returns_unknown_on_transport_error(self):
        res = Stub({}, error="URLError: tunnel refused")
        rows = verify._dns_checks(D, {"mx": ["a.example.com"],
                                      "spf_includes": ["spf.example.com"],
                                      "dkim_selectors": ["key1"],
                                      "dmarc_policy": "quarantine"}, res)
        self.assertEqual([r["status"] for r in rows], [UNKNOWN] * 4)
        for r in rows:
            self.assertIsNotNone(r["checked_at"])
            self.assertTrue(r["limitation"])


class TestMx(unittest.TestCase):
    def test_exact_match_passes(self):
        res = Stub({(D, "MX"): ["10 route1.mx.cloudflare.net",
                                "20 route2.mx.cloudflare.net"]})
        r = verify.check_mx(D, ["route2.mx.cloudflare.net",
                                "route1.mx.cloudflare.net"], res)
        self.assertEqual(r["status"], PASS)

    def test_extra_host_fails(self):
        res = Stub({(D, "MX"): ["10 route1.mx.cloudflare.net",
                                "10 stale.oldhost.net"]})
        r = verify.check_mx(D, ["route1.mx.cloudflare.net"], res)
        self.assertEqual(r["status"], FAIL)

    def test_no_mx_at_all_fails(self):
        r = verify.check_mx(D, ["route1.mx.cloudflare.net"], Stub({}))
        self.assertEqual(r["status"], FAIL)

    def test_no_expectation_is_unknown_not_pass(self):
        res = Stub({(D, "MX"): ["10 route1.mx.cloudflare.net"]})
        r = verify.check_mx(D, None, res)
        self.assertEqual(r["status"], UNKNOWN)
        self.assertEqual(r["observed"], ["route1.mx.cloudflare.net"])


class TestSpf(unittest.TestCase):
    def test_single_valid_record_with_expected_include_passes(self):
        res = Stub({(D, "TXT"): ["v=spf1 include:spf.migadu.com ~all"],
                    ("spf.migadu.com", "TXT"): ["v=spf1 ip4:1.2.3.4 -all"]})
        r = verify.check_spf(D, ["spf.migadu.com"], res)
        self.assertEqual(r["status"], PASS)
        self.assertEqual(r["observed"]["lookups"], 1)

    def test_two_spf_records_fail(self):
        res = Stub({(D, "TXT"): ["v=spf1 include:a.com ~all",
                                 "v=spf1 include:b.com ~all"]})
        self.assertEqual(verify.check_spf(D, None, res)["status"], FAIL)

    def test_missing_all_mechanism_fails(self):
        res = Stub({(D, "TXT"): ["v=spf1 include:spf.migadu.com"],
                    ("spf.migadu.com", "TXT"): ["v=spf1 -all"]})
        r = verify.check_spf(D, ["spf.migadu.com"], res)
        self.assertEqual(r["status"], FAIL)
        self.assertIn("no 'all' mechanism", " ".join(r["observed"]["problems"]))

    def test_expected_include_absent_fails(self):
        res = Stub({(D, "TXT"): ["v=spf1 include:_spf.google.com ~all"],
                    ("_spf.google.com", "TXT"): ["v=spf1 -all"]})
        r = verify.check_spf(D, ["spf.migadu.com"], res)
        self.assertEqual(r["status"], FAIL)

    def test_lookup_limit_counted_recursively(self):
        # 1 include at the apex + 11 nested = 12, over the RFC 7208 limit of 10.
        nested = " ".join(f"include:n{i}.com" for i in range(11))
        answers = {(D, "TXT"): ["v=spf1 include:top.com ~all"],
                   ("top.com", "TXT"): [f"v=spf1 {nested} ~all"]}
        for i in range(11):
            answers[(f"n{i}.com", "TXT")] = ["v=spf1 -all"]
        r = verify.check_spf(D, ["top.com"], Stub(answers))
        self.assertEqual(r["status"], FAIL)
        self.assertEqual(r["observed"]["lookups"], 12)

    def test_unresolvable_include_is_unknown_not_pass(self):
        # Syntax is fine, but the count could not be completed.
        class Partial(Stub):
            def query(self, name, rtype):
                if name == "spf.migadu.com":
                    return {"status": None, "records": [], "error": "timeout"}
                return super().query(name, rtype)

        res = Partial({(D, "TXT"): ["v=spf1 include:spf.migadu.com ~all"]})
        r = verify.check_spf(D, ["spf.migadu.com"], res)
        self.assertEqual(r["status"], UNKNOWN)
        self.assertTrue(r["evidence"]["unresolved_includes"])

    def test_include_loop_does_not_hang(self):
        res = Stub({(D, "TXT"): ["v=spf1 include:loop.com ~all"],
                    ("loop.com", "TXT"): ["v=spf1 include:loop.com ~all"]})
        self.assertIn(verify.check_spf(D, ["loop.com"], res)["status"],
                      (PASS, FAIL, UNKNOWN))


class TestDkim(unittest.TestCase):
    def test_no_selectors_configured_is_unknown(self):
        """The requirement that must never regress: an undiscovered selector
        cannot silently become a pass."""
        r = verify.check_dkim(D, None, Stub({}))
        self.assertEqual(r["status"], UNKNOWN)
        r = verify.check_dkim(D, [], Stub({}))
        self.assertEqual(r["status"], UNKNOWN)

    def test_published_key_passes(self):
        res = Stub({(f"key1._domainkey.{D}", "TXT"):
                    ["v=DKIM1; k=rsa; p=MIIBIjANBgkqh"]})
        self.assertEqual(verify.check_dkim(D, ["key1"], res)["status"], PASS)

    def test_record_present_but_empty_key_fails(self):
        res = Stub({(f"key1._domainkey.{D}", "TXT"): ["v=DKIM1; k=rsa; p="]})
        self.assertEqual(verify.check_dkim(D, ["key1"], res)["status"], FAIL)

    def test_one_missing_selector_fails_the_check(self):
        res = Stub({(f"key1._domainkey.{D}", "TXT"): ["v=DKIM1; p=AAAA"]})
        r = verify.check_dkim(D, ["key1", "key2"], res)
        self.assertEqual(r["status"], FAIL)
        self.assertEqual(r["observed"]["missing"], ["key2"])


class TestDmarc(unittest.TestCase):
    def test_no_record_fails(self):
        self.assertEqual(verify.check_dmarc(D, "quarantine", Stub({}))["status"], FAIL)

    def test_p_none_is_not_enforcement(self):
        res = Stub({(f"_dmarc.{D}", "TXT"): ["v=DMARC1; p=none; sp=none"]})
        r = verify.check_dmarc(D, "quarantine", res)
        self.assertEqual(r["status"], FAIL)
        self.assertFalse(r["observed"]["enforcing"])

    def test_p_none_recorded_as_not_enforcing_even_when_expected(self):
        res = Stub({(f"_dmarc.{D}", "TXT"): ["v=DMARC1; p=none"]})
        r = verify.check_dmarc(D, "none", res)
        self.assertEqual(r["status"], PASS)      # matches what was asked for
        self.assertFalse(r["observed"]["enforcing"])  # but is still not protection

    def test_matching_policy_passes_and_parses_tags(self):
        res = Stub({(f"_dmarc.{D}", "TXT"):
                    ["v=DMARC1; p=quarantine; pct=50; rua=mailto:r@x.com"]})
        r = verify.check_dmarc(D, "quarantine", res)
        self.assertEqual(r["status"], PASS)
        self.assertEqual(r["observed"]["pct"], "50")
        self.assertEqual(r["observed"]["rua"], "mailto:r@x.com")

    def test_no_expected_policy_is_unknown(self):
        res = Stub({(f"_dmarc.{D}", "TXT"): ["v=DMARC1; p=reject"]})
        self.assertEqual(verify.check_dmarc(D, None, res)["status"], UNKNOWN)


class TestFormAdapter(unittest.TestCase):
    """Observation only. This check has no PASS branch, by design."""

    def _run(self, html):
        class R:
            status = 200
            def read(self, n): return html.encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False

        orig = verify.urllib.request.urlopen
        verify.urllib.request.urlopen = lambda *a, **k: R()
        try:
            return verify.check_form("https://example.com/contact")
        finally:
            verify.urllib.request.urlopen = orig

    def test_visible_freemail_address_fails(self):
        r = self._run('<a href="mailto:mikesdrywall1987@gmail.com">email</a>')
        self.assertEqual(r["status"], FAIL)
        self.assertEqual(r["observed"]["freemail_addresses_visible"],
                         ["mikesdrywall1987@gmail.com"])

    def test_clean_page_is_unknown_never_pass(self):
        r = self._run('<form action="/submit"><input name="email"></form>'
                      '<p>mike@mikesdrywall.com</p>')
        self.assertEqual(r["status"], UNKNOWN)
        self.assertEqual(r["observed"]["form_actions"], ["/submit"])

    def test_unreachable_page_is_unknown(self):
        orig = verify.urllib.request.urlopen

        def boom(*a, **k):
            raise verify.urllib.error.URLError("refused")

        verify.urllib.request.urlopen = boom
        try:
            self.assertEqual(
                verify.check_form("https://example.com/contact")["status"], UNKNOWN)
        finally:
            verify.urllib.request.urlopen = orig

    def test_no_code_path_returns_pass(self):
        # Guard against someone later "improving" this into a judgement.
        import inspect
        src = inspect.getsource(verify.check_form)
        self.assertNotIn('"form_destination", PASS', src)


class TestExitCodes(unittest.TestCase):
    def _finish(self, statuses):
        rows = [verify.result(f"c{i}", s, None, None, {}, "x")
                for i, s in enumerate(statuses)]
        return verify.finish({"domain": D, "checked_at": verify.now(),
                              "resolver": "stub", "profile": None,
                              "checks": rows}, None)

    def test_all_pass_is_zero(self):
        self.assertEqual(self._finish([PASS, PASS]), 0)

    def test_any_fail_is_one(self):
        self.assertEqual(self._finish([PASS, UNKNOWN, FAIL]), 1)

    def test_unknown_without_fail_is_two_not_zero(self):
        self.assertEqual(self._finish([PASS, UNKNOWN]), 2)


class TestEveryRowIsAuditable(unittest.TestCase):
    def test_all_checks_carry_timestamp_expected_evidence_limitation(self):
        res = Stub({(D, "MX"): ["10 a.example.com"],
                    (D, "TXT"): ["v=spf1 -all"],
                    (f"_dmarc.{D}", "TXT"): ["v=DMARC1; p=none"],
                    (f"k._domainkey.{D}", "TXT"): ["v=DKIM1; p=AAAA"]})
        rows = verify._dns_checks(D, {"dkim_selectors": ["k"]}, res)
        for r in rows:
            for key in ("check", "status", "checked_at", "observed",
                        "expected", "evidence", "limitation"):
                self.assertIn(key, r, f"{r['check']} missing {key}")
            self.assertIn(r["status"], (PASS, FAIL, UNKNOWN))
            self.assertTrue(r["limitation"].strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
