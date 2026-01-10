"""
matrixlayout: layout-only TeX generators for matrix-themed figures.

Rendering is strictly delegated to jupyter_tikz via :func:`matrixlayout.render.render_svg`.
"""

from .jinja_env import get_environment
from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import eigproblem_tex, eigproblem_svg
from .ge import (
    ge_tex,
    ge_svg,
    ge_grid_tex,
    ge_grid_svg,
    resolve_ge_grid_name,
    ge_grid_line_specs,
    ge_grid_highlight_specs,
    ge_grid_text_specs,
    ge_grid_label_layouts,
    ge_decorations_help,
)
from .qr import qr_grid_tex, qr_grid_svg, resolve_qr_grid_name
from .specs import GEGridSpec, QRGridSpec
from .formatting import (
    decorate_tex_entries,
    latexify,
    make_decorator,
    decorator_box,
    decorator_color,
    decorator_bg,
    decorator_bf,
    sel_entry,
    sel_box,
    sel_row,
    sel_col,
    sel_rows,
    sel_cols,
    sel_all,
    sel_vec,
    sel_vec_range,
)
from .nicematrix_decor import (
    DelimCallout,
    DelimCalloutDict,
    infer_ge_matrix_labels,
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
    "ge_grid_line_specs",
    "ge_grid_highlight_specs",
    "ge_grid_text_specs",
    "ge_grid_label_layouts",
    "ge_decorations_help",
    "resolve_ge_grid_name",
    "qr_grid_tex",
    "qr_grid_svg",
    "resolve_qr_grid_name",
    "GEGridSpec",
    "QRGridSpec",
    "latexify",
    "make_decorator",
    "decorate_tex_entries",
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
    "DelimCallout",
    "DelimCalloutDict",
    "infer_ge_matrix_labels",
    "infer_ge_layer_callouts",
    "render_delim_callout",
    "render_delim_callouts",
]
