---
description: Change a Graphite color safely by editing only the canonical primitive, then verify
argument-hint: <what to change> (e.g. "make the brand primary a warmer orange")
---
Goal: change a color WITHOUT spreading values across the token graph.

1. **Find the canonical primitive.** Resolve the `var()` chain from the HA consumer down to the
   owning `token-rgb-*` primitive in `src/tokens_*.yaml` (use `grep` / `tools/color_utils.py`).
2. **Edit only that primitive** (plus its documented legacy `rgb-*-color` mirror, if one exists).
   Do NOT touch downstream `token-color-*` or template `var()` consumers — they follow
   automatically. Apply the same change to sibling theme files when the color is themed per
   build; if a sibling must differ, record it as an exception (`token-lint: allow-...` or
   `tools/token_exceptions.yaml`) with a reason.
3. **Regenerate:** `python3 tools/theme_assembler.py` (no flags).
4. **Verify:** `python3 tools/validate_tokens.py` (no new duplicate-literal/orphan),
   `python3 tools/check_contrast.py --all` (no new AA regression), `scripts/check_drift.sh`.
5. If a contrast pair now fails, adjust the primitive until it meets AA; report the resolved
   hex + ratio and note other consumers of that primitive that are affected.
6. Never hand-edit `themes/`. Stage `src/` and the regenerated `themes/` together.

Request: $ARGUMENTS
