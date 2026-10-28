#!/usr/bin/env python3
"""
test_plainreport.py — guards on the owner-facing language.

These are not cosmetic. The whole point of the artifact is that the buyer can
read it, and the three rules it rests on are easy to break by accident the next
time someone adds a check.

Usage:  python3 test_plainreport.py
"""

import json
import unittest

import plainreport
from plainreport import BROKEN, UNANSWERED, WORKING

# Every acronym and insider term that must never reach the owner-facing text.
BANNED_TERMS = ["dmarc", "spf", "dkim", " mx", "dns", " txt", "nxdomain",
                "rdap", "selector", "p=none", "record type", "resolver",
                "api", "json", "ttl"]

# Claims the tool cannot establish and must therefore never make.
BANNED_CLAIMS = ["landing in spam", "going to spam", "your mail is failing",
                 "your email is failing", "is being blocked", "you are losing",
                 "guaranteed", "hackers"]


def row(check, status, observed=None):
    return {"check": check, "status": status, "observed": observed,
            "expected": None, "evidence": {}, "limitation": "x"}


def doc_for(checks, business="Mike's Drywall"):
    return plainreport.build(
        {"domain": "mikesdrywall.com", "checked_at": "2026-10-28T01:39:29+00:00",
         "checks": checks}, business)


ALL_STATES = [
    row("domain_expiry", "PASS", {"expires": "2028-07-06T12:01:08Z", "days_left": 617}),
    row("domain_expiry", "FAIL", {"expires": "2026-11-01T00:00:00Z", "days_left": 4}),
    row("domain_expiry", "UNKNOWN"),
    row("mx", "PASS", ["route1.mx.cloudflare.net"]),
    row("mx", "FAIL", []),
    row("mx", "UNKNOWN"),
    row("spf", "PASS", {"record": "v=spf1 -all", "lookups": 1}),
    row("spf", "FAIL", {"record": "v=spf1 -all", "problems": ["expected includes absent: ['x']"]}),
    row("spf", "FAIL", {"record": "v=spf1", "problems": ["no 'all' mechanism"]}),
    row("spf", "FAIL", None),
    row("spf", "UNKNOWN", {"record": "v=spf1 -all", "lookups": 1}),
    row("spf", "UNKNOWN"),
    row("dkim", "PASS", {"published": ["key1"]}),
    row("dkim", "FAIL", {"published": [], "missing": ["key1"]}),
    row("dkim", "UNKNOWN"),
    row("dmarc", "PASS", {"policy": "reject", "enforcing": True}),
    row("dmarc", "PASS", {"policy": "none", "enforcing": False}),
    row("dmarc", "FAIL", {"policy": "none", "enforcing": False}),
    row("dmarc", "FAIL", None),
    row("dmarc", "UNKNOWN"),
    row("form_destination", "FAIL", {"freemail_addresses_visible": ["mike1987@gmail.com"]}),
    row("form_destination", "UNKNOWN", {"form_actions": ["/submit"]}),
]


class TestNoJargonReachesTheOwner(unittest.TestCase):
    """Rule 1. He does not know what DMARC is and should not have to."""

    def test_no_banned_term_in_any_heading_or_body(self):
        for r in ALL_STATES:
            _, heading, body = plainreport._plain(r)
            text = f" {heading} {body} ".lower()
            for term in BANNED_TERMS:
                self.assertNotIn(term, text,
                                 f"{r['check']}/{r['status']} leaked {term!r}")

    def test_rendered_text_body_is_clean(self):
        doc = doc_for(ALL_STATES)
        body = plainreport.render_text(doc).lower()
        for term in BANNED_TERMS:
            self.assertNotIn(term, body)

    def test_html_appendix_may_contain_jargon_but_the_body_may_not(self):
        doc = doc_for(ALL_STATES)
        page = plainreport.render_html(doc)
        owner_half = page.split('class="appendix"')[0].lower()
        for term in BANNED_TERMS:
            self.assertNotIn(term, owner_half)
        # the appendix is where the detail belongs, and it must survive
        self.assertIn("dmarc", page.lower())


