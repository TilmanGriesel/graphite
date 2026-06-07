# GitHub AI PR Review & Quality Gate — Recommendation

> Status: **research-backed recommendation** (design proposal). Sourced and adversarially
> verified (Jan 2026). Citations at the end; read the **caveats** — pricing and tool
> coverage were only partially researched.

## TL;DR

Build the quality gate as **deterministic scripts surfaced as GitHub check runs + sticky PR
comments, made *required*** — and add an **AI reviewer for judgment** on top. The AI advises;
the deterministic checks gate. For a generated repo like ours there is one make-or-break
GitHub gotcha (§2.1).

## 1. AI PR-review layer

**Primary recommendation: Anthropic Claude Code in GitHub Actions.**
- `anthropics/claude-code-action@v1` runs on `pull_request: [opened, synchronize]` and can
  invoke a packaged `code-review` skill, or respond to `@claude` mentions. It auto-detects
  interactive vs automation mode. [1]
- **Known gap:** the self-hosted action does *not* reliably post an on-PR review on a clean
  pass (issue #1054). For a guaranteed every-PR review with zero trigger wiring, Anthropic
  points to the **managed GitHub Code Review** product instead. [1]
- The AI reviewer reads `CLAUDE.md` for our review criteria and design philosophy — but this
  is **best-effort context, not enforcement** (§3). [1][5]

**Other tools (CodeRabbit, GitHub Copilot code review/coding agent, Qodo Merge / PR-Agent):**
the research did **not** gather verified capability/pricing claims on these, so I won't
assert specifics. They are viable; if you want a head-to-head, that's a focused follow-up.
Decision driver for us: we already use Claude, so the Claude Code Action (or managed Code
Review) is the lowest-friction, most aligned choice.

**Critical framing:** an AI reviewer is a *reviewer*, not a *gate*. It's probabilistic. Keep
the hard rules (drift, contrast, token quality) in deterministic checks; let the AI catch the
judgment-call stuff (readability, naming intent, "is this duplication justified?").

## 2. Wiring the reported quality gate

Emit every check as a **check run** (Checks API), not a legacy commit status — check runs give
line annotations, richer messaging, and a defined conclusion vocabulary
(`success/failure/neutral/skipped/…`). GitHub Actions runs as a GitHub App, so its jobs already
produce checks. Make the ones that matter **required status checks** with "Do not allow
bypassing" enabled. [a][b]

Surface results three ways (complementary, not either/or):
- **Check runs** — the pass/fail the branch protection gates on. [a][b]
- **Sticky PR comments** via `marocchino/sticky-pull-request-comment`, one per gate using
  distinct `header:` values (e.g. `header: drift`, `header: tokens`, `header: a11y`) so each
  refreshes in place instead of spamming. [c]
- **`$GITHUB_STEP_SUMMARY`** job summaries for the human-readable detail (the contrast table,
  the drift diff).

### 2.1 ⚠️ The generated-repo gotcha (most important finding)

> If a **workflow** is skipped due to **path / branch / commit-message filtering**, its checks
> stay **`Pending` forever** and a PR that requires them is **blocked from merging**. But a
> **job** skipped via an `if:` **conditional** reports **`Success`**. [b]

For us this is decisive: our PRs often touch `src/` *and* the generated `themes/`, and it's
tempting to `paths:`-filter the gate workflow. **Don't.** Always run the gate workflow on PRs;
gate granularity with **job-level `if:` conditionals**, never workflow-level `paths:`. Also note
required checks are evaluated only against the **latest commit SHA**. [b]

## 3. Encoding design principles for agents

- Put the design philosophy and review criteria in a **root `CLAUDE.md`** (Claude reads it
  natively). Keep it **concise** — an ETH Zurich study (Feb 2026) found bloated context files
  can slightly *reduce* task success and raise cost. [5]
- `AGENTS.md` is an open, vendor-neutral alternative, but **Claude Code reads `CLAUDE.md`, not
  `AGENTS.md`** natively, and the "supported by 25+ tools" claim did **not** survive
  verification. Recommendation: maintain `CLAUDE.md` as canonical; optionally symlink/duplicate
  to `AGENTS.md` only if you adopt other agents. [5][refuted]
- **Any rule that must not be violated must be a deterministic CI gate**, not a sentence in
  `CLAUDE.md`. [5]

## 4. Design-token-specific automation

- **DTCG / Style Dictionary.** The W3C DTCG spec reached its first **stable version (2025.10)**
  on 28 Oct 2025 — a vendor-neutral format whose aliases/inheritance/references are *themselves*
  the anti-duplication foundation; Style Dictionary v4 / Terrazzo / Tokens Studio implement it.
  It's a Community Group Candidate Recommendation, **not a formal W3C standard**. [d]
  → **Open decision:** migrate `src/` to DTCG for standardized alias validation, or keep our
  custom YAML pipeline (which already centralizes via `var()`)? My lean: **keep the pipeline**,
  borrow the *principle* (values live once, everything else references). Migration risk
  outweighs the gain at our size. Revisit if the token count grows a lot.
- **Token naming/order linting** is enforceable deterministically (Kong/design-tokens uses
  ESLint `jsonc/*` rules; their breakpoint files document an *intentional* sort override — a
  nice precedent for documented exceptions). Their files are JSON; ours are YAML, so our
  `validate_tokens.py` is the equivalent. [e]
- **WCAG contrast in CI.** Off-the-shelf: `bbc/color-contrast-checker` (`isLevelAA`,
  `checkPairs`) or `get-contrast` (CLI exits non-zero on inaccessible pairs). Both are
  WCAG 2.0/2.1, lightly maintained, Node. [f][g] For us, a small Python `check_contrast.py`
  on the same math avoids a Node dependency and lets us resolve our `var()` chains directly.
- **Visual regression** (Chromatic, snapshots in CI via Playwright) is the heaviest/most
  optional gate and needs a harness that renders the theme (e.g. a representative HA dashboard
  under Playwright — we already have the `make ha-start` instance). Treat as P3/optional. [h]

## 5. The justified-exception escape hatch (your "sometimes we must duplicate")

This is the crux of your constraint, and the research points to a clear pattern:

1. **Grandfather, don't break.** ESLint's **bulk-suppressions** model (Apr 2025): record
   existing violations in a checked-in file, fail only *new* ones, and re-expose a file's
   violations once it exceeds its recorded count — "prevent new violations, improve existing at
   your own pace." [i] Our analogue is **`tools/token_exceptions.yaml`**: a reviewed allowlist
   of intentional duplications/divergences. `main` stays green; new unjustified spread fails.
2. **Per-line, documented exceptions** via inline annotations — ESLint's
   `// eslint-disable-next-line <rule>` pattern. Our analogue:
   ```yaml
   token-rgb-green: 32, 126, 71   # token-lint: allow-duplicate(reason="HA core requires literal here")
   ```
   `validate_tokens.py` honors the annotation **only when a reason is present**, so every
   exception is explicit and reviewable in the diff.
3. **Caveat:** bulk-suppression is *count-based*, not line-precise — a fix + a new violation in
   the same file/rule can net to zero and mask the new one. For hard cases prefer the inline
   annotation (line-precise) over the allowlist (count-based). [i]

Net: the gate enforces "no *new, unjustified* spread" — never "no duplication ever." A valid
duplication becomes a one-line, reviewed, self-documenting decision.

## 6. Recommended end state

```
PR opened/updated
 ├─ Gate workflow (always runs; job-level if: conditionals)
 │   ├─ job: drift        → check run "drift"        (required)   ← check_drift.sh
 │   ├─ job: tokens       → check run "tokens"       (required)   ← validate_tokens.py
 │   ├─ job: contrast     → check run "a11y"         (required)   ← check_contrast.py
 │   ├─ job: token-report → sticky comment (advisory)             ← layer/shape --report
 │   └─ job: visual       → check run "visual" (optional/P3)      ← Chromatic
 ├─ AI review (Claude Code Action / managed Code Review) → review comments (advisory)
 └─ Branch protection: drift + tokens + a11y required, no bypass
```

Local pre-commit runs `drift` + `tokens` (same scripts) so failures surface before push.

---

## Sources (verified Jan 2026)
- [1] Claude Code GitHub Action — https://code.claude.com/docs/en/github-actions ; managed Code Review — https://code.claude.com/docs/en/code-review ; action repo — https://github.com/anthropics/claude-code-action
- [5] Claude memory/CLAUDE.md — https://code.claude.com/docs/en/memory ; AGENTS.md — https://agents.md/
- [a] GitHub status checks — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks ; Checks API — https://docs.github.com/en/rest/checks/runs
- [b] Troubleshooting required status checks (the path-filter/Pending gotcha) — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
- [c] sticky-pull-request-comment — https://github.com/marketplace/actions/sticky-pull-request-comment
- [d] DTCG 2025.10 — https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/ ; format — https://designtokens.org/tr/2025.10/format/
- [e] Kong/design-tokens — https://github.com/Kong/design-tokens
- [f] bbc/color-contrast-checker — https://github.com/bbc/color-contrast-checker
- [g] get-contrast — https://github.com/johno/get-contrast
- [h] Chromatic + Playwright — https://www.chromatic.com/playwright
- [i] ESLint bulk suppressions — https://eslint.org/blog/2025/04/introducing-bulk-suppressions/ ; https://eslint.org/docs/latest/use/suppressions ; inline directives — https://eslint.org/docs/latest/use/configure/rules

## Caveats
- **Pricing/limits NOT researched** for any AI reviewer (Claude Code Action, managed Code
  Review, CodeRabbit, Copilot, Qodo) — these change often; verify before committing budget.
- **Tool comparison is partial:** only Claude Code Action has verified claims; CodeRabbit /
  Copilot / Qodo were not independently verified here.
- Contrast libraries are WCAG 2.0/2.1 (not APCA/WCAG 3) and lightly maintained.
- DTCG 2025.10 is a Community Group Candidate Recommendation, not a formal W3C standard.
- **Refuted/unsupported:** "Kong wires its lint into a *required* status check" (only the
  linting automation is confirmed); "AGENTS.md supported by 25+ tools."
- The path-filter→Pending gotcha (§2.1) is current as of 2026 but is long-standing GitHub
  behavior they've declined to change — re-verify if they ship the requested fix.
