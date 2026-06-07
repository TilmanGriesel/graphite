# Claude Code Support & Agentic Maintenance — Architecture

> Status: **design proposal** (architect-first). Nothing here is wired up yet.
> Scope: enable correct, autonomous repository maintenance for the Graphite theme
> without sacrificing the centralized-token foundation, readability, or visual quality.

## 0. Thesis

Graphite is a YAML design-token pipeline: hand-edited fragments under `src/` are
concatenated by `tools/theme_assembler.py` into five **generated-but-committed** files
under `themes/`. Every recurring quality problem we have hit is a *coherence* failure —
between source and generated output, between duplicate copies of one value, between
sibling theme files, between a token and its consumer, or between a foreground and its
background. None are caught locally today.

The design is **four layers over one source of truth**:

1. **Validation scripts = the only place rule logic lives.** Small, dependency-light,
   each with a strict CLI contract (`exit 0` pass / `1` violations / `2` internal error)
   and `--json` output so an agent can reason over results, not prose.
2. **Hooks = a fast local *mirror*** that call those scripts at edit time. Convenience,
   not a security boundary (see §6).
3. **CI = the real, contributor-agnostic gate.** It runs the *same scripts*, so an
   agent's local verdict and the merge gate are the same artifact.
4. **Agent layer** (`CLAUDE.md` + skills + subagents) that makes maintenance
   *by-construction correct* — editing the canonical primitive instead of catching
   duplication after the fact.

One line: **scripts are truth; hooks call them locally; CI calls them at merge; skills/subagents call them proactively.**

## 1. Verified facts this design rests on

All confirmed by reading the repo (and the running HA instance):

- The assembler is a pure function of `src/` **except one line**: `# This file was
  generated at <ts>`. Committed `themes/` currently equals `assemble(src/)` minus that line.
- `themes/graphite-auto.yaml` carries the timestamp on **two** lines, because the auto
  theme re-reads the already-written light + dark files from disk and nests them under
  `modes:`. A drift check must strip **all** occurrences.
- Canonical build = `python3 tools/theme_assembler.py` with **no flags**. `--dev` appends
  ` [DEV]` to theme names → any drift check using it reports false drift.
- Validators must run against `src/` per build, **never** against `graphite-auto.yaml`
  (it is a second-order derivative with `_dark`-suffixed anchors; only the drift check
  should touch it).