class TestNoUnprovableClaims(unittest.TestCase):
    """Rule 2. Nothing here can establish that his mail is failing."""

    def test_no_banned_claim_anywhere_in_the_owner_text(self):
        doc = doc_for(ALL_STATES)
        text = plainreport.render_text(doc).lower()
        for claim in BANNED_CLAIMS:
            self.assertNotIn(claim, text)

    def test_bottom_line_disclaims_before_it_sells(self):
        doc = doc_for([row("dmarc", "FAIL", None)])
        self.assertIn("none of this proves", doc["bottom_line"].lower())

    def test_clean_report_gets_a_different_bottom_line(self):
        doc = doc_for([row("dmarc", "PASS", {"policy": "reject", "enforcing": True}),
                       row("mx", "PASS", ["a.example.com"])])
        self.assertNotIn("none of this proves", doc["bottom_line"].lower())


class TestUnknownIsSaidOutLoud(unittest.TestCase):
    """Rule 3. UNKNOWN is never omitted and never softened into a pass."""

    def test_every_unknown_says_it_could_not_be_checked_or_confirmed(self):
        for check in ("domain_expiry", "mx", "spf", "form_destination"):
            _, heading, body = plainreport._plain(row(check, "UNKNOWN"))
            self.assertRegex((heading + " " + body).lower(),
                             r"could not|cannot|not confirmed|do not know")

    def test_unknown_is_never_badged_as_working(self):
        for check in ("domain_expiry", "spf", "form_destination"):
            sev, _, _ = plainreport._plain(row(check, "UNKNOWN"))
            self.assertNotEqual(sev, WORKING, check)

    def test_html_explains_not_answered_is_not_a_pass(self):
        page = plainreport.render_html(doc_for(ALL_STATES)).lower()
        self.assertIn("not a pass", page)

    def test_monitoring_only_dmarc_is_not_shown_as_working(self):
        """p=none passes the technical check but protects nothing."""
        sev, heading, body = plainreport._plain(
            row("dmarc", "PASS", {"policy": "none", "enforcing": False}))
        self.assertEqual(sev, UNANSWERED)
        self.assertIn("not", (heading + body).lower())


class TestOrderingAndCoverage(unittest.TestCase):
    def test_broken_items_sort_first(self):
        doc = doc_for([row("mx", "PASS", ["a.example.com"]),
                       row("dmarc", "FAIL", None)])
        self.assertEqual(doc["rows"][0][0], BROKEN)

    def test_every_check_verify_emits_has_a_translation(self):
        import verify
        for check in ("domain_expiry", "mx", "spf", "dkim", "dmarc",
                      "form_destination"):
            for status in (verify.PASS, verify.FAIL, verify.UNKNOWN):
                _, heading, body = plainreport._plain(row(check, status))
                self.assertNotIn("not translated", heading,
                                 f"{check}/{status} has no plain-language entry")
                self.assertTrue(body.strip())

    def test_business_name_is_used_verbatim(self):
        doc = doc_for([row("mx", "PASS", ["a.example.com"])], "Mike's Drywall & Son")
        self.assertIn("Mike's Drywall & Son", plainreport.render_text(doc))
        self.assertIn("Mike&#x27;s Drywall &amp; Son", plainreport.render_html(doc))

    def test_falls_back_to_domain_when_no_business_name(self):
        doc = plainreport.build(
            {"domain": "mikesdrywall.com", "checked_at": "2026-10-28T01:39:29+00:00",
             "checks": [row("mx", "PASS", ["a.example.com"])]}, None)
        self.assertEqual(doc["business"], "mikesdrywall.com")


if __name__ == "__main__":
    unittest.main(verbosity=2)
