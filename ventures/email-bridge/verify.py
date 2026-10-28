#!/usr/bin/env python3
"""
verify.py — deterministic evidence collection for the quarterly re-verify.

Answers one question per check, from PUBLIC DNS, with no credentials:
what does the outside world currently observe about this domain's mail setup?

This is deliberately NOT `provision.py check`. That one reads the Cloudflare
API — the control plane, i.e. what Cloudflare believes it configured. This one
reads what a sending mail server actually sees. When those two disagree, the
data plane is the one that matters, and only the data plane is evidence.

Every check returns PASS, FAIL or UNKNOWN with a timestamp, the observed
value, the expected value, the raw evidence, and its own limitation. UNKNOWN
is a first-class result: an unreachable registrar or an unconfigured DKIM
selector must never silently become a PASS.

What this tool does NOT do: decide whether the business is functioning.
Correct records are not delivered mail. See the `limitation` on every row.

Usage:
    # no profile — everything that needs an expected value returns UNKNOWN
    python3 verify.py dns --domain mikesdrywall.com

    # with a profile, checks become expected-vs-observed
    python3 verify.py dns --domain mikesdrywall.com --profile mikes.json

    # cross-check two independent resolvers; disagreement -> UNKNOWN
    python3 verify.py dns --domain mikesdrywall.com --profile mikes.json --cross-check

    # write the machine-readable report for the acceptance register
    python3 verify.py dns --domain mikesdrywall.com --json report.json

    # separate adapter, separate command, never auto-judged
    python3 verify.py form --url https://mikesdrywall.com/contact

Profile schema (all keys optional; a missing key yields UNKNOWN, not PASS):
    {
      "mx":            ["route1.mx.cloudflare.net", "route2.mx.cloudflare.net"],
      "spf_includes":  ["_spf.mx.cloudflare.net", "spf.migadu.com"],
      "dkim_selectors":["key1", "key2"],
      "dmarc_policy":  "quarantine",
      "form_url":      "https://mikesdrywall.com/contact"
    }

Exit codes:  0 = all PASS   1 = at least one FAIL   2 = UNKNOWN, no FAIL

Notes:
  - Stdlib only. No pip installs.
  - DNS goes over DNS-over-HTTPS so it works behind an HTTPS proxy and gives
    an auditable HTTP response as evidence. Two independent resolvers are
    available precisely so the result can be corroborated.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"

RESOLVERS = {
    "cloudflare": "https://cloudflare-dns.com/dns-query",
    "google": "https://dns.google/resolve",
}

# RFC 7208 caps SPF at 10 DNS-querying mechanisms.
SPF_LOOKUP_LIMIT = 10
SPF_QUERY_MECHANISMS = ("include:", "a:", "mx:", "ptr:", "exists:", "redirect=")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- dns transport

class Resolver:
    """DNS-over-HTTPS, with fallback across endpoints.

    `auto` tries each endpoint in turn and returns the first that answers.
    A blocked endpoint is not evidence of anything — plenty of home routers
    and security suites drop known DoH hosts because DoH bypasses their
    filtering — so one being unreachable must not turn every record into
    UNKNOWN while another endpoint can still answer. Which endpoint answered,
    and what the failed ones said, is recorded on every row.
    """

    def __init__(self, name: str = "auto", timeout: int = 15):
        if name == "auto":
            self.chain = ["cloudflare", "google"]
        elif name in RESOLVERS:
            self.chain = [name]
        else:
            raise ValueError(f"unknown resolver {name!r}")
        self.name = name
        self.timeout = timeout

    def query(self, name: str, rtype: str) -> dict:
        """Returns {'status', 'records', 'error', 'resolver', 'attempts'}."""
        attempts = []
        for which in self.chain:
            out = self._one(RESOLVERS[which], name, rtype)
            if out["error"] is None:
                out["resolver"] = which
                out["attempts"] = attempts
                return out
            attempts.append({"resolver": which, "error": out["error"]})
        # Every endpoint failed: we learned nothing, which is never a FAIL.
        return {"status": None, "records": [], "resolver": None,
                "error": attempts[-1]["error"], "attempts": attempts}

    def _one(self, url: str, name: str, rtype: str) -> dict:
        qs = urllib.parse.urlencode({"name": name, "type": rtype})
        req = urllib.request.Request(
            f"{url}?{qs}", headers={"accept": "application/dns-json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.load(r)
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            return {"status": None, "records": [], "error": f"{type(e).__name__}: {e}"}

        records = []
        for ans in body.get("Answer") or []:
            # Only keep answers of the type we asked for; CNAME chains appear here too.
            if ans.get("type") == _rtype_num(rtype):
                records.append(_clean(ans.get("data", ""), rtype))
        return {"status": body.get("Status"), "records": records, "error": None}


def _rtype_num(rtype: str) -> int:
    return {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "MX": 15, "TXT": 16}[rtype]


def _clean(data: str, rtype: str) -> str:
    if rtype == "TXT":
        # Long TXT records arrive as adjacent quoted strings; RFC 1035 says
        # they concatenate with no separator. Splitting them loses SPF records.
        return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', data)) or data.strip('"')
    if rtype == "MX":
        return data.strip().rstrip(".").lower()
    return data.strip().rstrip(".")


# ---------------------------------------------------------------- result record

def result(check: str, status: str, observed, expected, evidence, limitation: str) -> dict:
    return {
        "check": check,
        "status": status,
        "checked_at": now(),
        "observed": observed,
        "expected": expected,
        "evidence": evidence,
        "limitation": limitation,
    }


# ---------------------------------------------------------------- group 1: registrar

def check_domain_expiry(domain: str, timeout: int = 15) -> dict:
    """RDAP where the registry serves it; UNKNOWN otherwise. Never inferred."""
    lim = ("DNS alone cannot establish renewal status. An unreachable or "
           "redacted registry yields UNKNOWN, which must be resolved by hand "
           "in the registrar account.")
    url = f"https://rdap.org/domain/{urllib.parse.quote(domain)}"
    try:
        req = urllib.request.Request(url, headers={"accept": "application/rdap+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.load(r)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return result("domain_expiry", UNKNOWN, None, "a future expiry date",
                      {"rdap_url": url, "error": f"{type(e).__name__}: {e}"}, lim)

    expiry = None
    for ev in body.get("events") or []:
        if ev.get("eventAction") in ("expiration", "registrar expiration"):
            expiry = ev.get("eventDate")
            break
    if not expiry:
        return result("domain_expiry", UNKNOWN, None, "a future expiry date",
                      {"rdap_url": url, "note": "no expiration event in RDAP response",
                       "events": body.get("events")}, lim)

    try:
        when = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    except ValueError:
        return result("domain_expiry", UNKNOWN, expiry, "a parseable future date",
                      {"rdap_url": url, "raw": expiry}, lim)

    days = (when - datetime.now(timezone.utc)).days
    status = PASS if days > 30 else FAIL
    return result("domain_expiry", status, {"expires": expiry, "days_left": days},
                  "more than 30 days remaining",
                  {"rdap_url": url, "registrar_events": body.get("events")}, lim)


# ---------------------------------------------------------------- group 2: dns records

def check_mx(domain: str, expected: list | None, res: Resolver) -> dict:
    lim = ("Correct MX records do not prove successful delivery. Only a real "
           "message landing in the inbox proves that (acceptance.md Part 1).")
    q = res.query(domain, "MX")
    ev = {"resolver": q.get("resolver"), "resolver_requested": res.name, "dns_status": q["status"],
          "raw": q["records"], "error": q["error"],
          "resolver_attempts": q.get("attempts")}
    if q["error"] is not None:
        return result("mx", UNKNOWN, None, expected, ev, lim)

    hosts = sorted(r.split(None, 1)[1] for r in q["records"] if " " in r)
    if not hosts:
        return result("mx", FAIL, [], expected or "at least one MX host", ev, lim)
    if expected is None:
        return result("mx", UNKNOWN, hosts,
                      "no expected MX in profile — cannot judge", ev, lim)

    want = sorted(h.rstrip(".").lower() for h in expected)
    return result("mx", PASS if hosts == want else FAIL, hosts, want, ev, lim)


def _spf_records(txts: list) -> list:
    return [t for t in txts if t.lower().startswith("v=spf1")]


def _count_spf_lookups(record: str, res: Resolver, depth: int = 0,
                       seen: set | None = None) -> tuple:
    """Recursively count DNS-querying mechanisms. Returns (count, unresolved)."""
    seen = seen if seen is not None else set()
    count, unresolved = 0, []
    if depth > 3:
        return count, ["include depth exceeded 3; not expanded further"]

    for term in record.split():
        low = term.lower().lstrip("+-~?")
        if not low.startswith(SPF_QUERY_MECHANISMS) and low not in ("a", "mx", "ptr"):
            continue
        count += 1
        target = low.split(":", 1)[1] if ":" in low else (
            low.split("=", 1)[1] if "=" in low else None)
        if not target or not low.startswith(("include:", "redirect=")):
            continue
        if target in seen:
            continue
        seen.add(target)
        sub = res.query(target, "TXT")
        if sub["error"] is not None:
            unresolved.append(f"{target}: {sub['error']}")
            continue
        for inner in _spf_records(sub["records"]):
            c, u = _count_spf_lookups(inner, res, depth + 1, seen)
            count += c
            unresolved.extend(u)
    return count, unresolved


def check_spf(domain: str, expected_includes: list | None, res: Resolver) -> dict:
    lim = ("A published SPF record does not prove every sender is authorized, "
           "and it says nothing about mail forwarded through a third hop, "
           "where SPF alignment breaks by design.")
    q = res.query(domain, "TXT")
    ev = {"resolver": q.get("resolver"), "resolver_requested": res.name, "dns_status": q["status"],
          "raw_txt": q["records"], "error": q["error"],
          "resolver_attempts": q.get("attempts")}
    if q["error"] is not None:
        return result("spf", UNKNOWN, None, expected_includes, ev, lim)

    spf = _spf_records(q["records"])
    if not spf:
        return result("spf", FAIL, None, "exactly one v=spf1 record", ev, lim)
    if len(spf) > 1:
        return result("spf", FAIL, spf,
                      "exactly one v=spf1 record (multiple is a permanent error)",
                      ev, lim)

    record = spf[0]
    lookups, unresolved = _count_spf_lookups(record, res)
    ev["record"] = record
    ev["dns_lookups"] = lookups
    ev["unresolved_includes"] = unresolved

    problems = []
    if not re.search(r"[~\-?+]all\b", record.lower()):
        problems.append("no 'all' mechanism — undefined behaviour for unlisted senders")
    if lookups > SPF_LOOKUP_LIMIT:
        problems.append(f"{lookups} DNS lookups exceeds the RFC 7208 limit of "
                        f"{SPF_LOOKUP_LIMIT}; receivers may return permerror")

    missing = []
    if expected_includes:
        missing = [i for i in expected_includes if i.lower() not in record.lower()]
        if missing:
            problems.append(f"expected includes absent: {missing}")

    if problems:
        return result("spf", FAIL, {"record": record, "lookups": lookups,
                                    "problems": problems},
                      expected_includes or "syntactically valid, within lookup limit",
                      ev, lim)
    if unresolved:
        # Syntax is fine but we could not finish counting — do not claim PASS.
        return result("spf", UNKNOWN, {"record": record, "lookups_counted": lookups},
                      "complete lookup count", ev, lim)
    if expected_includes is None:
        return result("spf", UNKNOWN, {"record": record, "lookups": lookups},
                      "no expected includes in profile — syntax checked only",
                      ev, lim)
    return result("spf", PASS, {"record": record, "lookups": lookups},
                  expected_includes, ev, lim)


def check_dkim(domain: str, selectors: list | None, res: Resolver) -> dict:
    lim = ("A published public key does not prove outgoing mail is signed or "
           "that signatures verify. Only inspecting Authentication-Results on "
           "a real received message proves that.")
    if not selectors:
        return result("dkim", UNKNOWN, None,
                      "selector list in profile — without it DKIM cannot be checked",
                      {"note": "no dkim_selectors configured; this is not a pass"}, lim)

    found, missing, ev = {}, [], {"resolver": res.name, "queries": {}}
    for sel in selectors:
        name = f"{sel}._domainkey.{domain}"
        q = res.query(name, "TXT")
        ev["queries"][name] = {"dns_status": q["status"], "raw": q["records"],
                               "error": q["error"],
                               "resolver": q.get("resolver"),
                               "resolver_attempts": q.get("attempts")}
        if q["error"] is not None:
            return result("dkim", UNKNOWN, None, selectors, ev, lim)
        keys = [t for t in q["records"]
                if "v=dkim1" in t.lower() and re.search(r"\bp=[A-Za-z0-9+/=]+", t)]
        if keys:
            found[sel] = keys[0][:60] + "..."
        else:
            missing.append(sel)

    if missing:
        return result("dkim", FAIL, {"published": list(found), "missing": missing},
                      selectors, ev, lim)
    return result("dkim", PASS, {"published": list(found)}, selectors, ev, lim)


def check_dmarc(domain: str, expected_policy: str | None, res: Resolver) -> dict:
    lim = ("p=none is monitoring, not enforcement. A published DMARC record "
           "with p=none blocks nothing and should not be read as protection.")
    name = f"_dmarc.{domain}"
    q = res.query(name, "TXT")
    ev = {"resolver": q.get("resolver"), "resolver_requested": res.name, "dns_status": q["status"],
          "raw_txt": q["records"], "error": q["error"],
          "resolver_attempts": q.get("attempts")}
    if q["error"] is not None:
        return result("dmarc", UNKNOWN, None, expected_policy, ev, lim)

    recs = [t for t in q["records"] if t.lower().startswith("v=dmarc1")]
    if not recs:
        return result("dmarc", FAIL, None, "a v=DMARC1 record", ev, lim)
    if len(recs) > 1:
        return result("dmarc", FAIL, recs, "exactly one v=DMARC1 record", ev, lim)

    tags = {}
    for part in recs[0].split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            tags[k.strip().lower()] = v.strip()
    policy = tags.get("p", "").lower()
    observed = {"policy": policy, "subdomain_policy": tags.get("sp"),
                "pct": tags.get("pct", "100"), "rua": tags.get("rua"),
                "enforcing": policy in ("quarantine", "reject"),
                "record": recs[0]}
    ev["tags"] = tags

    if not policy:
        return result("dmarc", FAIL, observed, "a p= tag", ev, lim)
    if expected_policy is None:
        return result("dmarc", UNKNOWN, observed,
                      "no dmarc_policy in profile — record parsed, not judged", ev, lim)
    status = PASS if policy == expected_policy.lower() else FAIL
    return result("dmarc", status, observed, f"p={expected_policy}", ev, lim)


# ---------------------------------------------------------------- group 3: form adapter

def check_form(url: str, timeout: int = 20) -> dict:
    """Observation only. A displayed address never establishes delivery."""
    lim = ("A displayed address and a form action do not establish where "
           "submissions arrive. Only a controlled end-to-end submission with "
           "a unique token, confirmed in the destination mailbox, does. This "
           "check cannot return PASS by design.")
    ev = {"url": url}
    try:
        req = urllib.request.Request(url, headers={"user-agent": "go-legit-local-verify/1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ev["http_status"] = r.status
            html = r.read(400_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as e:
        ev["error"] = f"{type(e).__name__}: {e}"
        return result("form_destination", UNKNOWN, None,
                      "page reachable for inspection", ev, lim)

    actions = re.findall(r"<form[^>]*\baction\s*=\s*[\"']([^\"']+)", html, re.I)
    mailtos = re.findall(r"mailto:([^\"'?\s>]+)", html, re.I)
    addrs = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", html)
    freemail = sorted({a for a in addrs
                       if a.split("@")[-1].lower() in
                       ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                        "aol.com", "icloud.com", "msn.com", "live.com")})

    ev.update({"form_actions": actions, "mailto_links": sorted(set(mailtos)),
               "addresses_on_page": sorted(set(addrs))})
    observed = {"form_actions": actions, "freemail_addresses_visible": freemail}

    # A visible freemail address is a definite finding — the old identity is
    # still published. Everything else stays UNKNOWN pending the live test.
    if freemail:
        return result("form_destination", FAIL, observed,
                      "no freemail address published on the page", ev, lim)
    return result("form_destination", UNKNOWN, observed,
                  "controlled submission test, confirmed in the destination mailbox",
                  ev, lim)


# ---------------------------------------------------------------- reporting

def cross_check(primary: list, domain: str, profile: dict, other: str) -> list:
    """Corroborate against one named endpoint — not the fallback chain, or the
    two runs could silently land on the same resolver and prove nothing."""
    """Re-run the DNS checks on a second resolver; disagreement -> UNKNOWN."""
    res = Resolver(other)
    second = {r["check"]: r for r in _dns_checks(domain, profile, res)}
    out = []
    for row in primary:
        peer = second.get(row["check"])
        if peer and peer["status"] != row["status"]:
            row = dict(row)
            row["status"] = UNKNOWN
            row["evidence"] = {
                "disagreement": True,
                "note": "independent resolvers disagree; propagation may be in "
                        "flight. Re-check before recording.",
                "primary": row["evidence"],
                f"{other}": peer["evidence"],
                f"{other}_status": peer["status"],
            }
        out.append(row)
    return out


def _dns_checks(domain: str, profile: dict, res: Resolver) -> list:
    return [
        check_mx(domain, profile.get("mx"), res),
        check_spf(domain, profile.get("spf_includes"), res),
        check_dkim(domain, profile.get("dkim_selectors"), res),
        check_dmarc(domain, profile.get("dmarc_policy"), res),
    ]


def render(report: dict) -> None:
    w = max(len(r["check"]) for r in report["checks"])
    print(f"\ndomain   : {report['domain']}")
    print(f"checked  : {report['checked_at']}  (resolver: {report['resolver']})")
    print(f"profile  : {report['profile'] or 'NONE — expected values unavailable'}\n")
    for r in report["checks"]:
        print(f"  {r['status']:<8} {r['check']:<{w}}  {json.dumps(r['observed'])}")
        if r["status"] != PASS:
            print(f"           {' ' * w}  expected: {json.dumps(r['expected'])}")
    # Distinguish "one endpoint was blocked and another answered" from
    # "nothing answered" — the second is why rows came back UNKNOWN.
    skipped, dead = set(), set()
    for r in report["checks"]:
        ev = r["evidence"]
        attempts = [a for a in (ev.get("resolver_attempts") or [])
                    if isinstance(a, dict) and a.get("resolver")]
        if not attempts:
            continue
        (skipped if ev.get("resolver") else dead).update(
            a["resolver"] for a in attempts)
    if skipped:
        print(f"\n  note: {', '.join(sorted(skipped))} unreachable from this "
              f"machine; a fallback endpoint answered instead.")
    if dead:
        print(f"\n  note: no DNS endpoint answered ({', '.join(sorted(dead))} all "
              f"failed), which is why rows above are UNKNOWN rather than clean. "
              f"See resolver_attempts in the JSON.")
    c = report["summary"]
    print(f"\n  {c[PASS]} pass, {c[FAIL]} fail, {c[UNKNOWN]} unknown")
    if c[UNKNOWN]:
        print("  UNKNOWN is not a pass. Resolve each one by hand before signing off.")
    print()


def finish(report: dict, json_path: str | None) -> int:
    counts = {PASS: 0, FAIL: 0, UNKNOWN: 0}
    for r in report["checks"]:
        counts[r["status"]] += 1
    report["summary"] = counts
    if json_path:
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"wrote {json_path}")
    render(report)
    return 1 if counts[FAIL] else (2 if counts[UNKNOWN] else 0)


# ---------------------------------------------------------------- cli

def main() -> int:
    p = argparse.ArgumentParser(
        description="Go Legit Local — deterministic verification evidence")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dns", help="registrar + DNS record checks")
    d.add_argument("--domain", required=True)
    d.add_argument("--profile", help="JSON file of expected values")
    d.add_argument("--resolver", default="auto",
                   choices=["auto"] + sorted(RESOLVERS),
                   help="auto (default) tries each endpoint until one answers")
    d.add_argument("--cross-check", action="store_true",
                   help="corroborate with a second resolver; disagreement -> UNKNOWN")
    d.add_argument("--json", dest="json_path", help="write the report here")

    f = sub.add_parser("form", help="inspect a contact page (observation only)")
    f.add_argument("--url", required=True)
    f.add_argument("--json", dest="json_path")

    a = p.parse_args()

    if a.cmd == "form":
        return finish({"domain": urllib.parse.urlparse(a.url).netloc,
                       "checked_at": now(), "resolver": "n/a", "profile": None,
                       "checks": [check_form(a.url)]}, a.json_path)

    profile = {}
    if a.profile:
        if not os.path.exists(a.profile):
            print(f"ERROR: no such profile: {a.profile}", file=sys.stderr)
            return 1
        with open(a.profile) as fh:
            profile = json.load(fh)

    domain = a.domain.lower().rstrip(".")
    res = Resolver(a.resolver)
    checks = [check_domain_expiry(domain)] + _dns_checks(domain, profile, res)
    if a.cross_check:
        other = "google" if a.resolver in ("cloudflare", "auto") else "cloudflare"
        checks = checks[:1] + cross_check(checks[1:], domain, profile, other)

    return finish({"domain": domain, "checked_at": now(), "resolver": a.resolver,
                   "profile": a.profile, "checks": checks}, a.json_path)


if __name__ == "__main__":
    sys.exit(main())
