"""
matrixlayout: layout-only TeX generators for matrix-themed figures.

Rendering is strictly delegated to jupyter_tikz via :func:`matrixlayout.render.render_svg`.
"""

from .jinja_env import get_environment
from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import eigproblem_tex, eigproblem_svg
from .ge import ge_tex, ge_svg, ge_grid_tex, ge_grid_svg
from .nicematrix_decor import (
    DelimCallout,
    DelimCalloutDict,
    infer_ge_layer_callouts,
    render_delim_callout,
    render_delim_callouts,
)

__all__ = [
    "get_environment",
    "backsubst_tex",
    "backsubst_svg",
    "eigproblem_tex",
    "eigproblem_svg",
    "ge_tex",
    "ge_svg",
    "ge_grid_tex",
    "ge_grid_svg",
    "DelimCallout",
    "DelimCalloutDict",
    "infer_ge_layer_callouts",
    "render_delim_callout",
    "render_delim_callouts",
]
