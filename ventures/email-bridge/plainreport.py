#!/usr/bin/env python3
"""
plainreport.py — turns a verify.py report into something the business owner reads.

Same discipline as salad-scout/translate.py: a deterministic glossary, plain
English, and no invented claims. A dictionary can't make something up; it can
only describe what was actually observed.

verify.py's output is evidence for the operator — PASS/FAIL/UNKNOWN, raw
records, exit codes. That is the wrong artifact to put in front of a drywall
contractor. He does not know what DMARC is and should not have to.

Three rules, enforced by tests:

  1. No acronyms in the owner-facing text. No DMARC, SPF, DKIM, MX, DNS, TXT.
     Those live in the technical appendix, for whoever fixes it.
  2. Never claim his mail is failing. Nothing here can establish that. Say what
     is published, what isn't, and what nobody can tell him as a result.
  3. UNKNOWN is said out loud, in his language: "we could not check this."
     Never omitted, never softened into a pass.

Usage:
    python3 verify.py dns --domain mikesdrywall.com --json baseline.json
    python3 plainreport.py --from baseline.json --business "Mike's Drywall"
    python3 plainreport.py --from baseline.json --business "Mike's Drywall" --html report.html
"""

import argparse
import html
import json
import sys

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"

# Severity drives the order on the page: what's broken, then what's unanswered,
# then what's fine. He reads the top third and stops.
BROKEN, UNANSWERED, WORKING = 0, 1, 2
BADGE = {BROKEN: "Needs fixing", UNANSWERED: "Not answered", WORKING: "Working"}


