"""Back-substitution layout template.

This module migrates BACKSUBST_TEMPLATE from the legacy ``itikz.nicematrix``
implementation.

The template is treated as a layout/presentation artifact only:

- The caller provides representation strings for the system, cascade, and
  solution blocks.
- matrixlayout generates TeX and (optionally) renders SVG via the
  :func:`jupyter_tikz.render_svg` rendering boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence, Union, List, Tuple

from .jinja_env import render_template
from .render import render_svg
from .shortcascade import mk_shortcascade_lines
from .formatting import apply_decorator, expand_entry_selectors


def _as_lines(value: Union[str, Sequence[str], None]) -> list[str]:
    """Normalize a value to a list of strings.

    Julia/PythonCall commonly passes tuples instead of lists; we accept both.
    """

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _as_scale(value: Optional[Union[str, float, int]]) -> Optional[str]:
    """Normalize a scale value to the string used by the TeX template.

    Accepts:
    - ``None``: no scaling wrapper is emitted.
    - ``str``: passed through verbatim (caller-managed formatting).
    - numeric: formatted with ``format(value, 'g')`` to avoid TeX-unfriendly
      representations (e.g., excessive trailing zeros).
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    # Stable, TeX-friendly numeric formatting
    return format(value, "g")


def _apply_line_decorators(
    lines: List[str],
    decorators: Optional[Sequence[Any]],
    block: str,
    *,
    strict: bool,
) -> List[str]:
    if not decorators or not lines:
        return lines
    nrows, ncols = len(lines), 1
    block_key = block.lower()
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("block", spec_item.get("target"))
        if key is None or str(key).lower() not in {block_key, f"{block_key}_txt"}:
            continue
        dec = spec_item.get("decorator")
        if not callable(dec):
            raise ValueError("decorator must be callable")
        applied = 0
        for i, j in expand_entry_selectors(spec_item.get("entries"), nrows, ncols, allow_int=True):
            if i < 0 or i >= nrows or j != 0:
                continue
            base = lines[i]
            lines[i] = apply_decorator(dec, i, j, base, base)
            applied += 1
        if strict and applied == 0:
            raise ValueError("decorator selector did not match any entries")
    return lines


@dataclass(frozen=True)
class BacksubstContext:
    preamble: str = ""
    system_txt: str = ""
    cascade_txt: tuple[str, ...] = ()
    solution_txt: str = ""

    show_system: bool = True
    show_cascade: bool = True
    show_solution: bool = True
    fig_scale: Optional[str] = None

    def as_dict(self) -> Mapping[str, Any]:
        return {
            "preamble": self.preamble,
            "system_txt": self.system_txt,
            "cascade_txt": list(self.cascade_txt),
            "solution_txt": self.solution_txt,
            "show_system": self.show_system,
            "show_cascade": self.show_cascade,
            "show_solution": self.show_solution,
            "fig_scale": self.fig_scale,
        }


def backsubst_tex(
    *,
    preamble: str = "",
    system_txt: str = "",
    cascade_txt: Union[str, Sequence[str], None] = None,
    cascade_trace: Any = None,
    solution_txt: str = "",
    show_system: bool = True,
    show_cascade: bool = True,
    show_solution: bool = True,
    fig_scale: Optional[Union[str, float, int]] = None,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
) -> str:
    """Render the back-substitution TeX document.

    Parameters are intentionally representation-oriented: callers pass LaTeX
    snippets for each block.
    """

    if cascade_txt is None and cascade_trace is not None:
        cascade_txt = mk_shortcascade_lines(cascade_trace)

    system_lines = _apply_line_decorators([system_txt] if system_txt else [], decorators, "system", strict=strict)
    cascade_lines = _apply_line_decorators(_as_lines(cascade_txt), decorators, "cascade", strict=strict)
    solution_lines = _apply_line_decorators([solution_txt] if solution_txt else [], decorators, "solution", strict=strict)

    ctx = BacksubstContext(
        preamble=preamble,
        system_txt=system_lines[0] if system_lines else system_txt,
        cascade_txt=tuple(cascade_lines),
        solution_txt=solution_lines[0] if solution_lines else solution_txt,
        show_system=bool(show_system),
        show_cascade=bool(show_cascade),
        show_solution=bool(show_solution),
        fig_scale=_as_scale(fig_scale),
    )

    return render_template("backsubst.tex.j2", ctx.as_dict())


def backsubst_svg(
    *,
    preamble: str = "",
    system_txt: str = "",
    cascade_txt: Union[str, Sequence[str], None] = None,
    cascade_trace: Any = None,
    solution_txt: str = "",
    show_system: bool = True,
    show_cascade: bool = True,
    show_solution: bool = True,
    fig_scale: Optional[Union[str, float, int]] = None,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
) -> str:
    """Render the back-substitution document to SVG using jupyter_tikz."""

    tex = backsubst_tex(
        preamble=preamble,
        system_txt=system_txt,
        cascade_txt=cascade_txt,
        cascade_trace=cascade_trace,
        solution_txt=solution_txt,
        show_system=show_system,
        show_cascade=show_cascade,
        show_solution=show_solution,
        fig_scale=fig_scale,
        decorators=decorators,
        strict=strict,
    )
    return render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
