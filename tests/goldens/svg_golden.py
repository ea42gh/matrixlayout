"""Stable SVG golden comparison helpers.

dvisvgm may emit font glyph definitions and glyph ids differently across
invocations and TeX/font cache states. Those definitions are renderer internals;
the matrixlayout golden tests should compare the rendered layout body, crop, and
graphics, not volatile font paths.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

normalize_svg = pytest.importorskip("jupyter_tikz.svg_normalize").normalize_svg

_DEFS_RE = re.compile(r"\s*<defs>.*?</defs>\s*", flags=re.DOTALL)
_HREF_RE = re.compile(r"\s+(?:xlink:)?href=['\"]#[^'\"]+['\"]")
_ID_RE = re.compile(r"\s+id=['\"][^'\"]+['\"]")
_SPACE_RE = re.compile(r"\s+")


def normalize_svg_golden(svg_text: str) -> str:
    """Normalize SVG while ignoring volatile font glyph definitions."""

    normalized = normalize_svg(svg_text)
    normalized = _DEFS_RE.sub(" ", normalized)
    normalized = _HREF_RE.sub("", normalized)
    normalized = _ID_RE.sub("", normalized)
    return _SPACE_RE.sub(" ", normalized).strip()


def assert_svg_matches_golden(svg_text: str, golden_path: Path) -> None:
    assert normalize_svg_golden(svg_text) == normalize_svg_golden(golden_path.read_text())
