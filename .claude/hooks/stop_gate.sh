#!/usr/bin/env bash
# Stop/SubagentStop: the full read-only quality gate. Blocks turn completion (exit 2) on any
# failure so the agent self-corrects. This is the backstop for any write the matchers missed.
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}" || exit 0
fail=0
report=""
run() {  # run <label> <cmd...>
  local label="$1"; shift
  local out
  if ! out=$("$@" 2>&1); then
    fail=1
    report="${report}
── ${label} ──
${out}"
  fi
}
run "drift"    scripts/check_drift.sh
run "tokens"   python3 tools/validate_tokens.py
run "contrast" python3 tools/check_contrast.py --all
if [ "$fail" -eq 1 ]; then
  printf 'Quality gate failed — resolve before finishing:%s\n' "$report" >&2
  exit 2
fi
exit 0
