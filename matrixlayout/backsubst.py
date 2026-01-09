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
import inspect
from typing import Any, Iterable, Mapping, Optional, Sequence, Union, List, Tuple

from .jinja_env import render_template
from .render import render_svg
from .shortcascade import mk_shortcascade_lines


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


def _expand_entries(entries: Optional[Iterable[Any]], nrows: int, ncols: int) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    if entries is None:
        return [(i, j) for i in range(nrows) for j in range(ncols)]
    for ent in entries:
        if isinstance(ent, int):
            out.append((int(ent), 0))
            continue
        if isinstance(ent, dict):
            if ent.get("all"):
                out.extend((i, j) for i in range(nrows) for j in range(ncols))
            if "row" in ent:
                i = int(ent["row"])
                out.extend((i, j) for j in range(ncols))
            if "col" in ent:
                j = int(ent["col"])
                out.extend((i, j) for i in range(nrows))
            if "rows" in ent:
                for i in ent["rows"]:
                    out.extend((int(i), j) for j in range(ncols))
            if "cols" in ent:
                for j in ent["cols"]:
                    out.extend((i, int(j)) for i in range(nrows))
            continue
        if isinstance(ent, (list, tuple)) and len(ent) == 2:
            a, b = ent
            if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == 2 and len(b) == 2:
                i0, j0 = int(a[0]), int(a[1])
                i1, j1 = int(b[0]), int(b[1])
                for i in range(min(i0, i1), max(i0, i1) + 1):
                    for j in range(min(j0, j1), max(j0, j1) + 1):
                        out.append((i, j))
            else:
                out.append((int(a), int(b)))
    return out


def _apply_decorator(dec: Any, i: int, j: int, v: Any, tex: str) -> str:
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


def _apply_line_decorators(lines: List[str], decorators: Optional[Sequence[Any]], block: str) -> List[str]:
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
        for i, j in _expand_entries(spec_item.get("entries"), nrows, ncols):
            if i < 0 or i >= nrows or j != 0:
                continue
            base = lines[i]
            lines[i] = _apply_decorator(dec, i, j, base, base)
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
) -> str:
    """Render the back-substitution TeX document.

    Parameters are intentionally representation-oriented: callers pass LaTeX
    snippets for each block.
    """

    if cascade_txt is None and cascade_trace is not None:
        cascade_txt = mk_shortcascade_lines(cascade_trace)

    system_lines = _apply_line_decorators([system_txt] if system_txt else [], decorators, "system")
    cascade_lines = _apply_line_decorators(_as_lines(cascade_txt), decorators, "cascade")
    solution_lines = _apply_line_decorators([solution_txt] if solution_txt else [], decorators, "solution")

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
    )
    return render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
