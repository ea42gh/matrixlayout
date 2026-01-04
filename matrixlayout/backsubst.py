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
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

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
) -> str:
    """Render the back-substitution TeX document.

    Parameters are intentionally representation-oriented: callers pass LaTeX
    snippets for each block.
    """

    if cascade_txt is None and cascade_trace is not None:
        cascade_txt = mk_shortcascade_lines(cascade_trace)

    ctx = BacksubstContext(
        preamble=preamble,
        system_txt=system_txt,
        cascade_txt=tuple(_as_lines(cascade_txt)),
        solution_txt=solution_txt,
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
    )
    return render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
