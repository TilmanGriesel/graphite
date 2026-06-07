# Graphite — project memory for AI agents

Graphite is a Home Assistant theme: design tokens in YAML, compiled to HA theme files.
Keep this file short; depth lives in `.claude/DESIGN-GUIDELINE.md`.

## Golden rules
1. **`themes/*.yaml` are GENERATED — never edit them.** Edit `src/` and run
   `python3 tools/theme_assembler.py` (no flags). Commit `src/` and the regenerated
   `themes/` together.
2. **Color literals (`R, G, B`) live ONLY in `token-rgb-*` primitives.** Semantic tokens and
   templates reference them via `var()`. Templates carry no raw color.
3. **Contrast meets WCAG AA** (4.5:1 normal, 3.0:1 large), checked per build.
4. **Verify before finishing:** `make verify` (drift + tokens + contrast + yaml).

## Source → output
- `src/tokens_common.yaml` + `src/tokens_{dark,light,eink_dark,eink_light}.yaml` — tokens
- `src/template.yaml` (dark/light), `src/template_eink.yaml` (e-ink) — map tokens → HA vars
- `tools/theme_assembler.py` → `themes/{graphite,graphite-light,graphite-auto,graphite-eink-dark,graphite-eink-light}.yaml`

## Quality gates (single source of truth; hooks and CI call these same scripts)
- `scripts/check_drift.sh` — committed `themes/` equals a fresh assembly from `src/`
- `python3 tools/validate_tokens.py` — orphans, duplicate literals, template literals
- `python3 tools/check_contrast.py --all` — WCAG AA per build

**Justified duplication is allowed** — the gate blocks only NEW, *unjustified* spread (a new
color literal outside `token-rgb-*`, a new orphan, etc.):
- inline `key: value  # token-lint: allow-<rule>(reason="...")` (e.g. `allow-duplicate`,
  `allow-literal-outside-primitive`), or
- an entry in `tools/token_exceptions.yaml` (curated, reviewed in the PR),
- pre-existing semantic-layer literals are grandfathered in `tools/token_baseline.yaml`
  (auto-generated; regenerate with `python3 tools/validate_tokens.py --update-baseline` — pay
  them down by converting to `rgb(var(--token-rgb-*))`),
- pre-existing contrast failures are baselined in `tools/contrast_pairs.yaml`.

## Common jobs (skills in `.claude/commands/`)
- `/retune-color` — change a color safely (edit the primitive only)
- `/check-a11y` — contrast report + the minimal fix
- `/verify-theme` — run the full gate (`--report` adds advisory findings)

## Dev environment
- `make ha-start` → http://localhost:8123 (Docker HA mounting `./themes`). On first run,
  **create your own throwaway local account** — no shared credential is committed.
  `make ha-stop` to tear down.
- `scripts/deploy-dev.sh` and `scripts/ha-rebuild-local.sh` use machine-specific paths —
  maintainer-only; don't invoke blindly.

## Conventions
- Commit messages: `feat(themes): …` / `fix(themes): …`.
- Design rationale: `.claude/DESIGN-GUIDELINE.md`, `.claude/ARCHITECTURE.md`,
  `.claude/CI-QUALITY-GATE.md`.
