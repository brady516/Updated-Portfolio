#!/usr/bin/env python3
"""
provision.py — automate the LookLegit Email setup on Cloudflare.

Turns the ~30-minute dashboard portion of a client setup into one command:
creates the zone (if needed), enables Email Routing, registers the client's
destination inbox, adds the forwarding rule, and writes the SPF + DMARC
records. Prints the two things that still need a human: the nameserver
handoff (if the domain is registered elsewhere) and the client-side Gmail
"send mail as" steps (see runbook.md).

Usage:
    export CF_API_TOKEN="..."       # API token: Zone.Zone + Zone.DNS + Email Routing edit
    export CF_ACCOUNT_ID="..."      # Cloudflare account id (dashboard right sidebar)

    # full setup: route hello@mikesdrywall.com -> mikesdrywall1987@gmail.com
    python3 provision.py setup --domain mikesdrywall.com \
        --address hello --forward-to mikesdrywall1987@gmail.com

    # check an existing setup (records + routing status)
    python3 provision.py check --domain mikesdrywall.com

Notes:
  - Stdlib only. No pip installs.
  - The destination inbox gets a Cloudflare verification email; the CLIENT
    must click it before mail flows. The script tells you when it's pending.
  - Written against the Cloudflare v4 API. If an endpoint errors, the full
    API response is printed so you can see exactly why.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def token() -> str:
    t = os.environ.get("CF_API_TOKEN")
    if not t:
        die("set CF_API_TOKEN (My Profile -> API Tokens; needs Zone + DNS + Email Routing edit)")
    return t


def account_id() -> str:
    a = os.environ.get("CF_ACCOUNT_ID")
    if not a:
        die("set CF_ACCOUNT_ID (found on any zone's Overview page, right sidebar)")
    return a


def call(method: str, path: str, body: dict | None = None) -> dict:
    """One Cloudflare API call; surfaces the full error body on failure."""
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token()}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        die(f"HTTP {e.code} on {method} {path}\n{detail}")
    if not out.get("success", False):
        die(f"API declined {method} {path}\n{json.dumps(out.get('errors'), indent=2)}")
    return out


# ---------------------------------------------------------------- zone

def find_zone(domain: str) -> dict | None:
    out = call("GET", f"/zones?name={domain}")
    hits = out.get("result") or []
    return hits[0] if hits else None


def ensure_zone(domain: str) -> dict:
    z = find_zone(domain)
    if z:
        print(f"zone exists: {domain} (status: {z['status']})")
        return z
    print(f"creating zone: {domain}")
    out = call("POST", "/zones", {"name": domain, "account": {"id": account_id()}})
    return out["result"]


# ---------------------------------------------------------------- dns records

def existing_records(zone_id: str, rtype: str, name: str) -> list[dict]:
    out = call("GET", f"/zones/{zone_id}/dns_records?type={rtype}&name={name}")
    return out.get("result") or []


def ensure_txt(zone_id: str, name: str, content: str, label: str) -> None:
    for rec in existing_records(zone_id, "TXT", name):
        if rec["content"].strip('"') == content:
            print(f"{label}: already present")
            return
    call("POST", f"/zones/{zone_id}/dns_records",
         {"type": "TXT", "name": name, "content": content, "ttl": 1})
    print(f"{label}: added")


# ---------------------------------------------------------------- email routing

def enable_routing(zone_id: str) -> None:
    """Enable Email Routing; Cloudflare adds its own MX + SPF when enabling."""
    status = call("GET", f"/zones/{zone_id}/email/routing")["result"]
    if status.get("enabled"):
        print("email routing: already enabled")
        return
    call("POST", f"/zones/{zone_id}/email/routing/enable", {})
    print("email routing: enabled (Cloudflare added its MX + SPF records)")


def ensure_destination(forward_to: str) -> bool:
    """Register the client's real inbox; returns True when verified."""
    acct = account_id()
    out = call("GET", f"/accounts/{acct}/email/routing/addresses")
    for addr in out.get("result") or []:
        if addr["email"].lower() == forward_to.lower():
            verified = bool(addr.get("verified"))
            print(f"destination {forward_to}: {'verified' if verified else 'PENDING — client must click the Cloudflare verification email'}")
            return verified
    call("POST", f"/accounts/{acct}/email/routing/addresses", {"email": forward_to})
    print(f"destination {forward_to}: created — Cloudflare just emailed a verification link; have the client click it")
    return False


