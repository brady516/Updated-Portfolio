#!/usr/bin/env python3
"""Salad Scout — find Wall Street word salad for the North de Noise paid segment.

Ranks the most jargon-dense sentences in a body of text and prints them with
citations, so picking the "Wall Street Word Salad of the Week" is a 10-minute job
instead of a 24-hour CNBC marathon.

Sources are public and quotable on purpose:
  * `edgar`  — SEC EDGAR full-text search (public-domain govt data, free API)
  * `url`    — any public page (an IR earnings-call transcript, a Fed statement…)
  * `score`  — a local file / stdin you already have

Stdlib only. EDGAR requires a declared User-Agent (SEC rule) — pass --ua
"Your Name your@email".

Examples:
  python3 salad_scout.py score --input transcript.txt --top 10
  cat transcript.txt | python3 salad_scout.py score --stdin
  python3 salad_scout.py url "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240131a.htm"
  python3 salad_scout.py edgar --forms 10-K,10-Q --days 14 --max-docs 8 \
      --ua "Brady Gallagher brady@northdenoise.com" --out output

Output is ranked candidates; YOU pick one and write the plain-English translation.
Quote short, attribute the source — that's textbook fair-use commentary.
"""

import argparse
import csv
import html.parser
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

# --------------------------------------------------------------------------
# Default weighted lexicon. Higher weight = more egregious salad.
# Override / extend with --lexicon FILE (one "term,weight" per line).
# --------------------------------------------------------------------------
DEFAULT_LEXICON = {
    # peak salad (3)
    "optionality": 3, "asymmetric": 3, "idiosyncratic": 3, "secular": 3,
    "inflection": 3, "flywheel": 3, "synergies": 3, "synergy": 3,
    "best-in-class": 3, "paradigm": 3, "north star": 3, "operationalize": 3,
    "core competency": 3, "value creation": 3, "shareholder value": 3,
    "headwinds": 3, "tailwinds": 3, "green shoots": 3, "derisk": 3, "de-risk": 3,
    "holistic": 3, "ecosystem": 3, "durable competitive": 3, "moat": 3,
    "multi-bagger": 3, "right-size": 3, "leverage our": 3,
    # medium salad (2)
    "robust": 2, "prudent": 2, "dynamic": 2, "disciplined": 2, "accretive": 2,
    "cadence": 2, "bandwidth": 2, "granularity": 2, "visibility": 2,
    "constructive": 2, "nuanced": 2, "conviction": 2, "catalyst": 2,
    "backdrop": 2, "regime": 2, "mission-critical": 2, "scalable": 2,
    "frictionless": 2, "seamless": 2, "unlock": 2, "double down": 2,
    "circle back": 2, "secular tailwind": 2, "priced in": 2, "sustainable": 2,
    "strategic": 2, "monetize": 2, "structural": 2, "embedded": 2,
    "long runway": 2, "high-conviction": 2, "premium multiple": 2,
    # common filler (1)
    "growth": 1, "momentum": 1, "exposure": 1, "allocation": 1,
    "fundamentals": 1, "valuation": 1, "guidance": 1, "outlook": 1,
    "macro": 1, "thesis": 1, "narrative": 1, "data-dependent": 1,
}


