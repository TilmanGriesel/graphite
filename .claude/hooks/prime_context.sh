#!/usr/bin/env bash
# UserPromptSubmit: short orientation primer (stdout is added to the agent's context).
cat <<'EOF'
[graphite] themes/*.yaml are GENERATED — edit src/ (tokens_*.yaml / template*.yaml), then `python3 tools/theme_assembler.py` (no flags). Never hand-edit themes/.
[graphite] Gates: `make verify` = drift + tokens + contrast + yaml. Rules: color literals live ONLY in token-rgb-*; text/bg meets WCAG AA 4.5:1. Justified duplication → inline `# token-lint: allow-duplicate(reason="...")` or tools/token_exceptions.yaml.
[graphite] Visual check: `make ha-start` → http://localhost:8123 (first run: create your own throwaway local account). See .claude/DESIGN-GUIDELINE.md.
EOF
exit 0
