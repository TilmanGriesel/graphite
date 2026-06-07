#!/usr/bin/env bash
#
# check_drift.sh — assert the committed themes/ exactly equal a fresh assembly from src/.
#
# This is the single drift gate, called identically by the Stop hook, `make check-drift`,
# the pre-commit hook, and CI. It regenerates into a temp dir using the CANONICAL no-flag
# assembler invocation, strips EVERY generator-timestamp line (graphite-auto.yaml carries
# two, because the auto theme re-reads light+dark from disk), and diffs.
#
# Never goes through `make` (whose clean target is a historical no-op); calls the assembler
# directly so it can't inherit broken-clean coupling.
#
# Usage:   scripts/check_drift.sh [--json]
# Exit:    0 = committed matches fresh assembly · 1 = drift · 2 = assembler/internal failure
set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

JSON=0
[[ "${1:-}" == "--json" ]] && JSON=1

TS_MARKER='This file was generated at'
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REGEN="$TMP/regen"
A="$TMP/committed_norm"
B="$TMP/regen_norm"
mkdir -p "$REGEN" "$A" "$B"

fail2() {
  if [[ $JSON -eq 1 ]]; then printf '{"ok":false,"error":%s}\n' "$(printf '%s' "$1" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
  else echo "check_drift: ERROR: $1" >&2; fi
  exit 2
}

# 1. Regenerate from src/ via the canonical invocation (no --dev, no --name override).
python3 tools/theme_assembler.py --themes-dir "$REGEN" >/dev/null 2>"$TMP/assembler.err" \
  || fail2 "assembler failed: $(cat "$TMP/assembler.err")"

[[ -d themes ]] || fail2 "no committed themes/ directory to compare against"

# 2. Normalize: copy both trees stripping the timestamp line(s).
for f in themes/*.yaml; do grep -v "$TS_MARKER" "$f" > "$A/$(basename "$f")"; done
for f in "$REGEN"/*.yaml; do grep -v "$TS_MARKER" "$f" > "$B/$(basename "$f")"; done

# 3. Compare.
if DIFF="$(diff -r "$A" "$B" 2>&1)"; then
  if [[ $JSON -eq 1 ]]; then echo '{"ok":true,"drift":[]}'
  else echo "✅ check_drift: committed themes/ match a fresh assembly from src/ (timestamps ignored)"; fi
  exit 0
else
  if [[ $JSON -eq 1 ]]; then
    printf '{"ok":false,"diff":%s}\n' "$(printf '%s' "$DIFF" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
  else
    echo "❌ check_drift: committed themes/ DIFFER from a fresh assembly from src/" >&2
    echo "   Run 'python3 tools/theme_assembler.py' and commit the regenerated themes/." >&2
    echo "$DIFF" >&2
  fi
  exit 1
fi
