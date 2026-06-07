#!/usr/bin/env bash
# PreToolUse(Write|Edit): deny edits to generated themes/*.yaml and point at the src/ source.
# exit 2 blocks the tool call and shows stderr to the agent.
input=$(cat)
fp=$(printf '%s' "$input" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)
case "$fp" in
  */themes/*.yaml|themes/*.yaml)
    echo "Refusing to edit a GENERATED file: $fp" >&2
    echo "themes/*.yaml are produced by tools/theme_assembler.py. Edit the matching src/ fragment" >&2
    echo "(src/tokens_*.yaml or src/template*.yaml); the themes/ files regenerate from it." >&2
    exit 2 ;;
esac
exit 0
