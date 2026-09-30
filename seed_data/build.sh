#!/usr/bin/env bash
# Render the synthetic seed documents from their HTML sources to the PDFs the demo uploads.
#
# The HTML files under each persona's source/ directory are the editable originals. Run this
# after editing one, then re-seed in live mode so the extraction snapshot matches.
#
#     ./seed_data/build.sh
#
# Chrome is used because the machine has no LaTeX or WeasyPrint, matching docs/print/build.sh.
set -euo pipefail

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$CHROME" ]; then
  echo "error: Chrome not found at $CHROME. Set CHROME=/path/to/chrome and retry." >&2
  exit 1
fi

# With no arguments every persona is rendered. Pass persona directory names to render only
# those, which is how the two newer personas were added without touching the verified PDFs
# of the original two.
WANTED=("$@")

wanted() {
  [ ${#WANTED[@]} -eq 0 ] && return 0
  local candidate
  for candidate in "${WANTED[@]}"; do
    [ "$candidate" = "$1" ] && return 0
  done
  return 1
}

render() {
  local persona="$1" source_file="$2" target="$3"
  wanted "$persona" || return 0
  mkdir -p "$HERE/$persona/documents"
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$HERE/$persona/documents/$target" \
    "file://$HERE/$persona/source/$source_file" 2>/dev/null
  echo "wrote seed_data/$persona/documents/$target"
}

render conflict_persona conflict_will.html 01_will.pdf
render conflict_persona conflict_bank_nomination.html 02_bank_nomination.pdf
render conflict_persona conflict_insurance_nomination.html 03_insurance_nomination.pdf
render conflict_persona conflict_mutual_fund_nomination.html 04_mutual_fund_nomination.pdf

render clean_persona clean_will.html 01_will.pdf
render clean_persona clean_bank_nomination.html 02_bank_nomination.pdf
render clean_persona clean_insurance_nomination.html 03_insurance_nomination.pdf

render nps_persona nps_will.html 01_will.pdf
render nps_persona nps_nomination.html 02_nps_nomination.pdf

render joint_persona joint_will.html 01_will.pdf
render joint_persona joint_bank_nomination.html 02_bank_nomination.pdf
