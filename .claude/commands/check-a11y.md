---
description: Report WCAG contrast for the theme and the minimal fix to reach AA
argument-hint: "[--build dark|light|eink-dark|eink-light]"
---
1. Run `python3 tools/check_contrast.py --all` (or `--build <build>` if named in `$ARGUMENTS`).
2. For each failing or baseline-waived pair, report: build, UI element (pair name), resolved
   foreground/background hex, current ratio vs the required threshold.
3. For real failures, propose the minimal edit to the canonical `token-rgb-*` primitive that
   brings the pair to ≥ 4.5:1 (or 3.0:1 for large text), and note the side effects on other
   consumers of that primitive.
4. Do not modify `themes/`. If asked to apply a fix, edit the primitive in `src/`, run
   `python3 tools/theme_assembler.py`, and re-run the gate to confirm.
