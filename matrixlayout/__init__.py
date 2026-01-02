"""
matrixlayout: layout-only TeX generators for matrix-themed figures.

Rendering is strictly delegated to jupyter_tikz via :func:`matrixlayout.render.render_svg`.
"""

from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import eigproblem_tex, eigproblem_svg
from .ge import ge_tex, ge_svg

__all__ = [
    "backsubst_tex",
    "backsubst_svg",
    "eigproblem_tex",
    "eigproblem_svg",
    "ge_tex",
    "ge_svg",
]
