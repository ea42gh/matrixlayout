"""matrixlayout: matrix-based layout and presentation library.

matrixlayout is a *layout-only* library. It generates TeX (typically TikZ /
nicematrix-based) from explicit description objects, and may optionally render
SVG through the strict rendering boundary provided by :func:`jupyter_tikz.render_svg`.
"""

from .jinja_env import (
    JinjaConfig,
    get_environment,
    make_environment,
    render_template,
    render_string,
)
from .render import render_svg

from .shortcascade import BackSubStep, BackSubTrace, mk_shortcascade_lines
from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import eigproblem_tex, eigproblem_svg
from .ge import ge_tex, ge_svg

__all__ = [
    "JinjaConfig",
    "get_environment",
    "make_environment",
    "render_template",
    "render_string",
    "render_svg",
    "BackSubStep",
    "BackSubTrace",
    "mk_shortcascade_lines",
    "backsubst_tex",
    "backsubst_svg",
    "eigproblem_tex",
    "eigproblem_svg",
    "ge_tex",
    "ge_svg",
]
