# Graphite Design Guideline (for agents & contributors)

> The principles an agent must honor when changing this theme. Concise by design — a bloated
> guide measurably hurts agent performance. Hard rules are also enforced by CI; this document
> explains the *why* so you cooperate with the gates instead of fighting them.

## The product goal

Graphite is a calm, cohesive Home Assistant theme. Quality means three things, in order:
1. **Visual quality** — it must look right in the actual UI, not just pass a checker.
2. **Readability** — the token source reads cleanly and a human can follow a value to its use.
3. **A strong, centralized token foundation** — values live in one place; meaning is expressed
   by reference, not by copy-paste.

Never trade #1 for #2/#3. If a check passes but the UI looks wrong, the check is incomplete —
fix the theme *and* flag the check. Verify visually with `make ha-start` (→ localhost:8123).

## Non-negotiables

1. **`themes/*.yaml` is GENERATED. Never hand-edit it.** Edit the fragments in `src/` and run
   `python3 tools/theme_assembler.py` (no flags). The committed `themes/` must always equal a
   fresh assembly from `src/`.
2. **One value, one home.** A raw color literal (`R, G, B`) belongs in the primitive layer
   (`token-rgb-*`) and nowhere else. Everything downstream references it via
   `rgb(var(--token-rgb-*))` or `var(--token-…)`. Templates contain **zero** raw color literals.
3. **No orphans.** Every `token-*` you define must be consumed (reachable via an exact
   `var(--NAME)`) by at least one template. If nothing uses it, don't add it (or wire a consumer).
4. **Accessibility is a floor, not a goal.** Text/background pairings meet **WCAG 2.x AA**:
   **4.5:1** normal text, **3.0:1** large. Check the *real* rendered pair (the foreground HA
   actually paints — resolve the template `var()` chain), **per build** (dark and light resolve
   differently). When in doubt, run `/check-a11y`.
5. **Don't break existing behavior.** Changing a shared primitive cascades to every consumer —
   resolve the full `var()` chain first and check all affected builds.

## The token layers

```
token-rgb-*            primitives — the ONLY place raw color literals live
   ↓ rgb(var(--…))
token-color-*          semantic tokens — reference primitives, express meaning
   ↓ var(--…)
template.yaml          maps semantic tokens onto HA / Web Awesome variables (ha-*, wa-*)
                       — references only; never a raw literal

legacy  rgb-*-color    a parallel legacy surface kept in sync with the modern tokens
                       (see "Justified exceptions" — this mirror is an accepted duplication)
```

To change a color: edit the **primitive** (and its documented legacy mirror). Do **not** edit
the downstream semantic tokens or template — they follow automatically. `/retune-color` does
this correctly by construction.

## Per-theme files

`tokens_dark.yaml`, `tokens_light.yaml`, `tokens_eink_dark.yaml`, `tokens_eink_light.yaml`
share `tokens_common.yaml`. Dark/light use `template.yaml`; e-ink uses `template_eink.yaml`.
The e-ink themes are intentionally monochrome and intentionally more `var()`-aliased than
dark/light — that structural difference is expected, not a defect.

A change to one theme usually needs the **same logical change in its siblings**, in the same
shape. If a sibling genuinely should differ, that's an exception — document it (below).

## Justified exceptions (this is allowed)

The "one value, one home" rule has documented escape hatches, because sometimes duplication is
correct (HA core requires a literal in a specific slot; a legacy variable must mirror a modern
one; an e-ink value is intentionally decoupled). Two mechanisms:

- **Per-line annotation** (preferred — line-precise, self-documenting):
  ```yaml
  token-color-feedback-success: rgb(118, 214, 152)  # token-lint: allow-duplicate(reason="…")
  ```
  The gate accepts the duplication **only when a reason is given**. The reason is reviewed in
  the diff like any other code.
- **`tools/token_exceptions.yaml`** — an allowlist for structural exceptions (e.g. the e-ink
  accent split, the legacy `rgb-*-color` mirror). Grandfathers the current state; new,
  unjustified spread still fails.

The gate enforces "**no new, unjustified spread**" — never "no duplication ever." When you
must duplicate, make it an explicit, reasoned, reviewable one-liner.

## Workflow checklist for any token/color change

1. Identify the **primitive** that owns the value; edit it (+ documented legacy mirror only).
2. `python3 tools/theme_assembler.py` to regenerate all five files.
3. `validate_tokens.py` — no new duplicates, orphans, or template literals.
4. `check_contrast.py --all` — all real pairs still meet AA (or fix the primitive until they do).
5. `check_drift.sh` — committed `themes/` matches the fresh assembly.
6. Visual check: `make ha-start`, look at it in both modes.
7. Commit `src/` **and** regenerated `themes/` together. Convention: `fix(themes): …` /
   `feat(themes): …`.

`/verify-theme` runs steps 2–5 as one pass/fail; `/verify-theme --report` adds the advisory
layer-equivalence / cross-file-shape audit.

## Dev environment

- `make ha-start` boots a disposable HA test instance (Docker) at **localhost:8123** mounting
  `./themes`. A fresh clone needs one-time onboarding — create your own throwaway local account
  (no shared secret is committed). `make ha-stop` to tear down.
- `scripts/deploy-dev.sh` (`/Volumes/config`) and `scripts/ha-rebuild-local.sh` (`/config`) are
  **maintainer-only**, machine-specific paths — do not invoke them blindly.
