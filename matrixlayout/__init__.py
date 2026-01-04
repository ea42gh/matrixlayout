"""
matrixlayout: layout-only TeX generators for matrix-themed figures.

Rendering is strictly delegated to jupyter_tikz via :func:`matrixlayout.render.render_svg`.
"""

from .jinja_env import get_environment
from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import eigproblem_tex, eigproblem_svg
from .ge import ge_tex, ge_svg, ge_grid_tex, ge_grid_svg

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
]
