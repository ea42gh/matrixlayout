"""Shared TeX formatting helpers for matrixlayout.

Selector helpers and decorator presets are convenience utilities for building
decorator specs. Example:

    dec = decorator_box()
    specs = [{"grid": (0, 1), "entries": [sel_entry(0, 0)], "decorator": dec}]
"""

from __future__ import annotations

from fractions import Fraction
import inspect
import numbers
import re
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple


def latexify(x: Any) -> str:
    """Return a TeX-ready representation for a scalar-like value."""
    if isinstance(x, str):
        return x

    if isinstance(x, (tuple, list)) and len(x) == 2 and all(isinstance(v, int) for v in x):
        num, den = x
        return rf"\frac{{{num}}}{{{den}}}"

    if isinstance(x, Fraction):
        return rf"\frac{{{x.numerator}}}{{{x.denominator}}}"

    try:
        import sympy as sym  # type: ignore

        if isinstance(x, sym.Basic):
            return sym.latex(x)
    except Exception:
        pass

    if isinstance(x, numbers.Number) and not isinstance(x, bool):
        return format(x, "g")

    return str(x)


def norm_str(x: Any) -> Any:
    """Normalize Julia/PythonCall/PyCall string-like values."""
    if x is None:
        return None
    s = x if isinstance(x, str) else str(x)
    s = s.strip()
    if s.startswith(":"):
        return s[1:]
    if "Symbol(" in s:
        match = re.search(r"Symbol\((.*)\)", s)
        if match:
            inner = match.group(1).strip()
            if inner.startswith(":"):
                inner = inner[1:]
            if len(inner) >= 2 and inner[0] == inner[-1] and inner[0] in ("'", '"'):
                inner = inner[1:-1]
            return inner
    return s

def make_decorator(
    *,
    text_color: str = "black",
    bg_color: Optional[str] = None,
    text_bg: Optional[str] = None,
    boxed: Optional[bool] = None,
    box_color: Optional[str] = None,
    bf: Optional[bool] = None,
    move_right: bool = False,
    delim: Optional[str] = None,
) -> Callable[[str], str]:
    """Return a decorator function for TeX strings (legacy-compatible)."""
    box_decorator = r"\boxed{{{a}}}"
    coloredbox_decorator = r"\colorboxed{{{color}}}{{{a}}}"
    color_decorator = r"\Block[draw={text_color},fill={bg_color}]<>{{{a}}}"
    txt_color_decorator = r"\color{{{color}}}{{{a}}}"
    # Ensure math entries (e.g., \frac) render correctly inside \colorbox.
    bg_color_decorator = r"\colorbox{{{color}}}{{\ensuremath{{{a}}}}}"
    bf_decorator = r"\mathbf{{{a}}}"
    rlap_decorator = r"\mathrlap{{{a}}}"
    delim_decorator = r"{delim}{a}{delim}"

    def _decorate(x: str) -> str:
        if bf:
            x = bf_decorator.format(a=x)
        if boxed:
            x = box_decorator.format(a=x)
        if box_color:
            x = coloredbox_decorator.format(a=x, color=box_color)
        if bg_color:
            x = bg_color_decorator.format(a=x, color=bg_color)
        if text_bg:
            x = color_decorator.format(a=x, text_color=text_color, bg_color=text_bg)
        if text_color:
            x = txt_color_decorator.format(color=text_color, a=x)
        if move_right:
            x = rlap_decorator.format(a=x)
        if delim:
            x = delim_decorator.format(delim=delim, a=x)
        return x

    return _decorate


def decorator_box(*, color: Optional[str] = None) -> Callable[[str], str]:
    """Return a decorator that draws a (possibly colored) box around TeX."""
    if color:
        return make_decorator(box_color=color)
    return make_decorator(boxed=True)


def decorator_color(color: str) -> Callable[[str], str]:
    """Return a decorator that colors TeX."""
    return make_decorator(text_color=color)


def decorator_bg(color: str) -> Callable[[str], str]:
    """Return a decorator that adds a background color."""
    return make_decorator(bg_color=color)


def decorator_bf() -> Callable[[str], str]:
    """Return a decorator that boldfaces TeX."""
    return make_decorator(bf=True)


def sel_entry(i: int, j: int) -> Tuple[int, int]:
    """Selector for a single matrix entry."""
    return (int(i), int(j))