def ensure_rule(zone_id: str, domain: str, address: str, forward_to: str) -> None:
    full = f"{address}@{domain}"
    out = call("GET", f"/zones/{zone_id}/email/routing/rules")
    for rule in out.get("result") or []:
        for m in rule.get("matchers", []):
            if m.get("value", "").lower() == full.lower():
                print(f"route {full}: already exists")
                return
    call("POST", f"/zones/{zone_id}/email/routing/rules", {
        "name": f"LookLegit {full}",
        "enabled": True,
        "matchers": [{"type": "literal", "field": "to", "value": full}],
        "actions": [{"type": "forward", "value": [forward_to]}],
    })
    print(f"route {full} -> {forward_to}: created")


# ---------------------------------------------------------------- commands

SPF = "v=spf1 include:_spf.mx.cloudflare.net include:_spf.google.com ~all"
DMARC = "v=DMARC1; p=none; sp=none; adkim=r; aspf=r"


def cmd_setup(domain: str, address: str, forward_to: str) -> None:
    zone = ensure_zone(domain)
    zone_id = zone["id"]

    enable_routing(zone_id)
    verified = ensure_destination(forward_to)
    ensure_rule(zone_id, domain, address, forward_to)

    # SPF: replace Cloudflare's routing-only record with one that also
    # authorizes Google (outbound "send as" goes through Gmail's SMTP).
    for rec in existing_records(zone_id, "TXT", domain):
        c = rec["content"].strip('"')
        if c.startswith("v=spf1") and "google.com" not in c:
            call("DELETE", f"/zones/{zone_id}/dns_records/{rec['id']}")
            print("SPF: removed routing-only record (replacing with merged one)")
    ensure_txt(zone_id, domain, SPF, "SPF (cloudflare + google)")
    ensure_txt(zone_id, f"_dmarc.{domain}", DMARC, "DMARC (p=none)")

    print("\n---- remaining human steps ----")
    if zone["status"] != "active":
        ns = ", ".join(zone.get("name_servers") or [])
        print(f"1. Point the domain's nameservers to: {ns}")
        print("   (registrar dashboard; zone activates automatically once seen)")
    if not verified:
        print("2. Client clicks the Cloudflare verification email sent to "
              f"{forward_to} — routing will not deliver until then.")
    print("3. 10-minute screenshare: Gmail 'send mail as' (see runbook.md).")
    print(f"4. Test the loop, install the signature, send the cheat sheet. Done.")


def cmd_check(domain: str) -> None:
    zone = find_zone(domain)
    if not zone:
        die(f"no zone for {domain} in this account")
    zone_id = zone["id"]
    print(f"zone status : {zone['status']}")
    routing = call("GET", f"/zones/{zone_id}/email/routing")["result"]
    print(f"routing     : {'enabled' if routing.get('enabled') else 'DISABLED'}")
    mx = call("GET", f"/zones/{zone_id}/dns_records?type=MX")["result"]
    for r in mx:
        print(f"MX          : {r['content']} (prio {r.get('priority')})")
    for r in call("GET", f"/zones/{zone_id}/dns_records?type=TXT")["result"]:
        c = r["content"].strip('"')
        if c.startswith(("v=spf1", "v=DMARC1")):
            print(f"TXT {r['name']}: {c}")
    rules = call("GET", f"/zones/{zone_id}/email/routing/rules")["result"]
    for r in rules:
        for m in r.get("matchers", []):
            if m.get("type") == "literal":
                dests = [v for a in r.get("actions", []) for v in a.get("value", [])]
                print(f"route       : {m.get('value')} -> {', '.join(dests)} "
                      f"({'on' if r.get('enabled') else 'OFF'})")


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="LookLegit Email — Cloudflare provisioning")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("setup", help="full setup for one client domain")
    s.add_argument("--domain", required=True, help="client domain, e.g. mikesdrywall.com")
    s.add_argument("--address", default="hello", help="mailbox name (default: hello)")
    s.add_argument("--forward-to", required=True, help="client's existing inbox (their gmail)")

    c = sub.add_parser("check", help="report the current state of a client domain")
    c.add_argument("--domain", required=True)

    a = p.parse_args()
    if a.cmd == "setup":
        cmd_setup(a.domain.lower(), a.address.lower(), a.forward_to)
    else:
        cmd_check(a.domain.lower())


if __name__ == "__main__":
    main()
