#!/usr/bin/env bash
# Render the JeevanSetu handouts to PDF using headless Chrome.
#
# Chrome is used because the machine has no LaTeX or WeasyPrint, and Chrome's print
# engine handles the print stylesheet directly. Run from anywhere:
#
#     ./docs/print/build.sh
#
set -euo pipefail

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$(cd "$HERE/.." && pwd)"

if [ ! -x "$CHROME" ]; then
  echo "error: Chrome not found at $CHROME. Set CHROME=/path/to/chrome and retry." >&2
  exit 1
fi

render() {
  local source="$1" target="$2"
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$OUT/$target" "file://$HERE/$source" 2>/dev/null
  echo "wrote docs/$target"
}

render pitch.html JeevanSetu-Pitch.pdf
render project-explained.html JeevanSetu-Project-Explained.pdf