def sel_box(top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Selector for a rectangular entry region."""
    return ((int(top_left[0]), int(top_left[1])), (int(bottom_right[0]), int(bottom_right[1])))


def sel_row(i: int) -> dict:
    """Selector for an entire row."""
    return {"row": int(i)}


def sel_col(j: int) -> dict:
    """Selector for an entire column."""
    return {"col": int(j)}


def sel_rows(rows: Sequence[int]) -> dict:
    """Selector for multiple rows."""
    return {"rows": [int(r) for r in rows]}


def sel_cols(cols: Sequence[int]) -> dict:
    """Selector for multiple columns."""
    return {"cols": [int(c) for c in cols]}


def sel_all() -> dict:
    """Selector for all entries."""
    return {"all": True}


def sel_vec(group: int, vec: int, entry: int) -> Tuple[int, int, int]:
    """Selector for a vector entry in an eigenproblem row."""
    return (int(group), int(vec), int(entry))


def sel_vec_range(
    start: Tuple[int, int, int],
    end: Tuple[int, int, int],
) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Selector for a contiguous vector entry range."""
    return (
        (int(start[0]), int(start[1]), int(start[2])),
        (int(end[0]), int(end[1]), int(end[2])),
    )

def decorate_tex_entries(
    matrices: Sequence[Sequence[Any]],
    gM: int,
    gN: int,
    decorator: Callable[[str], str],
    *,
    entries: Optional[Iterable[Tuple[int, int]]] = None,
    formatter: Callable[[Any], str] = latexify,
) -> Sequence[Sequence[Any]]:
    """Apply a decorator to selected entries in a grid matrix (in-place)."""
    grid = [list(r) for r in matrices]
    if gM < 0 or gN < 0 or gM >= len(grid) or gN >= len(grid[gM]):
        raise IndexError("grid position out of range")

    target = grid[gM][gN]
    if target is None:
        return grid

    if hasattr(target, "tolist"):
        rows = target.tolist()
    else:
        rows = [list(r) for r in target]

    if not rows:
        return grid

    nrows = len(rows)
    ncols = len(rows[0]) if rows[0] else 0
    if entries is None:
        entries = [(i, j) for i in range(nrows) for j in range(ncols)]

    for i, j in entries:
        if i < 0 or j < 0 or i >= nrows or j >= ncols:
            continue
        rows[i][j] = decorator(formatter(rows[i][j]))

    grid[gM][gN] = rows
    return grid


def expand_entry_selectors(
    entries: Optional[Iterable[Any]],
    nrows: int,
    ncols: int,
    *,
    allow_int: bool = False,
    filter_bounds: bool = False,
) -> set[Tuple[int, int]]:
    """Expand selector specs into entry coordinates."""
    out: set[Tuple[int, int]] = set()
    if entries is None:
        for i in range(nrows):
            for j in range(ncols):
                out.add((i, j))
        return out
    for ent in entries:
        if allow_int and isinstance(ent, int):
            out.add((int(ent), 0))
            continue
        if isinstance(ent, dict):
            if ent.get("all"):
                for i in range(nrows):
                    for j in range(ncols):
                        out.add((i, j))
            if "row" in ent:
                i = int(ent["row"])
                for j in range(ncols):
                    out.add((i, j))
            if "col" in ent:
                j = int(ent["col"])
                for i in range(nrows):
                    out.add((i, j))
            if "rows" in ent:
                for i in ent["rows"]:
                    for j in range(ncols):
                        out.add((int(i), j))
            if "cols" in ent:
                for j in ent["cols"]:
                    for i in range(nrows):
                        out.add((i, int(j)))
            continue
        if isinstance(ent, (list, tuple)) and len(ent) == 2:
            a, b = ent
            if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == 2 and len(b) == 2:
                i0, j0 = int(a[0]), int(a[1])
                i1, j1 = int(b[0]), int(b[1])
                for i in range(min(i0, i1), max(i0, i1) + 1):
                    for j in range(min(j0, j1), max(j0, j1) + 1):
                        out.add((i, j))
            else:
                out.add((int(a), int(b)))
    if filter_bounds:
        out = {(i, j) for (i, j) in out if 0 <= i < nrows and 0 <= j < ncols}
    return out


def apply_decorator(dec: Callable[..., str], i: int, j: int, v: Any, tex: str) -> str:
    """Apply a decorator that accepts 1 or 4 positional args."""
    try:
        params = [
            p for p in inspect.signature(dec).parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
    except Exception:
        return dec(tex)
    if len(params) >= 4:
        return dec(i, j, v, tex)
    if len(params) == 1:
        return dec(tex)
    raise ValueError("Decorator must accept either 1 argument (tex) or 4 arguments (row,col,value,tex).")


__all__ = [
    "latexify",
    "norm_str",
    "make_decorator",
    "decorate_tex_entries",
    "expand_entry_selectors",
    "apply_decorator",
    "decorator_box",
    "decorator_color",
    "decorator_bg",
    "decorator_bf",
    "sel_entry",
    "sel_box",
    "sel_row",
    "sel_col",
    "sel_rows",
    "sel_cols",
    "sel_all",
    "sel_vec",
    "sel_vec_range",
]
