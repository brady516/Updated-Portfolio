#!/usr/bin/env bash
# partners.sh — source referral-partner suspects with the existing leadfinder.
#
# Same tool as trade lead-gen (leadfinder.py), different queries and NO
# --leads-only (for partners you want every contact, not just freemail ones).
# Edit the CITIES list and run. Requires PLACES_API_KEY set.
#
#   export PLACES_API_KEY="..."
#   bash partners.sh
#
# Output: partners_targets.csv (businesses) -> partners_contacts.csv (emails).
# Ignore the 'status' column on partner runs — freemail vs pro is irrelevant here.

set -euo pipefail
cd "$(dirname "$0")"

# --- edit these -------------------------------------------------------------
CITIES=(
  "Toledo, OH"
  "Ann Arbor, MI"
  # add your target metros
)
# Partner categories, ranked by fit (bookkeepers/accountants convert best).
CATEGORIES=(
  "bookkeeper"
  "accountant"
  "small business accountant"
  "web designer"
  "web design agency"
  "business formation service"
)
# ---------------------------------------------------------------------------

: "${PLACES_API_KEY:?set PLACES_API_KEY first}"

# Build the -q argument list: every category x every city.
QARGS=()
for city in "${CITIES[@]}"; do
  for cat in "${CATEGORIES[@]}"; do
    QARGS+=( -q "${cat} in ${city}" )
  done
done

echo "== sourcing partner suspects (${#CATEGORIES[@]} categories x ${#CITIES[@]} cities) =="
python3 leadfinder.py places "${QARGS[@]}" -o partners_targets.csv

echo "== harvesting partner contact emails (keeping ALL, not just freemail) =="
python3 leadfinder.py harvest -i partners_targets.csv -o partners_contacts.csv --delay 2

echo
echo "Done. Recruit from partners_contacts.csv using partner-outreach.md."
echo "Remember: partners are a relationship sale — email to open, call to close."