def _plain(row: dict) -> tuple:
    """(severity, heading, body) in the owner's language. Observation only."""
    check, status, obs = row["check"], row["status"], row["observed"]

    if check == "domain_expiry":
        if status == PASS and isinstance(obs, dict):
            days = obs.get("days_left")
            return (WORKING, "Your name is paid up",
                    f"You own your business name on the internet through "
                    f"{str(obs.get('expires', ''))[:10]} — about {days} days. "
                    f"If it ever lapses, your website and your email both stop "
                    f"the same day.")
        if status == FAIL and isinstance(obs, dict):
            return (BROKEN, "Your name is about to lapse",
                    f"You own your business name on the internet for only about "
                    f"{obs.get('days_left')} more days. When it lapses, your "
                    f"website and your email both stop. Renew it now.")
        return (UNANSWERED, "We could not confirm your renewal date",
                "The registry did not answer, so we do not know when your "
                "business name comes up for renewal. Check the account you "
                "bought it from. This is not a pass — it is a blank.")

    if check == "mx":
        if status == PASS or (status == UNKNOWN and obs):
            return (WORKING, "Mail sent to you is being delivered",
                    "There is a working path for mail addressed to your "
                    "business, and it is pointed at a real service.")
        if status == FAIL:
            return (BROKEN, "Nothing is set up to receive your mail",
                    "Mail sent to your business address has nowhere to go. "
                    "Anyone writing to you is getting a bounce, or nothing.")
        return (UNANSWERED, "We could not check how your mail is received",
                "No answer came back. We do not know whether mail addressed "
                "to your business reaches you.")

    if check == "spf":
        if status == FAIL and isinstance(obs, dict):
            probs = obs.get("problems") or []
            if any("absent" in p for p in probs):
                return (BROKEN, "Your approved-sender list is missing the "
                                "service you send through",
                        "Your business name carries a list of which mail "
                        "services are allowed to send on your behalf. The "
                        "service your mail actually goes through is not on it. "
                        "Receiving systems check that list.")
            return (BROKEN, "Your approved-sender list has a problem",
                    "Your business name carries a list of which mail services "
                    "are allowed to send on your behalf. It is there, but it is "
                    "not valid, so a receiving system cannot rely on it.")
        if status == FAIL:
            return (BROKEN, "You have no approved-sender list",
                    "Nothing on your business name says which mail services are "
                    "allowed to send on your behalf. A receiving system has "
                    "nothing to check against.")
        if status == PASS:
            return (WORKING, "Your approved-sender list is correct",
                    "Your business name says which services may send on your "
                    "behalf, and the service you use is on the list.")
        if isinstance(obs, dict) and obs.get("record"):
            return (UNANSWERED, "You have an approved-sender list, but we "
                                "cannot confirm it is complete",
                    "The list exists and is readable. We have not confirmed "
                    "that it covers every service your mail goes through.")
        return (UNANSWERED, "We could not check your approved-sender list",
                "No answer came back. We do not know what your business name "
                "publishes about who may send for you.")

    if check == "dkim":
        if status == PASS:
            return (WORKING, "Your mail is being signed",
                    "Mail leaving your business carries a signature that proves "
                    "it really came from you and was not altered on the way.")
        if status == FAIL:
            return (BROKEN, "Your mail is not being signed",
                    "A signature is how a receiving system confirms a message "
                    "really came from your business. Yours is set up but not "
                    "publishing properly, so there is nothing to confirm.")
        return (BROKEN, "Nothing is signing your mail",
                "A signature is how a receiving system confirms a message "
                "really came from your business and was not altered on the way. "
                "Yours has none, so there is nothing for anyone to check.")

    if check == "dmarc":
        if status == PASS and isinstance(obs, dict) and obs.get("enforcing"):
            return (WORKING, "You have instructions in place for fake mail",
                    "If someone sends mail pretending to be your business, "
                    "receiving systems have your instructions on what to do "
                    "with it.")
        if status == PASS:
            return (UNANSWERED, "You are watching, but not protecting",
                    "You have a record in place, but it only asks for reports. "
                    "It does not tell anyone to stop mail that is pretending to "
                    "be you. It is a smoke alarm with nobody home.")
        if isinstance(obs, dict) and obs.get("policy"):
            return (BROKEN, "Your instructions for fake mail do not match what "
                            "you intended",
                    "You have a record in place, but it says something different "
                    "from what was meant to be set.")
        return (BROKEN, "Nothing protects your name from being used by someone "
                        "else",
                "Right now nothing on your business name tells email providers "
                "what to do with messages that only claim to be from you. "
                "Anyone can put your business name on an email and a receiving "
                "system has no instruction to follow. You also get no reports "
                "back, so if one of your quotes goes missing, there is no "
                "record anywhere of what happened to it.")

    if check == "form_destination":
        if status == FAIL and isinstance(obs, dict):
            addrs = obs.get("freemail_addresses_visible") or []
            shown = addrs[0] if addrs else "a free email address"
            return (BROKEN, "Your website still shows a free email address",
                    f"Your contact page publishes {shown}. Every customer who "
                    f"looks you up sees it, whatever your email now says.")
        return (UNANSWERED, "We could not confirm where your contact form goes",
                "Looking at the page cannot establish where a submission "
                "actually lands. The only way to know is to fill the form in "
                "and watch for it to arrive.")

    return (UNANSWERED, f"{check}: not translated",
            "This check has no plain-language entry yet.")


BOTTOM_LINE_BROKEN = (
    "None of this proves an email of yours has failed. It proves that nothing "
    "is published, nobody is authorized, and nobody is measuring. If a quote "
    "goes missing, there is currently no way for you or anyone else to find "
    "out why."
)
BOTTOM_LINE_CLEAN = (
    "Everything we could check is in order, and the report above is dated. "
    "Keep it. If something changes later, this is what it changed from."
)


def build(report: dict, business: str | None) -> dict:
    rows = sorted((_plain(r) for r in report["checks"]), key=lambda t: t[0])
    worst = rows[0][0] if rows else WORKING
    return {
        "business": business or report.get("domain", ""),
        "domain": report.get("domain", ""),
        "checked_at": report.get("checked_at", ""),
        "rows": rows,
        "bottom_line": BOTTOM_LINE_BROKEN if worst == BROKEN else BOTTOM_LINE_CLEAN,
        "appendix": report["checks"],
    }


