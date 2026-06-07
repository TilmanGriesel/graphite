#!/usr/bin/env bash
# PostToolUse(Write|Edit on src/*.yaml): keep themes/ in sync via the canonical assembler.
# Runs only after a src/ fragment changes. exit 2 surfaces an assembler failure to the agent.
input=$(cat)
fp=$(printf '%s' "$input" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)
case "$fp" in
  */src/*.yaml|src/*.yaml) ;;
  *) exit 0 ;;
esac
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}" || exit 0
err=$(python3 tools/theme_assembler.py 2>&1 >/dev/null) \
  && { echo "Regenerated themes/ from src/ (canonical assembler)."; exit 0; } \
  || { echo "Assembler FAILED after editing $fp:" >&2; echo "$err" >&2; exit 2; }
