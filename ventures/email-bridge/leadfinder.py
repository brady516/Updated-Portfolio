#!/usr/bin/env python3
"""
leadfinder.py — find tradespeople still running their business on a freemail
address (gmail/yahoo/hotmail/...). Those are Go Legit Local leads.

Two-step, ToS-clean pipeline:

  1. `places`  — query the OFFICIAL Google Places API (Text Search) for a trade
                 + city, collecting business name / address / phone / website.
                 This is Google's sanctioned door; scraping Maps or Search
                 results directly is against their ToS, so we don't.
  2. `harvest` — visit each business's OWN public website (robots.txt
                 respected, rate-limited, identified user-agent) and read the
                 contact email they published. A freemail address = a lead.
                 A you@theirdomain.com address = already professional, skip.

Output is CSV — opens directly in Google Sheets or Excel.

Usage:
    # step 1: build the target list (needs a Places API key)
    export PLACES_API_KEY="..."
    python3 leadfinder.py places -q "drywall contractor in Toledo, OH" \
        -q "drywall contractor in Ann Arbor, MI" -o targets.csv

    # step 2: harvest emails from the businesses' own sites
    python3 leadfinder.py harvest -i targets.csv -o leads.csv --leads-only

    # or harvest from a plain list of site URLs you collected yourself
    python3 leadfinder.py harvest -i urls.txt -o leads.csv

Stdlib only. Be a polite guest: identified UA, robots.txt honored, one site
touched every couple of seconds. Outreach to the resulting list is EMAIL under
CAN-SPAM rules — never cold SMS (TCPA). See leadgen.md.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = "GoLegitLocalLeadFinder/1.0 (small-business outreach; contact: hello@golegitlocal.com)"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ("places.displayName,places.formattedAddress,"
              "places.nationalPhoneNumber,places.websiteUri,nextPageToken")

# The inversion that makes this tool: freemail = LEAD, own-domain = disqualified.
FREEMAIL = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "me.com", "mac.com", "msn.com", "live.com", "ymail.com",
    "rocketmail.com", "att.net", "sbcglobal.net", "bellsouth.net",
    "comcast.net", "verizon.net", "cox.net", "charter.net", "earthlink.net",
    "juno.com", "frontier.com", "windstream.net", "centurylink.net",
    "gmx.com", "mail.com", "protonmail.com", "proton.me",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# obvious non-contact junk that matches the email regex inside HTML/JS
JUNK_HINTS = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".gif",
              ".webp", ".svg", "schema.org", "yourdomain", "youremail",
              "domain.com", "email.com", "@sentry", "no-reply", "noreply")

CONTACT_LINK_RE = re.compile(r'href=["\']([^"\']*contact[^"\']*)["\']', re.I)


def fetch(url: str, timeout: int = 15, max_bytes: int = 600_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(max_bytes).decode("utf-8", errors="replace")


# ---------------------------------------------------------------- places

def places_search(query: str, api_key: str, max_pages: int = 3) -> list[dict]:
    """Official Places Text Search; up to ~60 results per query."""
    results, token = [], None
    for _ in range(max_pages):
        body = {"textQuery": query}
        if token:
            body["pageToken"] = token
        req = urllib.request.Request(
            PLACES_URL,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "X-Goog-Api-Key": api_key,
                     "X-Goog-FieldMask": FIELD_MASK},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.load(r)
        except urllib.error.HTTPError as e:
            print(f"  Places API error {e.code}: {e.read().decode(errors='replace')[:400]}",
                  file=sys.stderr)
            break
        for p in out.get("places", []):
            results.append({
                "business": p.get("displayName", {}).get("text", ""),
                "address": p.get("formattedAddress", ""),
                "phone": p.get("nationalPhoneNumber", ""),
                "website": p.get("websiteUri", ""),
                "query": query,
            })
        token = out.get("nextPageToken")
        if not token:
            break
        time.sleep(2)  # token needs a beat before it's valid
    return results


def cmd_places(queries: list[str], out_path: str) -> None:
    key = os.environ.get("PLACES_API_KEY")
    if not key:
        sys.exit("set PLACES_API_KEY (Google Cloud console -> Places API (New); "
                 "has a monthly free tier)")
    rows, seen = [], set()
    for q in queries:
        print(f"searching: {q}")
        for row in places_search(q, key):
            dedupe = (row["business"].lower(), row["address"].lower())
            if dedupe in seen:
                continue
            seen.add(dedupe)
            rows.append(row)
        time.sleep(1)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["business", "address", "phone", "website", "query"])
        w.writeheader()
        w.writerows(rows)
    no_site = sum(1 for r in rows if not r["website"])
    print(f"\n{len(rows)} businesses -> {out_path}")
    print(f"note: {no_site} have NO website at all — that's a different (bigger) "
          f"upsell conversation; they're kept in the file.")


# ---------------------------------------------------------------- harvest

def clean_emails(html: str) -> set[str]:
    found = set()
    for m in EMAIL_RE.findall(html):
        low = m.lower().strip(".")
        if any(j in low for j in JUNK_HINTS):
            continue
        found.add(low)
    return found


def contact_pages(base: str, html: str, limit: int = 2) -> list[str]:
    urls, seen = [], set()
    for href in CONTACT_LINK_RE.findall(html):
        full = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(full).netloc != urllib.parse.urlparse(base).netloc:
            continue
        if full not in seen:
            seen.add(full)
            urls.append(full)
        if len(urls) >= limit:
            break
    return urls


def robots_ok(base: str) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urllib.parse.urljoin(base, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        rp.allow_all = True  # unreadable robots -> default permissive, stay polite anyway
    return rp


def harvest_site(website: str) -> tuple[set[str], str]:
    """Return (emails, error). Scans homepage + up to 2 contact-ish pages."""
    if not website.startswith(("http://", "https://")):
        website = "https://" + website
    base = website
    rp = robots_ok(base)
    emails: set[str] = set()
    pages = [base]
    try:
        if not rp.can_fetch(UA, base):
            return emails, "robots.txt disallows"
        html = fetch(base)
        emails |= clean_emails(html)
        pages = contact_pages(base, html)
    except Exception as e:
        return emails, f"{type(e).__name__}: {e}"
    for url in pages:
        if not rp.can_fetch(UA, url):
            continue
        time.sleep(1)
        try:
            emails |= clean_emails(fetch(url))
        except Exception:
            continue
    return emails, ""


def classify(email: str, website: str) -> str:
    dom = email.split("@", 1)[1]
    site_dom = urllib.parse.urlparse(
        website if website.startswith("http") else "https://" + website
    ).netloc.lower().removeprefix("www.")
    if dom in FREEMAIL:
        return "LEAD"
    if site_dom and (dom == site_dom or dom.endswith("." + site_dom)):
        return "already-pro"
    return "other-domain"


def read_targets(path: str) -> list[dict]:
    """Accept the places CSV, any CSV with a website column, or a plain URL list."""
    rows = []
    with open(path, newline="") as f:
        head = f.read(4096)
        f.seek(0)
        if "," in head.splitlines()[0] and "website" in head.splitlines()[0].lower():
            for r in csv.DictReader(f):
                r = {k.lower(): (v or "").strip() for k, v in r.items()}
                if r.get("website"):
                    rows.append(r)
        else:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    rows.append({"business": "", "phone": "", "website": line})
    return rows


def cmd_harvest(in_path: str, out_path: str, delay: float, leads_only: bool) -> None:
    targets = read_targets(in_path)
    print(f"{len(targets)} sites to scan (delay {delay}s between sites)\n")
    out_rows = []
    for i, t in enumerate(targets, 1):
        site = t["website"]
        emails, err = harvest_site(site)
        status = err or f"{len(emails)} email(s)"
        print(f"[{i}/{len(targets)}] {site} — {status}")
        if err and not emails:
            out_rows.append({**base_row(t), "email": "", "status": f"error: {err}"})
        for e in sorted(emails):
            out_rows.append({**base_row(t), "email": e, "status": classify(e, site)})
        time.sleep(delay)

    if leads_only:
        out_rows = [r for r in out_rows if r["status"] == "LEAD"]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["business", "phone", "website", "email", "status"])
        w.writeheader()
        w.writerows(out_rows)
    leads = sum(1 for r in out_rows if r["status"] == "LEAD")
    print(f"\n{len(out_rows)} rows -> {out_path}  |  {leads} LEADS (freemail businesses)")


def base_row(t: dict) -> dict:
    return {"business": t.get("business", ""), "phone": t.get("phone", ""),
            "website": t.get("website", "")}


# ---------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description="Go Legit Local lead finder")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("places", help="build target list via official Google Places API")
    s.add_argument("-q", "--query", action="append", required=True,
                   help='e.g. "drywall contractor in Toledo, OH" (repeatable)')
    s.add_argument("-o", "--out", default="targets.csv")

    h = sub.add_parser("harvest", help="scan businesses' own sites for contact emails")
    h.add_argument("-i", "--infile", required=True, help="targets.csv or a plain URL list")
    h.add_argument("-o", "--out", default="leads.csv")
    h.add_argument("--delay", type=float, default=2.0, help="seconds between sites")
    h.add_argument("--leads-only", action="store_true", help="write only freemail LEAD rows")

    a = p.parse_args()
    if a.cmd == "places":
        cmd_places(a.query, a.out)
    else:
        cmd_harvest(a.infile, a.out, a.delay, a.leads_only)


if __name__ == "__main__":
    main()
