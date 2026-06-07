#!/usr/bin/env python3
"""Token-graph linter for the Graphite theme source.

Enforces the design principles in .claude/DESIGN-GUIDELINE.md against the hand-edited
`src/` fragments (never against generated `themes/`).

Checks
------
BLOCKING (fail the gate unless grandfathered/annotated):
  * orphan            — a `token-*` defined but reachable from no consumer (dead token)
  * duplicate-literal — two `token-rgb-*` primitives in one file share the same color literal
  * template-literal  — a raw color literal in template*.yaml (templates must reference tokens)

ADVISORY (reported, never fail the gate — `--strict-advisory` to promote):
  * literal-outside-primitive — a color literal in a non-`token-rgb-*` definition
  * layer-equivalence         — modern token vs legacy `rgb-*-color` value drift

Escape hatches (so justified duplication never breaks the build)
  * inline:  `key: value  # token-lint: allow-<check>(reason="...")`  (reason required)
  * file:    tools/token_exceptions.yaml  (grandfathered/structural exceptions, reviewed in PRs)

Exit: 0 clean · 1 blocking violations · 2 internal error.
Output: human-readable, or machine-readable with --json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import color_utils as cu

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REPO_ROOT = cu.REPO_ROOT
SRC = cu.SRC
EXCEPTIONS_FILE = REPO_ROOT / "tools" / "token_exceptions.yaml"

VAR_RE = cu._VAR_RE
PRIMITIVE_PREFIX = "token-rgb-"


def load_exceptions(path: Path) -> dict:
    if not path.exists():
        return {}
    if yaml is None:
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data if isinstance(data, dict) else {}


def is_color_literal(value: str) -> bool:
    return cu.parse_color(value) is not cu.UNRESOLVABLE and "var(" not in value


def color_key(value: str):
    c = cu.parse_color(value)
    if c is cu.UNRESOLVABLE:
        return None
    return tuple(round(x, 3) for x in c)


# --------------------------------------------------------------------------- checks


def check_orphans(token_defs, template_defs):
    """Reachability from non-token-* roots; a token-* never reached is an orphan."""
    all_defs = token_defs + template_defs
    edges: dict[str, set] = {}
    for d in all_defs:
        edges.setdefault(d.key, set()).update(VAR_RE.findall(d.value))
    roots = [d.key for d in all_defs if not d.key.startswith("token-")]
    reachable: set = set()
    stack = list(roots)
    while stack:
        name = stack.pop()
        for ref in edges.get(name, ()):  # var(--ref)
            if ref not in reachable:
                reachable.add(ref)
                stack.append(ref)
    defined_tokens = {d.key for d in token_defs if d.key.startswith("token-")}
    orphans = sorted(defined_tokens - reachable)
    # map orphan -> first defining (file, line)
    where = {}
    for d in token_defs:
        if d.key in orphans and d.key not in where:
            where[d.key] = (d.file, d.lineno)
    return [
        {"check": "orphan", "token": k, "file": where[k][0], "line": where[k][1],
         "detail": f"{k} is defined but referenced by no var(--{k}) consumer"}
        for k in orphans
    ]


def check_duplicate_literals(token_defs):
    """Two token-rgb-* primitives in the SAME file carrying the same literal."""
    by_file: dict[str, list] = {}
    for d in token_defs:
        if d.key.startswith(PRIMITIVE_PREFIX) and is_color_literal(d.value):
            by_file.setdefault(d.file, []).append(d)
    out = []
    for file, defs in by_file.items():
        groups: dict = {}
        for d in defs:
            groups.setdefault(color_key(d.value), []).append(d)
        for ckey, members in groups.items():
            if len(members) > 1:
                canonical = members[0].key
                for d in members[1:]:
                    out.append({
                        "check": "duplicate-literal", "token": d.key, "file": d.file,
                        "line": d.lineno,
                        "detail": f"{d.key} duplicates literal {d.value} "
                                  f"(canonical: {canonical}); reference rgb(var(--{canonical})) instead",
                    })
    return out


def check_template_literals(template_defs):
    out = []
    for d in template_defs:
        if is_color_literal(d.value):
            out.append({
                "check": "template-literal", "token": d.key, "file": d.file, "line": d.lineno,
                "detail": f"{d.key}: raw literal {d.value!r} in a template; reference a token instead",
            })
    return out


def check_literal_outside_primitive(token_defs):
    """ADVISORY: a color literal in a non-primitive definition."""
    out = []
    for d in token_defs:
        if d.key.startswith(PRIMITIVE_PREFIX):
            continue
        if d.key.startswith("token-") and is_color_literal(d.value):
            out.append({
                "check": "literal-outside-primitive", "token": d.key, "file": d.file,
                "line": d.lineno,
                "detail": f"{d.key} holds a literal {d.value}; semantic tokens should reference a primitive",
            })
    return out


LEGACY_MAP = {
    "rgb-warning-color": "token-color-feedback-warning",
    "rgb-error-color": "token-color-feedback-error",
    "rgb-success-color": "token-color-feedback-success",
    "rgb-info-color": "token-color-feedback-info",
}


def check_layer_equivalence(token_defs):
    """ADVISORY: legacy rgb-*-color should equal its modern feedback token, per file."""
    out = []
    by_file: dict[str, dict] = {}
    for d in token_defs:
        by_file.setdefault(d.file, {})[d.key] = d
    for file, defs in by_file.items():
        scope = {k: v.value for k, v in defs.items()}
        for legacy, modern in LEGACY_MAP.items():
            if legacy in defs and modern in defs:
                lv = cu.parse_color(cu.resolve_var(defs[legacy].value, scope))
                mv = cu.parse_color(cu.resolve_var(defs[modern].value, scope))
                if lv is not cu.UNRESOLVABLE and mv is not cu.UNRESOLVABLE and lv != mv:
                    out.append({
                        "check": "layer-equivalence", "token": legacy, "file": file,
                        "line": defs[legacy].lineno,
                        "detail": f"{legacy} ({lv}) != {modern} ({mv}) in {file}",
                    })
    return out


# --------------------------------------------------------------------------- exceptions


def annotated_allow(defn, check) -> bool:
    """An inline `# token-lint: allow-<check>(reason="...")` with a non-empty reason."""
    ann = defn.annotations
    key = f"allow-{check}"
    return key in ann and bool(ann[key])


def excepted(violation, exceptions, defs_by_keyfile) -> bool:
    check = violation["check"]
    entries = exceptions.get(check.replace("-", "_"), []) or exceptions.get(check, [])
    for e in entries:
        if not isinstance(e, dict):
            continue
        if e.get("token") not in (None, violation.get("token")):
            continue
        if e.get("key") not in (None, violation.get("token")):
            continue
        if e.get("file") not in (None, violation.get("file")):
            continue
        if not e.get("reason"):
            continue
        return True
    # inline annotation
    d = defs_by_keyfile.get((violation.get("token"), violation.get("file")))
    if d and annotated_allow(d, check):
        return True
    return False


# --------------------------------------------------------------------------- main

BLOCKING = {"orphan", "duplicate-literal", "template-literal"}


def run():
    parser = argparse.ArgumentParser(description="Graphite token-graph linter")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allowlist", default=str(EXCEPTIONS_FILE))
    parser.add_argument("--strict-advisory", action="store_true",
                        help="treat advisory findings as blocking too")
    args = parser.parse_args()

    token_defs = []
    for fname in cu.TOKEN_FILES:
        token_defs += cu.parse_fragment(SRC / fname)
    template_defs = []
    for fname in cu.TEMPLATE_FILES:
        template_defs += cu.parse_fragment(SRC / fname)

    exceptions = load_exceptions(Path(args.allowlist))
    defs_by_keyfile = {(d.key, d.file): d for d in token_defs + template_defs}

    findings = (
        check_orphans(token_defs, template_defs)
        + check_duplicate_literals(token_defs)
        + check_template_literals(template_defs)
        + check_literal_outside_primitive(token_defs)
        + check_layer_equivalence(token_defs)
    )

    blocking, advisory, waived = [], [], []
    for v in findings:
        is_block = v["check"] in BLOCKING or args.strict_advisory
        if excepted(v, exceptions, defs_by_keyfile):
            waived.append(v)
        elif is_block:
            blocking.append(v)
        else:
            advisory.append(v)

    if args.json:
        print(json.dumps({"blocking": blocking, "advisory": advisory, "waived": waived,
                          "ok": not blocking}, indent=2))
    else:
        def show(title, items):
            if items:
                print(f"\n{title} ({len(items)}):")
                for v in items:
                    print(f"  [{v['check']}] {v['file']}:{v['line']}  {v['detail']}")
        if blocking:
            show("❌ BLOCKING", blocking)
        show("⚠️  ADVISORY (non-blocking)", advisory)
        if waived:
            print(f"\nℹ️  {len(waived)} finding(s) waived via token_exceptions.yaml / inline annotation")
        if not blocking:
            print("\n✅ validate_tokens: no blocking violations")

    return 0 if not blocking else 1


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as exc:  # noqa: BLE001
        print(f"validate_tokens: internal error: {exc}", file=sys.stderr)
        sys.exit(2)
