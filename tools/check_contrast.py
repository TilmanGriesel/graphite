#!/usr/bin/env python3
"""Per-build WCAG contrast gate for the Graphite theme.

Resolves foreground/background pairs through the theme's REAL consumer var() wiring
(e.g. `var(--label-badge-text-color)` over `var(--label-badge-green)`) — not by token-name
heuristics — and checks the WCAG 2.x contrast ratio per build (dark/light/eink). The same
logical pairing can pass in one build and fail in another, so every pair is checked per build.

Pairs are declared in tools/contrast_pairs.yaml. Pre-existing failures are grandfathered in
that file's `baseline_failures` so the gate goes green today while blocking NEW regressions.

Usage:  check_contrast.py (--build dark|light|eink-dark|eink-light | --all) [--json] [--strict]
Exit:   0 = all pass (or waived) · 1 = a non-baseline pair fails · 2 = internal error
        --strict also fails on UNRESOLVABLE pairs (color-mix/relative-hsl/undefined vars).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import color_utils as cu

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

MANIFEST = cu.REPO_ROOT / "tools" / "contrast_pairs.yaml"
THRESHOLDS = {"normal": 4.5, "large": 3.0}


def hexs(rgba):
    return "#%02x%02x%02x" % (round(rgba[0]), round(rgba[1]), round(rgba[2]))


def evaluate(pair, build):
    scope = cu.build_scope(build)
    fg = cu.resolve_to_rgba(pair["fg"], scope)
    bg = cu.resolve_to_rgba(pair["bg"], scope)
    size = pair.get("size", "normal")
    threshold = THRESHOLDS.get(size, 4.5)
    if fg is cu.UNRESOLVABLE or bg is cu.UNRESOLVABLE:
        return {"build": build, "name": pair["name"], "status": "unresolvable",
                "fg": pair["fg"], "bg": pair["bg"], "threshold": threshold}
    # If the background is translucent, composite it over the build's base surface.
    if bg[3] < 1.0:
        base = cu.resolve_to_rgba(pair.get("over", "var(--token-color-background-base)"), scope)
        if base is cu.UNRESOLVABLE:
            base = (0, 0, 0, 1.0)
        bg = (*cu.composite(bg, base), 1.0)
    bg_rgb = (bg[0], bg[1], bg[2])
    ratio = cu.contrast_ratio(fg, bg_rgb)
    return {
        "build": build, "name": pair["name"],
        "status": "pass" if ratio >= threshold else "fail",
        "ratio": round(ratio, 2), "threshold": threshold,
        "fg_hex": hexs(fg), "bg_hex": hexs(bg_rgb),
        "fg": pair["fg"], "bg": pair["bg"],
    }


def run():
    ap = argparse.ArgumentParser(description="Graphite per-build WCAG contrast gate")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--build", choices=list(cu.BUILDS))
    g.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="fail on UNRESOLVABLE pairs too")
    args = ap.parse_args()

    if yaml is None:
        print("check_contrast: PyYAML is required", file=sys.stderr)
        return 2
    data = yaml.safe_load(MANIFEST.read_text()) or {}
    pairs = data.get("pairs", [])
    baseline = {(b["name"], b["build"]) for b in data.get("baseline_failures", []) if isinstance(b, dict)}

    builds = list(cu.BUILDS) if args.all or not args.build else [args.build]
    results = []
    for pair in pairs:
        pair_builds = [b for b in pair.get("builds", builds) if b in builds]
        for build in pair_builds:
            results.append(evaluate(pair, build))

    blocking, waived, unresolved, passed = [], [], [], []
    for r in results:
        if r["status"] == "pass":
            passed.append(r)
        elif r["status"] == "fail":
            (waived if (r["name"], r["build"]) in baseline else blocking).append(r)
        else:  # unresolvable
            if args.strict and (r["name"], r["build"]) not in baseline:
                blocking.append(r)
            else:
                unresolved.append(r)

    if args.json:
        print(json.dumps({"blocking": blocking, "waived": waived, "unresolved": unresolved,
                          "passed": passed, "ok": not blocking}, indent=2))
    else:
        for r in results:
            if r["status"] == "pass":
                continue
            tag = {"fail": "❌", "unresolvable": "…"}[r["status"]]
            wv = "  (baseline-waived)" if (r["name"], r["build"]) in baseline else ""
            if r["status"] == "fail":
                print(f"{tag} [{r['build']}] {r['name']}: {r['ratio']}:1 "
                      f"(need {r['threshold']}:1)  {r['fg_hex']} on {r['bg_hex']}{wv}")
            else:
                print(f"{tag} [{r['build']}] {r['name']}: UNRESOLVABLE ({r['fg']} / {r['bg']}){wv}")
        print(f"\n{len(passed)} pass · {len(blocking)} blocking · "
              f"{len(waived)} baseline-waived · {len(unresolved)} unresolvable")
        print("✅ check_contrast: no new contrast regressions" if not blocking
              else "❌ check_contrast: new contrast failure(s) above")

    return 0 if not blocking else 1


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as exc:  # noqa: BLE001
        print(f"check_contrast: internal error: {exc}", file=sys.stderr)
        sys.exit(2)