- **Real bugs to fix once:** `Makefile` `clean` runs `rm -rf theme/*` (singular → no-op;
  the real cleanup is the assembler's own `shutil.rmtree`); the `dockerfile` has a phantom
  `RUN mkdir -p theme`; CI installs PyYAML inline rather than from `requirements.txt`.
- `.claude/settings.json` currently holds only `env` + empty `attribution` — no hooks, no
  `CLAUDE.md`.
- **Contrast must be resolved from the template's real `var()` wiring, not token-name
  similarity.** The label badge's foreground is `label-badge-text-color → token-color-text-primary`
  (`rgb(228,228,231)`). The token `token-color-text-label-badge` (198,203,210) is mapped
  **nowhere** — it is a dead/orphan token, *not* the contrast risk. The actual dark
  failure is `text-primary` over `label-badge-green`.

## 2. The seven defects this prevents

| # | Defect | Example we hit |
|---|---|---|
| 1 | Source/generated **drift** | `themes/*.yaml` hand-committed; nothing enforces `== assemble(src/)` |
| 2 | Token **value duplication** | `224,138,0` defined 4× independently; `32,126,71` 4× in the PR |
| 3 | **Orphan** tokens | `token-color-text-label-badge` defined in all 4 files, consumed nowhere |
| 4 | **Parallel/legacy** systems | `token-*` and legacy `rgb-*-color` carry the same value separately |
| 5 | **Cross-file** structural drift | badge tokens are literals in dark, aliases in light |
| 6 | No **accessibility** gate | green badge 4.00:1, light wa-tag warning 1.85:1 shipped, nothing measured |
| 7 | **Undocumented** dev env | HA test password recorded nowhere |

## 3. Right-sizing (important)

This is a ~100-token, single-maintainer repo. The full design is deliberately scoped so
we **ship a minimal core that is unambiguous, and keep the opinionated checks advisory**
until they earn promotion. This directly serves your "sometimes duplication is justified"
constraint: nuanced rules *advise*; only safe, objective rules *block*.

**Ship now (blocking):**
- `check_drift.sh` — extract the existing CI bash into one reusable script (defect 1).
- `validate_tokens.py` with **only** three objective checks: ORPHAN, DUPLICATE-LITERAL
  (scoped to the `token-rgb-*` primitive layer), NO-RAW-LITERAL-IN-TEMPLATE (defects 2, 3,
  + template hardcodes).
- `check_contrast.py` keyed off real `var()` wiring (defect 6).
- `CLAUDE.md` (concise) + this design.

**Advisory `--report` only (do not block) until proven against `main`:**
- LAYER-EQUIVALENCE (`token-rgb-primary` == legacy `rgb-primary-color`, `feedback-*` ==
  `rgb-*-color`) — defect 4.
- CROSS-FILE SHAPE (same key set + definition style across theme files) — defect 5.
  The e-ink files are pervasively aliased while dark/light are literal-heavy, so the
  allowlist would be large and churny; advisory output avoids red-lining `main`.

**Just fix once (no standing gate):** the `make clean` / dockerfile / requirements bugs.

## 4. File layout (proposed)

```
graphite/
├── CLAUDE.md                      # NEW — concise agent steering (points at the guideline)
├── .gitattributes                 # NEW — themes/*.yaml linguist-generated
├── .claude/
│   ├── settings.json              # ADD hooks block
│   ├── ARCHITECTURE.md            # this doc
│   ├── CI-QUALITY-GATE.md         # research-backed CI recommendation
│   ├── DESIGN-GUIDELINE.md        # agent-readable design principles
│   ├── hooks/{block_generated_edit,regenerate,stop_gate,prime_context}.sh
│   ├── commands/{verify-theme,retune-color,check-a11y}.md
│   └── agents/{token-change,theme-pr-reviewer}.md
├── tools/
│   ├── color_utils.py             # NEW — tiny shared parse_color/resolve_var/ratio
│   ├── validate_tokens.py         # NEW — token-graph linter (3 blocking + 2 advisory)
│   ├── check_contrast.py          # NEW — per-build WCAG gate
│   ├── contrast_pairs.yaml        # NEW — fg/bg pairs derived from real var() wiring
│   └── token_exceptions.yaml      # NEW — documented, reviewable exceptions (escape hatch)
├── scripts/check_drift.sh         # NEW — portable drift gate (extracted from CI)
├── .github/workflows/             # REFACTOR to call the same scripts; job-level conditionals
├── Makefile                       # FIX clean; ADD verify/check-drift/lint-tokens/check-contrast
├── dockerfile / requirements.txt  # FIX phantom mkdir; pin deps; CI installs from requirements
└── .pre-commit-config.yaml        # ADD a real pre-commit gate (see §6)
```

## 5. Layer details

### 5.1 Scripts (truth)
- **`color_utils.py`** — one implementation of `parse_color` (bare `R,G,B`, `rgb()/rgba()`,
  hex, `#fff`), `resolve_var` (fixed-point `var()` expansion, cycle guard), `composite`
  (alpha-flatten before luminance), `contrast_ratio`. `color-mix()` / `hsl(from … calc())`
  return `UNRESOLVABLE` rather than crash. Kept a *utility*, not an architectural keystone —
  the orphan/duplicate checks need no color math at all.
- **`check_drift.sh`** — regenerate into a temp dir via the canonical no-flag invocation,
  strip **all** timestamp lines, `diff -r`. Calls the assembler directly (never `make`,
  which depends on the broken `clean`). Add a self-test so it can't pass by both sides being
  equally broken.
- **`validate_tokens.py`** — operates on **raw text lines** (PyYAML silently collapses
  duplicate keys, hiding them). DUPLICATE-LITERAL is scoped to the `token-rgb-*` layer so the
  *intentional* legacy mirror isn't flagged. ORPHAN uses exact `var(--NAME)` matching (not
  substring) and runs against `src/` per build.
- **`check_contrast.py`** — for each pair in `contrast_pairs.yaml`, resolve fg+bg via the
  real consumer `var()` chain **per build**, composite, compute the WCAG 2.x sRGB ratio,
  fail < 4.5 (normal) / 3.0 (large). Prints the resolved consumer key + both hex values so a
  reviewer can audit the pair is the one HA actually renders.

### 5.2 Hooks (fast local mirror — see §6 for what they are *not*)

| Event | Matcher | Action |
|---|---|---|
| PreToolUse | `Write\|Edit` on `^themes/.*\.yaml$` | **Deny**, name the correct `src/` fragment |
| PostToolUse | `Write\|Edit` on edited `src/` file | cheap, file-local checks only (yaml parse + duplicate-literal in that file) |
| Stop / SubagentStop | — | run the **full** suite once (`check_drift` + `validate_tokens` + `check_contrast --all`); block turn-end on failure |
| UserPromptSubmit | — | inject a 4-line primer (themes/ is generated; canonical build; AA 4.5:1; `make ha-start`) |

