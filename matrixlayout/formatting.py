"""Shared TeX formatting helpers for matrixlayout."""

from __future__ import annotations

from fractions import Fraction
import numbers
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
    bg_color_decorator = r"\colorbox{{{color}}}{{{a}}}"
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


def decorate_tex_entries(
    matrices: Sequence[Sequence[Any]],
    gM: int,
    gN: int,
    decorator: Callable[[str], str],
    *,
    entries: Optional[Iterable[Tuple[int, int]]] = None,
    formater: Callable[[Any], str] = latexify,
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
        rows[i][j] = decorator(formater(rows[i][j]))

    grid[gM][gN] = rows
    return grid


__all__ = ["latexify", "make_decorator", "decorate_tex_entries"]
