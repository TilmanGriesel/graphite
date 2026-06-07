#!/usr/bin/env python3
"""Shared color + token resolution utilities for the Graphite theme quality gates.

Stdlib only (no third-party deps) so the validators that import this run identically
in a git hook, a Make target, CI, and an agent tool.

Two consumers import this module:
  - validate_tokens.py  (token-graph linter)
  - check_contrast.py   (per-build WCAG gate)

Keeping one resolver means the two gates can never disagree about what a value or a
`var()` chain resolves to.

Design notes
------------
* Token source files are flat `key: value` YAML fragments. We parse them by raw text
  line, NOT via a YAML loader, because yaml.safe_load silently collapses duplicate keys
  (`a: 1` / `a: 2` -> {a: 2}) which would hide exactly the duplication we want to catch.
* CSS-ish values we cannot statically evaluate (`color-mix(...)`, `hsl(from ... calc())`)
  resolve to UNRESOLVABLE rather than raising. The contrast gate decides policy for those.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# A value we recognise structurally but cannot reduce to an sRGB triple statically.
UNRESOLVABLE = "UNRESOLVABLE"

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"

# build name -> (theme tokens file, common tokens file, template file)
# Mirrors tools/theme_assembler.py concat order: theme tokens -> common -> template.
BUILDS = {
    "dark": ("tokens_dark.yaml", "tokens_common.yaml", "template.yaml"),
    "light": ("tokens_light.yaml", "tokens_common.yaml", "template.yaml"),
    "eink-dark": ("tokens_eink_dark.yaml", "tokens_common.yaml", "template_eink.yaml"),
    "eink-light": ("tokens_eink_light.yaml", "tokens_common.yaml", "template_eink.yaml"),
}

# Files that hold token primitives/semantics (definitions live here).
TOKEN_FILES = [
    "tokens_common.yaml",
    "tokens_dark.yaml",
    "tokens_light.yaml",
    "tokens_eink_dark.yaml",
    "tokens_eink_light.yaml",
]
TEMPLATE_FILES = ["template.yaml", "template_eink.yaml"]


@dataclass
class Definition:
    """A single `key: value` line from a token/template fragment."""

    file: str
    lineno: int
    key: str
    value: str
    comment: str  # inline comment text after the value (without the leading '#')
    raw: str

    @property
    def annotations(self) -> dict:
        """Parse `token-lint: <directive>(reason="...")` directives from the inline comment.

        Returns a dict like {"allow-duplicate": "HA core needs a literal here"}.
        Only directives carrying a non-empty reason are honoured by the linter.
        """
        out: dict = {}
        if "token-lint:" not in self.comment:
            return out
        body = self.comment.split("token-lint:", 1)[1].strip()
        for m in re.finditer(r'([a-z-]+)\s*(?:\(\s*reason\s*=\s*"([^"]*)"\s*\))?', body):
            directive, reason = m.group(1), m.group(2)
            if directive:
                out[directive] = (reason or "").strip()
        return out


_LINE_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):\s?(?P<rest>.*)$")


def _split_value_comment(rest: str) -> tuple[str, str]:
    """Separate a value from a trailing inline comment.

    Handles quoted values (e.g. `"#fff"`) so the `#` inside the value is not mistaken
    for a comment. For unquoted values, a comment starts at the first ` #` (space-hash).
    """
    rest = rest.rstrip("\n")
    if not rest:
        return "", ""
    if rest[0] in "\"'":
        quote = rest[0]
        end = rest.find(quote, 1)
        if end != -1:
            value = rest[: end + 1]
            after = rest[end + 1 :]
            comment = after.split("#", 1)[1] if "#" in after else ""
            return value.strip(), comment.strip()
    # unquoted: a comment is ' #...'
    idx = rest.find(" #")
    if idx != -1:
        return rest[:idx].strip(), rest[idx + 2 :].strip()
    return rest.strip(), ""


def parse_fragment(path: Path) -> list[Definition]:
    """Parse a flat `key: value` YAML fragment into ordered Definitions (raw-line based)."""
    defs: list[Definition] = []
    for i, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _LINE_RE.match(raw)
        if not m:
            continue
        value, comment = _split_value_comment(m.group("rest"))
        defs.append(
            Definition(
                file=path.name,
                lineno=i,
                key=m.group("key"),
                value=value,
                comment=comment,
                raw=raw.rstrip("\n"),
            )
        )
    return defs


def build_scope(build: str, src_dir: Path = SRC) -> dict[str, str]:
    """Return the merged name->value map for a build (last definition wins)."""
    if build not in BUILDS:
        raise ValueError(f"unknown build {build!r}; expected one of {list(BUILDS)}")
    scope: dict[str, str] = {}
    for fname in BUILDS[build]:
        for d in parse_fragment(src_dir / fname):
            scope[d.key] = d.value
    return scope


# --------------------------------------------------------------------------- colors

_VAR_RE = re.compile(r"var\(\s*--([A-Za-z0-9_.-]+)\s*\)")


def resolve_var(value: str, scope: dict[str, str], _depth: int = 0, _seen: Optional[set] = None) -> str:
    """Expand every `var(--name)` against scope, recursively, with cycle/depth guards."""
    if _seen is None:
        _seen = set()
    if _depth > 40:
        return value

    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name in _seen or name not in scope:
            return m.group(0)  # leave unresolved -> surfaces as UNRESOLVABLE later
        return resolve_var(scope[name], scope, _depth + 1, _seen | {name})

    return _VAR_RE.sub(repl, value)


_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_RE = re.compile(r"^rgba?\(\s*([^)]+)\s*\)$", re.IGNORECASE)
_TRIPLE_RE = re.compile(r"^\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*$")


def parse_color(value: str):
    """Parse a resolved literal into (r, g, b, a) floats, or UNRESOLVABLE.

    Accepts: bare `R, G, B` triples, `rgb(...)`, `rgba(...)` (inner parts may themselves
    be `R, G, B` triples), `#rgb`, `#rrggbb`. Anything with leftover var()/color-mix/hsl
    is UNRESOLVABLE.
    """
    if value is None:
        return UNRESOLVABLE
    v = value.strip().strip("\"'").strip()
    if not v or "var(" in v or "color-mix(" in v or "hsl(" in v or "calc(" in v:
        return UNRESOLVABLE

    m = _HEX_RE.match(v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)

    m = _RGB_RE.match(v)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) in (3, 4):
            try:
                r, g, b = (float(parts[0]), float(parts[1]), float(parts[2]))
                a = float(parts[3]) if len(parts) == 4 else 1.0
                return (r, g, b, a)
            except ValueError:
                return UNRESOLVABLE
        return UNRESOLVABLE

    m = _TRIPLE_RE.match(v)
    if m:
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)), 1.0)

    return UNRESOLVABLE


def composite(fg, bg):
    """Flatten a translucent foreground (r,g,b,a) over an opaque background (r,g,b[,a])."""
    fr, fg_, fb, fa = fg
    br, bgc, bb = bg[0], bg[1], bg[2]
    return (
        fa * fr + (1 - fa) * br,
        fa * fg_ + (1 - fa) * bgc,
        fa * fb + (1 - fa) * bb,
    )


def _lin(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb) -> float:
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg, bg) -> float:
    """WCAG 2.x sRGB contrast ratio between a resolved fg and an opaque bg.

    fg may carry alpha; it is composited over bg first.
    """
    fg_rgb = composite(fg, bg) if len(fg) == 4 and fg[3] < 1.0 else (fg[0], fg[1], fg[2])
    l1 = relative_luminance(fg_rgb)
    l2 = relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def resolve_to_rgba(value: str, scope: dict[str, str]):
    """Resolve a raw value (possibly var()-laden) to (r,g,b,a) or UNRESOLVABLE."""
    return parse_color(resolve_var(value, scope))


if __name__ == "__main__":
    # Lightweight self-test against the real tree.
    scope = build_scope("dark")
    assert parse_color("32, 126, 71") == (32.0, 126.0, 71.0, 1.0)
    assert parse_color("rgb(10, 104, 127)")[:3] == (10.0, 104.0, 127.0)
    assert parse_color("#fff") == (255, 255, 255, 1.0)
    assert parse_color("color-mix(in srgb, white 40%, black)") == UNRESOLVABLE
    badge = resolve_to_rgba("var(--token-color-background-label-badge-green)", scope)
    text = resolve_to_rgba("var(--token-color-text-primary)", scope)
    assert badge != UNRESOLVABLE and text != UNRESOLVABLE, (badge, text)
    ratio = contrast_ratio(text, (badge[0], badge[1], badge[2]))
    print(f"self-test OK: dark label-badge-green vs text-primary = {ratio:.2f}:1")