Note: full regeneration + full validation lives at **Stop**, not PostToolUse — running the
whole assembler after every keystroke thrashes `themes/` and creates noisy timestamps mid-turn.

### 5.3 Agent layer
- **`CLAUDE.md`** (concise — research warns bloated context *reduces* success): the token
  model, canonical build, "edit `src/` not `themes/`", AA thresholds, dev-env, commit
  convention. Points at `DESIGN-GUIDELINE.md` for depth.
- **Skills:** `/retune-color` (resolve the chain, edit **only** the canonical primitive +
  documented legacy mirror, then run the suite — by-construction prevention of defect 2),
  `/verify-theme [--report]` (the executable trust checklist), `/check-a11y`.
- **Subagents:** `token-change` (guarded edit→assemble→validate loop in isolation),
  `theme-pr-reviewer` (read-only, fixed checklist, structured verdict — this is the
  "review this PR" job).

## 6. Honest enforcement model (red-team correction)

**Client-side hooks are NOT a real gate.** `.claude/settings.json` is bypassed by
non-Claude contributors, `git commit --no-verify`, edits outside Claude Code, or a direct
`git add` of a stale generated file. The PreToolUse Bash guard is defeated by any
`python -c` / `tee` / heredoc. Treat hooks as a fast feedback mirror only.

The **real** enforcement is two things, both running the same scripts:
1. A genuine **`.git/hooks/pre-commit`** entry (the repo already uses `pre-commit`) running
   `check_drift.sh` + `validate_tokens.py` — stops local human commits.
2. **CI as a required status check** with "Do not allow bypassing" — the only
   contributor-agnostic boundary.

## 7. Defect → preventer

| # | Blocking preventer | Backstop |
|---|---|---|
| 1 | PreToolUse block + pre-commit `check_drift.sh` | Stop hook + CI |
| 2 | `validate_tokens` DUPLICATE-LITERAL; `/retune-color` by construction | CI |
| 3 | `validate_tokens` ORPHAN | CI; `/add-token` refuses |
| 4 | *advisory* LAYER-EQUIVALENCE + `token_exceptions.yaml` | review |
| 5 | *advisory* CROSS-FILE SHAPE + `token_exceptions.yaml` | review |
| 6 | `check_contrast` per-build | PostToolUse + CI |
| 7 | `CLAUDE.md` dev-env + onboarding fix | docs |

## 8. Rollout

- **P0 — Foundation + drift containment.** `color_utils.py`; extract `check_drift.sh`;
  `validate_tokens.py` (3 objective checks, warn mode); PreToolUse block + Stop hook;
  real `pre-commit` entry.
- **P0.5 — Fix the broken foundation.** `make clean`, dockerfile, `requirements.txt`/CI
  install parity.
- **P1 — Go blocking + steering + CI convergence.** Flip the 3 objective checks to blocking;
  write `CLAUDE.md` + `DESIGN-GUIDELINE.md`; refactor CI to call the scripts with
  **job-level conditionals** (not workflow path filters — see CI-QUALITY-GATE.md); add
  `.gitattributes`.
- **P1.5 — Accessibility gate.** `check_contrast.py` + `contrast_pairs.yaml` (seed from real
  wiring; confirm it reproduces the known dark-badge failure), wire into Stop + CI.
- **P2 — Proactive agent layer + (optional) AI PR review.** Skills, subagents, UserPromptSubmit
  primer; evaluate the AI reviewer options in CI-QUALITY-GATE.md.
- **P3 — Advisory → considered-blocking.** Once `token_exceptions.yaml` cleanly covers `main`,
  decide whether LAYER-EQUIVALENCE / CROSS-FILE SHAPE graduate to blocking.

## 9. Open questions (need a decision)
- **Dev-env credential (defect 7):** document a "create your own test account" convention,
  or script HA onboarding so there's no manual password? (Safe default: documented convention.)
- **UNRESOLVABLE contrast policy:** `color-mix()` / relative-HSL pairs — WARN locally,
  `--strict` (fail) in CI?
- **DTCG migration:** adopt the now-stable W3C DTCG token format for standardized
  alias/reference validation, or keep the custom YAML pipeline? (See CI-QUALITY-GATE.md §4.)
- **Manifest honesty:** should `validate_tokens` warn when a template adds a new
  `label-badge/on-/fill-` consumer with no `contrast_pairs.yaml` row? (Prevents the next
  silent contrast miss.)