def render_text(doc: dict) -> str:
    out = [f"\n{doc['business']} — what your email looks like from the outside",
           f"{doc['domain']} · checked {doc['checked_at'][:16].replace('T', ' ')} UTC",
           ""]
    for sev, heading, body in doc["rows"]:
        out.append(f"[{BADGE[sev]}] {heading}")
        for line in _wrap(body, 74):
            out.append(f"    {line}")
        out.append("")
    out.append("The bottom line")
    out.extend("  " + l for l in _wrap(doc["bottom_line"], 74))
    out.append("")
    return "\n".join(out)


def _wrap(text: str, width: int) -> list:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


CSS = """
:root{--ink:#111;--muted:#555;--line:#e5e5e5;--bad:#b4232c;--open:#8a6d1f;--ok:#1f6f43;--bg:#fff}
@media print{.appendix{page-break-before:always}}
*{box-sizing:border-box}
body{margin:0;padding:40px 24px;background:var(--bg);color:var(--ink);
 font:16px/1.6 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:660px;margin:0 auto}
h1{font-size:26px;line-height:1.25;margin:0 0 6px}
.meta{color:var(--muted);font-size:14px;margin:0 0 32px}
.item{border-top:1px solid var(--line);padding:20px 0}
.badge{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
 font-weight:700;padding:3px 8px;border-radius:3px;margin-bottom:8px}
.b0{background:#fdecee;color:var(--bad)}
.b1{background:#fcf4e0;color:var(--open)}
.b2{background:#eaf5ee;color:var(--ok)}
h2{font-size:18px;margin:0 0 6px;line-height:1.35}
p{margin:0}
.bottom{margin-top:36px;padding:22px;background:#f7f7f7;border-left:3px solid var(--ink)}
.bottom h2{font-size:15px;text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px}
.appendix{margin-top:48px;border-top:1px solid var(--line);padding-top:24px;
 color:var(--muted);font-size:13px}
.appendix h2{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.appendix table{width:100%;border-collapse:collapse;margin-top:12px}
.appendix td,.appendix th{text-align:left;padding:6px 8px 6px 0;vertical-align:top;
 border-bottom:1px solid var(--line);font-family:ui-monospace,Consolas,monospace;font-size:12px}
"""


def render_html(doc: dict) -> str:
    e = html.escape
    items = "".join(
        f'<div class="item"><span class="badge b{sev}">{e(BADGE[sev])}</span>'
        f'<h2>{e(head)}</h2><p>{e(body)}</p></div>'
        for sev, head, body in doc["rows"])
    appendix = "".join(
        f'<tr><td>{e(r["check"])}</td><td>{e(r["status"])}</td>'
        f'<td>{e(json.dumps(r["observed"]))}</td></tr>'
        for r in doc["appendix"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(doc['business'])} — email check</title>
<style>{CSS}</style></head><body><main>
<h1>{e(doc['business'])}<br>what your email looks like from the outside</h1>
<p class="meta">{e(doc['domain'])} &middot; checked {e(doc['checked_at'][:16].replace('T', ' '))} UTC</p>
{items}
<div class="bottom"><h2>The bottom line</h2><p>{e(doc['bottom_line'])}</p></div>
<div class="appendix"><h2>Technical detail — for whoever fixes it</h2>
<table><tr><th>check</th><th>result</th><th>observed</th></tr>{appendix}</table>
<p style="margin-top:14px">&ldquo;Not answered&rdquo; means the check could not be
completed. It is not a pass.</p></div>
</main></body></html>"""


def main() -> int:
    p = argparse.ArgumentParser(
        description="Plain-language report from a verify.py JSON report")
    p.add_argument("--from", dest="src", required=True, help="verify.py --json output")
    p.add_argument("--business", help="the owner's business name, as he says it")
    p.add_argument("--html", dest="html_path", help="also write a printable one-pager")
    a = p.parse_args()

    with open(a.src) as f:
        report = json.load(f)
    doc = build(report, a.business)
    print(render_text(doc))
    if a.html_path:
        with open(a.html_path, "w", encoding="utf-8") as f:
            f.write(render_html(doc))
        print(f"wrote {a.html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
