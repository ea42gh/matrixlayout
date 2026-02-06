"""
matrixlayout: layout-only TeX generators for matrix-themed figures.

Rendering is strictly delegated to jupyter_tikz via :func:`matrixlayout.render.render_svg`.

Public API
----------
Functions exported via ``__all__`` are the supported public entry points.
Helpers prefixed with ``_`` are internal and subject to change.
"""

from .jinja_env import get_environment
from .backsubst import backsubst_tex, backsubst_svg
from .eigproblem import render_eig_tex, render_eig_svg
from .ge import (
    tex,
    svg,
    render_ge_tex,
    render_ge_svg,
    resolve_ge_grid_name,
    grid_line_specs,
    grid_highlight_specs,
    render_ge_tex_specs,
    grid_label_layouts,
    decorations_help,
)
from .qr import render_qr_tex, render_qr_svg, resolve_qr_grid_name, qr_grid_bundle
from .specs import GEGridSpec, QRGridSpec, QRGridBundle
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
    validate_callouts,
)

def show_svg(svg: object):
    """Notebook-friendly display helper for SVG strings."""
    try:
        from IPython.display import SVG, display
    except Exception as exc:  # pragma: no cover - only used in notebooks
        raise ImportError("show_svg requires IPython (for SVG display).") from exc
    display(SVG(svg))
    return svg

__all__ = [
    "get_environment",
    "backsubst_tex",
    "backsubst_svg",
    "render_eig_tex",
    "render_eig_svg",
    "tex",
    "svg",
    "render_ge_tex",
    "render_ge_svg",
    "grid_line_specs",
    "grid_highlight_specs",
    "render_ge_tex_specs",
    "grid_label_layouts",
    "decorations_help",
    "resolve_ge_grid_name",
    "render_qr_tex",
    "render_qr_svg",
    "qr_grid_bundle",
    "resolve_qr_grid_name",
    "GEGridSpec",
    "QRGridSpec",
    "QRGridBundle",
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
    "validate_callouts",
    "show_svg",
]