# --------------------------------------------------------------------------
# HTML -> text
# --------------------------------------------------------------------------
class _TextExtractor(html.parser.HTMLParser):
    _SKIP = {"script", "style", "head", "noscript"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def strip_html(raw):
    p = _TextExtractor()
    try:
        p.feed(raw)
    except Exception:
        pass
    text = " ".join(p.parts)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
def load_lexicon(path):
    lex = dict(DEFAULT_LEXICON)
    if path:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "," in line:
                    term, w = line.rsplit(",", 1)
                    try:
                        lex[term.strip().lower()] = float(w)
                    except ValueError:
                        lex[line.lower()] = 2
                else:
                    lex[line.lower()] = 2
    # longest-first so multi-word phrases match before their parts
    return sorted(lex.items(), key=lambda kv: -len(kv[0]))


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def split_sentences(text):
    # collapse, then split; keep things that look like real sentences
    for chunk in _SENT_SPLIT.split(text):
        s = chunk.strip()
        if s:
            yield s


def score_sentence(sentence, lexicon):
    low = sentence.lower()
    hits, weighted, distinct = [], 0.0, set()
    for term, weight in lexicon:
        # word-boundary-ish match (handles hyphens/multiword)
        pat = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        n = len(re.findall(pat, low))
        if n:
            hits.append(term)
            weighted += weight * n
            distinct.add(term)
    words = max(1, len(re.findall(r"\b\w+\b", sentence)))
    # density: reward weighted hits and variety, gently dampen by length
    score = weighted * (1 + 0.5 * (len(distinct) - 1)) / math.log(words + 4)
    return score, weighted, sorted(set(hits)), words


def rank_text(text, lexicon, top, min_words=6, max_words=120):
    results = []
    seen = set()
    for sent in split_sentences(text):
        words = len(re.findall(r"\b\w+\b", sent))
        if words < min_words or words > max_words:
            continue
        key = sent.lower()[:120]
        if key in seen:
            continue
        seen.add(key)
        score, weighted, hits, _ = score_sentence(sent, lexicon)
        if weighted <= 0:
            continue
        results.append({"score": round(score, 2), "weighted": weighted,
                        "buzzwords": hits, "sentence": sent})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top]


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------
def fetch(url, ua, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        "Accept-Encoding": "identity",
        "Accept": "*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def edgar_search(terms, forms, days, max_docs, ua, entity=None):
    """Query EDGAR full-text search; return [{company, form, date, url}].

    entity: optional company-name filter (EFTS entityName) to target a specific
    filer — e.g. "Ford Motor Co" — when you want a named, attributable quote.
    """
    start = (date.today() - timedelta(days=days)).isoformat()
    end = date.today().isoformat()
    q = " OR ".join(f'"{t.strip()}"' for t in terms)
    params = {"q": q, "forms": forms, "startdt": start, "enddt": end}
    if entity:
        params["entityName"] = entity
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(params)
    data = json.loads(fetch(url, ua))
    out = []
    for h in data.get("hits", {}).get("hits", [])[:max_docs]:
        src = h.get("_source", {})
        names = src.get("display_names") or ["(unknown filer)"]
        ciks = src.get("ciks") or []
        _id = h.get("_id", "")  # "accession:document"
        doc_url = None
        if ":" in _id and ciks:
            accession, doc = _id.split(":", 1)
            acc_nodash = accession.replace("-", "")
            cik = ciks[0].lstrip("0")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"
        out.append({
            "company": names[0],
            "form": src.get("root_form") or src.get("file_type") or forms,
            "date": src.get("file_date", end),
            "url": doc_url,
        })
    return out


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def print_candidates(rows, fmt, fh=sys.stdout):
    if fmt == "json":
        json.dump(rows, fh, indent=2)
        fh.write("\n")
        return
    if fmt == "csv":
        w = csv.writer(fh)
        w.writerow(["rank", "score", "buzzwords", "sentence", "source"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["score"], "|".join(r["buzzwords"]),
                        r["sentence"], r.get("source", "")])
        return
    # text
    for i, r in enumerate(rows, 1):
        fh.write(f"\n#{i}  salad score {r['score']}  [{', '.join(r['buzzwords'])}]\n")
        if r.get("source"):
            fh.write(f"    source: {r['source']}\n")
        fh.write(f"    “{r['sentence']}”\n")
    fh.write("\n" + "-" * 70 + "\n")
    fh.write("Pick one, write the plain-English Translation + What it's hiding.\n")
    fh.write("Quote short and attribute (company, form/call, date). Fair-use commentary.\n")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def cmd_score(args, lexicon):
    if args.stdin:
        text = sys.stdin.read()
    elif args.input:
        with open(args.input, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    else:
        sys.exit("score: provide --input FILE or --stdin")
    if args.input and args.input.lower().endswith((".htm", ".html")):
        text = strip_html(text)
    rows = rank_text(text, lexicon, args.top)
    print_candidates(rows, args.format)


def cmd_url(args, lexicon):
    raw = fetch(args.url, args.ua)
    text = strip_html(raw)
    rows = rank_text(text, lexicon, args.top)
    for r in rows:
        r["source"] = args.url
    print_candidates(rows, args.format)


def cmd_edgar(args, lexicon):
    if not args.ua or "@" not in args.ua:
        sys.exit('edgar: --ua "Your Name your@email" is required by SEC.')
    terms = (args.terms.split(",") if args.terms
             else ["optionality", "headwinds", "secular", "synergies", "inflection"])
    try:
        filings = edgar_search(terms, args.forms, args.days, args.max_docs, args.ua,
                               entity=args.entity)
    except Exception as e:
        sys.exit(f"edgar search failed: {e}")
    all_rows = []
    for f in filings:
        if not f["url"]:
            continue
        try:
            raw = fetch(f["url"], args.ua)
        except Exception as e:
            print(f"  (skip {f['company']}: {e})", file=sys.stderr)
            continue
        text = strip_html(raw)
        cite = f"{f['company']} — {f['form']} {f['date']} — {f['url']}"
        for r in rank_text(text, lexicon, args.per_doc):
            r["source"] = cite
            all_rows.append(r)
        time.sleep(0.3)  # be polite to SEC
    all_rows.sort(key=lambda r: r["score"], reverse=True)
    all_rows = all_rows[:args.top]

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        stamp = date.today().isoformat()
        path = os.path.join(args.out, f"salad-{stamp}.{ 'json' if args.format=='json' else 'csv' if args.format=='csv' else 'txt'}")
        with open(path, "w", encoding="utf-8") as fh:
            print_candidates(all_rows, args.format, fh)
        print(f"Wrote {len(all_rows)} candidates -> {path}")
    else:
        print_candidates(all_rows, args.format)


def main():
    ap = argparse.ArgumentParser(description="Salad Scout — rank Wall Street word salad")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lexicon", help="extra term,weight file (extends the default)")
    common.add_argument("--format", choices=["text", "json", "csv"], default="text")
    common.add_argument("--top", type=int, default=10, help="candidates to return")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("score", parents=[common], help="score local text / stdin")
    sp.add_argument("--input")
    sp.add_argument("--stdin", action="store_true")

    up = sub.add_parser("url", parents=[common], help="score any public URL")
    up.add_argument("url")
    up.add_argument("--ua", default="Salad Scout (contact: set --ua)")

    ep = sub.add_parser("edgar", parents=[common], help="search SEC EDGAR full-text + score")
    ep.add_argument("--forms", default="10-K,10-Q,8-K")
    ep.add_argument("--days", type=int, default=14)
    ep.add_argument("--terms", help="comma list of search phrases (default: a salad starter pack)")
    ep.add_argument("--entity", help='filter to one filer (EFTS entityName), e.g. "Ford Motor Co"')
    ep.add_argument("--max-docs", type=int, default=8, dest="max_docs")
    ep.add_argument("--per-doc", type=int, default=5, dest="per_doc")
    ep.add_argument("--ua", help='required: "Your Name your@email"')
    ep.add_argument("--out", help="write a dated file to this dir (cron-friendly)")

    args = ap.parse_args()
    lexicon = load_lexicon(args.lexicon)
    {"score": cmd_score, "url": cmd_url, "edgar": cmd_edgar}[args.cmd](args, lexicon)


if __name__ == "__main__":
    main()
