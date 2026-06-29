#!/usr/bin/env python3
"""Salad Translator — a deterministic, no-AI decoder for Wall Street word salad.

Pairs with salad_scout.py: Scout *finds* the quote, this *drafts* the translation —
honestly. It is rule-based on purpose. A dictionary can't invent a motive; it can
only decode words that are actually on the page. That's the whole integrity point
("mock the words, not the motive") expressed as code.

It does NOT write the funny final copy — that's you. It hands you:
  1. DECODED   — each jargon phrase it found → plain English
  2. DRAFT     — a rough literal swap to react to
  3. TELLS     — what the *language pattern* signals (provable from the text)
You add the wit and approve before publishing. Add voice, never add claims.

Usage:
  python3 translate.py --quote "the optionality embedded in our sites..."
  cat quote.txt | python3 translate.py --stdin
"""

import argparse
import re
import sys

# jargon -> plain English. Neutral, literal decodings (no motive claims).
GLOSSARY = {
    "optionality": "choices / flexibility",
    "asymmetric": "more upside than downside (claimed)",
    "idiosyncratic": "specific to this company",
    "secular": "long-term",
    "inflection point": "a turn (hoped for)",
    "inflection": "a turn (hoped for)",
    "flywheel": "a self-reinforcing loop",
    "synergies": "savings from combining",
    "synergy": "savings from combining",
    "best-in-class": "good (asserted)",
    "world-class": "good (asserted)",
    "headwinds": "things going against us",
    "tailwinds": "things going our way",
    "green shoots": "early signs",
    "de-risk": "make less risky",
    "derisk": "make less risky",
    "holistic": "overall",
    "ecosystem": "set of related products",
    "moat": "competitive advantage",
    "robust": "solid (asserted)",
    "prudent": "careful",
    "disciplined": "careful",
    "accretive": "adds to earnings",
    "cadence": "schedule",
    "bandwidth": "time / capacity",
    "granularity": "detail",
    "visibility": "ability to forecast",
    "constructive": "optimistic",
    "conviction": "confidence (a feeling)",
    "catalyst": "trigger",
    "backdrop": "environment",
    "regime": "environment",
    "mission-critical": "important",
    "scalable": "able to grow",
    "frictionless": "easy",
    "seamless": "easy",
    "unlock": "release / enable",
    "monetize": "make money from",
    "structural": "built-in / lasting",
    "embedded": "built-in",
    "long runway": "lots of room to grow (claimed)",
    "premium multiple": "a high valuation",
    "shareholder value": "the stock price",
    "cost center": "a part that costs money",
    "capital allocation": "how we spend money",
    "return capital to shareholders": "buybacks / dividends",
    "data-dependent": "we'll see",
    "well-positioned": "we think we'll be fine",
    "navigate": "deal with",
    "operationalize": "actually do",
    "core competency": "what we're good at",
    "value creation": "making money (claimed)",
    "right-size": "cut",
    "nimble": "able to change our minds",
    "sustainable": "able to keep going (asserted)",
    "non-recurring": "one-time (allegedly)",
    "transitory": "temporary (hoped)",
    "additive": "helpful to",
    "transition workloads": "run something else on the machines",
}

# language-pattern -> what the WORDS typically signal. General media-literacy
# observations about the phrasing — not factual claims about the company.
TELLS = [
    (r"rather than (?:simply )?a?\s*cost center",
     "Invoking 'cost center' to deny it is usually a sign they're worried it is one."),
    (r"\b(?:remains? )?committed to\b",
     "'Committed to' states intent, not ability."),
    (r"\bnon-?recurring|\bone-?time\b",
     "'Non-recurring' / 'one-time' items have a famous habit of recurring."),
    (r"\btiming\b|\bunfavorable timing\b",
     "'Timing' is the all-purpose excuse for a weak result."),
    (r"\bdata-?dependent\b|\bnimble\b|\bmonitor(?:ing)?\b|\bas appropriate\b|\bwell-positioned\b",
     "Hedge language — the honest version is 'we don't know yet.'"),
    (r"\bsustainable\b|\bwell-?covered\b",
     "'Sustainable' / 'well-covered' tend to show up right before something isn't."),
    (r"\bsynerg(?:y|ies)\b",
     "'Synergies' usually means cost-cutting — ask where it comes from."),
    (r"\blong-?term shareholder value\b",
     "Everything gets justified as 'long-term shareholder value'; it explains nothing."),
    (r"\brobust\b|\bbest-?in-?class\b|\bworld-?class\b|\bstrong\b|\bsolid\b",
     "Adjectives doing a number's job — ask for the number."),
    (r"\bheadwinds\b|\bmacro(?:economic)?\b",
     "External blame — check what was actually within their control."),
    (r"\bstrategic\b",
     "'Strategic' often just means 'on purpose.'"),
    (r"\bbacktest(?:ed)?\b",
     "Backtests are where overfitting lives — ask for out-of-sample and live results."),
    (r"\bproprietary\b|\bblack ?box\b",
     "'Proprietary' often means 'we won't show you.'"),
    (r"\bAI-?driven\b|\bmachine ?learning\b",
     "Tech buzzword — ask what it actually does."),
    (r"\boptionality\b",
     "'Optionality' is a long word for 'choices.'"),
]


def _phrases_longest_first():
    return sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0]))


def decode(quote):
    low = quote.lower()
    found = []
    for term, gloss in _phrases_longest_first():
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", low):
            found.append((term, gloss))
    return found


def rough_translate(quote):
    out = quote
    for term, gloss in _phrases_longest_first():
        out = re.sub(r"(?<!\w)" + re.escape(term) + r"(?!\w)",
                     f"[{gloss}]", out, flags=re.IGNORECASE)
    return out


def find_tells(quote):
    notes = []
    for pat, note in TELLS:
        if re.search(pat, quote, flags=re.IGNORECASE):
            notes.append(note)
    # de-dupe while preserving order
    seen, uniq = set(), []
    for n in notes:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def main():
    ap = argparse.ArgumentParser(description="Salad Translator — deterministic word-salad decoder (no AI)")
    ap.add_argument("--quote", help="the salad quote to decode")
    ap.add_argument("--stdin", action="store_true", help="read the quote from stdin")
    ap.add_argument("--input", help="read the quote from a file")
    args = ap.parse_args()

    if args.stdin:
        quote = sys.stdin.read().strip()
    elif args.input:
        with open(args.input, encoding="utf-8", errors="replace") as fh:
            quote = fh.read().strip()
    elif args.quote:
        quote = args.quote.strip()
    else:
        sys.exit("Provide --quote \"...\", --stdin, or --input FILE")

    decoded = decode(quote)
    tells = find_tells(quote)

    print("=" * 70)
    print("QUOTE")
    print("  " + quote)
    print()
    print("DECODED (jargon → plain):")
    if decoded:
        for term, gloss in decoded:
            print(f"  • {term} → {gloss}")
    else:
        print("  (no catalogued jargon found — add terms to GLOSSARY, or it's "
              "refreshingly plain)")
    print()
    print("DRAFT TRANSLATION (rough literal swap — polish in YOUR voice):")
    print("  " + rough_translate(quote))
    print()
    print("WHAT IT'S HIDING (language tells — provable from the text):")
    if tells:
        for n in tells:
            print(f"  • {n}")
    else:
        print("  (no classic tells fired)")
    print()
    print("-" * 70)
    print("INTEGRITY: everything above is derived only from words in the quote.")
    print("Add wit. Add nothing else. No motives, no claims not on the page.")
    print("Then attribute: — Company, form/call, date (link). Review before publish.")


if __name__ == "__main__":
    main()
