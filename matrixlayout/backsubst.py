"""Back-substitution layout template.

This module implements the BACKSUBST_TEMPLATE layout.

The template is treated as a layout/presentation artifact only:

- The caller provides representation strings for the system, cascade, and
  solution blocks.
- matrixlayout generates TeX and (optionally) renders SVG via the
  :func:`jupyter_tikz.render_svg` rendering boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Union

from .backsubst_helpers import apply_line_decorators as _apply_line_decorators
from .backsubst_helpers import as_lines as _as_lines
from .backsubst_helpers import as_scale as _as_scale
from .jinja_env import render_template
from .render import _resolve_render_svg_kwargs, render_svg
from .shortcascade import mk_shortcascade_lines


@dataclass(frozen=True)
class BacksubstContext:
    body_preamble: str = ""
    system_txt: str = ""
    cascade_txt: tuple[str, ...] = ()
    solution_txt: str = ""

    show_system: bool = True
    show_cascade: bool = True
    show_solution: bool = True
    fig_scale: Optional[str] = None

    def as_dict(self) -> Mapping[str, Any]:
        return {
            "body_preamble": self.body_preamble,
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
    body_preamble: str = "",
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
        body_preamble=body_preamble,
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
    body_preamble: str = "",
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
    frame: Any = None,
    exact_bbox: Optional[bool] = None,
    output_stem: Optional[str] = None,
    tmp_dir: Optional[Any] = None,
    output_dir: Optional[Any] = None,
    render_opts: Optional[Mapping[str, Any]] = None,
) -> str:
    """Render the back-substitution document to SVG using jupyter_tikz.

    ``tmp_dir`` is retained as a compatibility alias for ``output_dir``.
    Prefer ``output_dir`` for new code.
    """

    tex = backsubst_tex(
        body_preamble=body_preamble,
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
    opts = _resolve_render_svg_kwargs(
        render_opts,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
        tmp_dir=tmp_dir,
        output_stem=output_stem,
        exact_bbox=exact_bbox,
    )
    return render_svg(tex, **opts)
