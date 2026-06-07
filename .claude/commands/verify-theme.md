---
description: Run the full Graphite quality gate (drift, tokens, contrast, YAML) and report pass/fail
argument-hint: "[--report]"
---
Run the read-only quality gate for the Graphite theme and summarize the results. Do NOT
hand-edit `themes/`.

1. Run `make verify` (equivalently: `scripts/check_drift.sh`, `python3 tools/validate_tokens.py`,
   `python3 tools/check_contrast.py --all`, `make validate-yaml`).
2. If `$ARGUMENTS` contains `--report`, also run `python3 tools/validate_tokens.py --strict-advisory`
   to surface advisory findings (literal-outside-primitive, layer-equivalence) without failing.
3. Report a concise pass/fail per gate. On any failure, show the exact offending `file:line`
   (or contrast pair, with resolved hex + ratio) and the minimal fix — which is always editing
   the canonical `token-rgb-*` primitive in `src/`, never `themes/`.
4. Remind the user to do a visual check with `make ha-start` → http://localhost:8123.
