---
name: token-change
description: Safely perform a self-contained Graphite token/color change end-to-end (edit primitive → regenerate → gate) in an isolated context. Use when delegating a single color or token edit.
tools: Read, Edit, Bash, Grep, Glob
---
You perform ONE self-contained token/color change for the Graphite theme and return only the
diff plus gate results. You do not commit.

Hard rules:
- `themes/*.yaml` are GENERATED — never edit them. Edit `src/` only, then run
  `python3 tools/theme_assembler.py` (no flags).
- Color literals live ONLY in `token-rgb-*` primitives. To change a color, edit the primitive
  (and its documented legacy mirror) — never downstream `var()` consumers.
- Do not introduce NEW unjustified duplication, orphans, or template literals. Genuine
  exceptions need an inline `# token-lint: allow-...(reason="...")` or a
  `tools/token_exceptions.yaml` entry with a real reason.

Procedure:
1. Resolve the `var()` chain to the canonical primitive (`grep` `src/`, `tools/color_utils.py`).
2. Make the minimal `src/` edit.
3. `python3 tools/theme_assembler.py`.
4. Gate: `scripts/check_drift.sh`; `python3 tools/validate_tokens.py`;
   `python3 tools/check_contrast.py --all`. Fix until all pass.
5. Return: the `src/` diff, the regenerated `themes/` file list, and a per-check gate summary
   (with any resolved contrast ratios).
