r"""
GE (Gaussian Elimination) template helpers.

This module generates TeX for the GE "matrix-of-matrices" layout. In this layout,
outer delimiters (and block delimiters) are drawn with `nicematrix`'s `\SubMatrix`
inside `\CodeAfter`.

Target: current `nicematrix`
----------------------------
The `\SubMatrix` command syntax (as of current nicematrix releases) uses a single
mandatory argument of the form `({i-j}{k-l})` followed by an *optional* key-value
list *after* the argument: `\SubMatrix({1-1}{3-3})[name=...]`.

Therefore, this module normalizes submatrix locations into `(options, span)` where
`span` is a string like `"{1-1}{2-2}"`, and the template emits:
    `\SubMatrix({span})[options]`
"""

from __future__ import annotations

import os
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .formatting import latexify
from . import ge_decorations as _ge_decorations
from . import ge_labels as _ge_labels
from .ge_decorations import parse_ge_decorations as _parse_ge_decorations_impl
from .ge_decorator_map import build_ge_decorator_map
from .ge_spec_merge import (
    coerce_grid_spec as _coerce_grid_spec,
    coerce_layout_spec as _coerce_layout_spec,
    merge_grid_spec_inputs as _merge_grid_spec_inputs,
)
from .ge_grid import (
    as_2d_list as _as_2d_list,
    normalize_grid_input as _normalize_grid_input,
)
from .ge_grid_specs import (
    grid_highlight_specs,
    grid_line_specs,
    grid_submatrix_spans,
)
from .ge_layout_merge import (
    merge_layout_fields as _merge_layout_fields,
    merge_layout_string_hooks as _merge_layout_string_hooks,
    resolve_annotations as _resolve_annotations,
)
from .ge_render_grid import build_ge_grid_render_parts
from .ge_template import (
    append_nicematrix_option as _append_nicematrix_option,
    coerce_pivot_locs as _coerce_pivot_locs,
    coerce_rowechelon_paths as _coerce_rowechelon_paths,
    coerce_submatrix_locs as _coerce_submatrix_locs,
    coerce_text_annotations as _coerce_text_annotations,
    guess_shape_from_mat_rep as _guess_shape_from_mat_rep,
    merge_callouts as _merge_callouts,
    normalize_mat_format as _normalize_mat_format,
    normalize_mat_rep as _normalize_mat_rep,
    normalize_pivot_locs as _normalize_pivot_locs,
    normalize_submatrix_locs as _normalize_submatrix_locs,
    normalize_text_annotations as _normalize_text_annotations,
    validate_body_preamble as _validate_body_preamble,
)
from .ge_text_specs import render_ge_tex_specs as render_ge_tex_specs
from .jinja_env import render_template
from .render import _resolve_render_svg_kwargs, render_svg as _render_svg
from .specs import (
    GEGridBundle,
    GEGridSpec,
    GELayoutSpec,
)

LatexFormatter = Callable[[Any], str]

_blank_label_specs = _ge_labels.blank_label_specs
_build_label_maps = _ge_labels.build_label_maps
_compute_label_extras = _ge_labels.compute_label_extras
_embed_col_labels = _ge_labels.embed_col_labels
_embed_row_labels = _ge_labels.embed_row_labels
_normalize_index_list = _ge_decorations.normalize_index_list
_merge_label_specs = _ge_labels.merge_label_specs
_normalize_label_cols = _ge_labels.normalize_label_cols
_normalize_label_rows = _ge_labels.normalize_label_rows
grid_label_layouts = _ge_labels.grid_label_layouts


def _figure_scale_wrappers(fig_scale: Optional[Union[float, int, str]]) -> Tuple[str, str]:
    if fig_scale is None:
        return "", ""
    if isinstance(fig_scale, (int, float)) and float(fig_scale) != 1.0:
        return rf"\scalebox{{{fig_scale}}}{{%", "}"
    if isinstance(fig_scale, str) and fig_scale.strip():
        return fig_scale, ""
    return "", ""


def _submatrix_spans_with_outer_delims(
    *,
    submatrix_locs: Optional[Sequence[Any]],
    outer_delims: bool,
    outer_delims_name: str,
    outer_delims_span: Optional[Tuple[int, int]],
    mat_rep_norm: str,
) -> List[Tuple[Any, ...]]:
    sub_spans = _normalize_submatrix_locs(submatrix_locs)
    if outer_delims and not sub_spans:
        if outer_delims_span is None:
            outer_delims_span = _guess_shape_from_mat_rep(mat_rep_norm)
        nrows, ncols = outer_delims_span
        if nrows <= 0 or ncols <= 0:
            raise ValueError("Could not infer outer_delims_span; pass outer_delims_span=(nrows,ncols).")
        sub_spans.append((f"name={outer_delims_name}", f"{{1-1}}{{{nrows}-{ncols}}}"))
    return sub_spans


def _extract_submatrix_names(spans: Sequence[Tuple[Any, ...]]) -> List[str]:
    names: List[str] = []
    for item in spans:
        if not item:
            continue
        opts = item[0]
        if not opts:
            continue
        m = re.search(r"(?:^|,)\s*name\s*=\s*([A-Za-z0-9_]+)", str(opts))
        if m:
            names.append(m.group(1))
    return names


def _render_matrix_callouts(
    *,
    callouts: Optional[Sequence[Any]],
    matrix_labels: Optional[Sequence[Any]],
    sub_spans: Sequence[Tuple[Any, ...]],
    callout_name_map: Optional[Mapping[Tuple[int, int], str]],
) -> List[str]:
    if matrix_labels is not None:
        callouts = _merge_callouts(callouts, matrix_labels)
    if not callouts:
        return []
    try:
        from .nicematrix_decor import render_delim_callouts

        return render_delim_callouts(
            callouts,
            available_names=_extract_submatrix_names(sub_spans),
            name_map=callout_name_map,
            strict=True,
        )
    except Exception as e:
        raise ValueError(f"Failed to render callouts: {e}") from e


def tex(
    *,
    mat_rep: str,
    mat_format: str,
    document_preamble: str = "",
    body_preamble: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    text_annotations: Optional[Sequence[Any]] = None,
    rowechelon_paths: Optional[Sequence[Any]] = None,
    callouts: Optional[Sequence[Any]] = None,
    matrix_labels: Optional[Sequence[Any]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = None,
    create_extra_nodes: Optional[bool] = None,
    create_medium_nodes: Optional[bool] = None,
    outer_delims: Optional[bool] = None,
    outer_delims_name: Optional[str] = None,
    outer_delims_span: Optional[Tuple[int, int]] = None,
    callout_name_map: Optional[Mapping[Tuple[int, int], str]] = None,
) -> str:
    r"""Populate the GE template and return TeX."""
    mat_format_norm = _normalize_mat_format(mat_format)
    mat_rep_norm = _normalize_mat_rep(mat_rep)

    spec = _coerce_layout_spec(layout)
    document_preamble, body_preamble = _merge_layout_string_hooks(
        spec=spec,
        document_preamble=document_preamble,
        body_preamble=body_preamble,
    )
    _validate_body_preamble(body_preamble or "")

    (
        nice_options,
        landscape,
        create_cell_nodes,
        create_extra_nodes,
        create_medium_nodes,
        outer_delims,
        outer_delims_name,
        outer_delims_span,
        codebefore,
        submatrix_locs,
        submatrix_names,
        pivot_locs,
        text_annotations,
        rowechelon_paths,
        callouts,
    ) = _merge_layout_fields(
        spec=spec,
        nice_options=nice_options,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        create_extra_nodes=create_extra_nodes,
        create_medium_nodes=create_medium_nodes,
        outer_delims=outer_delims,
        outer_delims_name=outer_delims_name,
        outer_delims_span=outer_delims_span,
        codebefore=codebefore,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        text_annotations=text_annotations,
        rowechelon_paths=rowechelon_paths,
        callouts=callouts,
        matrix_labels=matrix_labels,
    )
    submatrix_locs = _coerce_submatrix_locs(submatrix_locs)
    pivot_locs = _coerce_pivot_locs(pivot_locs)
    text_annotations = _coerce_text_annotations(text_annotations)
    rowechelon_paths = _coerce_rowechelon_paths(rowechelon_paths)

    # Callouts (including matrix labels) require extra nodes for delimiter anchors.
    if callouts and create_extra_nodes is None:
        create_extra_nodes = True

    # Apply historical defaults after layout merging.
    if nice_options is None:
        nice_options = "vlines-in-sub-matrix = I"
    if landscape is None:
        landscape = False
    if create_cell_nodes is None:
        create_cell_nodes = True
    if create_extra_nodes is None:
        create_extra_nodes = False
    if create_medium_nodes is None:
        create_medium_nodes = False
    if not create_medium_nodes and codebefore:
        # Legacy codebefore snippets can reference -medium nodes; enable them automatically.
        if any("medium" in str(item) for item in codebefore):
            create_medium_nodes = True
    if outer_delims is None:
        outer_delims = False
    if outer_delims_name is None:
        outer_delims_name = "A0x0"

    if create_extra_nodes:
        nice_options = _append_nicematrix_option(nice_options, "create-extra-nodes")
    if create_medium_nodes:
        nice_options = _append_nicematrix_option(nice_options, "create-medium-nodes")

    fig_scale_open, fig_scale_close = _figure_scale_wrappers(fig_scale)
    sub_spans = _submatrix_spans_with_outer_delims(
        submatrix_locs=submatrix_locs,
        outer_delims=bool(outer_delims),
        outer_delims_name=str(outer_delims_name),
        outer_delims_span=outer_delims_span,
        mat_rep_norm=mat_rep_norm,
    )
    rendered_callouts = _render_matrix_callouts(
        callouts=callouts,
        matrix_labels=None,
        sub_spans=sub_spans,
        callout_name_map=callout_name_map,
    )

    ctx = {
        "document_preamble": document_preamble or "",
        "body_preamble": body_preamble or "",
        "fig_scale_open": fig_scale_open,
        "fig_scale_close": fig_scale_close,
        "landscape": bool(landscape),
        "nice_options": (nice_options or "").strip(),
        "mat_format": mat_format_norm,
        "create_cell_nodes": bool(create_cell_nodes),
        "create_extra_nodes": bool(create_extra_nodes),
        "create_medium_nodes": bool(create_medium_nodes),
        "codebefore": list(codebefore or []),
        "mat_rep": mat_rep_norm,
        "submatrix_spans": sub_spans,  # list[(opts, "{i-j}{k-l}")]
        "submatrix_names": list(submatrix_names or []),
        "pivot_locs": _normalize_pivot_locs(pivot_locs),
        "text_annotations": _normalize_text_annotations(text_annotations),
        "rowechelon_paths": list(rowechelon_paths or []) + rendered_callouts,
    }
    return render_template("ge.tex.j2", ctx)


def svg(
    *,
    mat_rep: str,
    mat_format: str,
    document_preamble: str = "",
    body_preamble: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    text_annotations: Optional[Sequence[Any]] = None,
    rowechelon_paths: Optional[Sequence[Any]] = None,
    callouts: Optional[Sequence[Any]] = None,
    matrix_labels: Optional[Sequence[Any]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = None,
    create_extra_nodes: Optional[bool] = None,
    create_medium_nodes: Optional[bool] = None,
    outer_delims: Optional[bool] = None,
    outer_delims_name: Optional[str] = None,
    outer_delims_span: Optional[Tuple[int, int]] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = "tight",
    padding: Any = None,
    frame: Any = None,
    exact_bbox: Optional[bool] = None,
    output_dir: Optional[Union[str, "os.PathLike[str]"]] = None,
    output_stem: str = "output",
    render_opts: Optional[Mapping[str, Any]] = None,
) -> str:
    """Render the GE template to SVG (strict rendering boundary)."""
    tex_doc = tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        document_preamble=document_preamble,
        body_preamble=body_preamble,
        nice_options=nice_options,
        layout=layout,
        codebefore=codebefore,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        text_annotations=text_annotations,
        rowechelon_paths=rowechelon_paths,
        callouts=callouts,
        matrix_labels=matrix_labels,
        fig_scale=fig_scale,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        create_extra_nodes=create_extra_nodes,
        create_medium_nodes=create_medium_nodes,
        outer_delims=outer_delims,
        outer_delims_name=outer_delims_name,
        outer_delims_span=outer_delims_span,
    )
    opts = _resolve_render_svg_kwargs(
        render_opts,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
        output_stem=output_stem,
        exact_bbox=exact_bbox,
    )
    return _render_svg(tex_doc, **opts)


def render_ge_tex(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    n_rhs: Any = None,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    block_vspace_mm: int = 1,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    document_preamble: Optional[str] = None,
    body_preamble: Optional[str] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    format_nrhs: Optional[bool] = None,
    decorators: Optional[Sequence[Any]] = None,
    decorations: Optional[Sequence[Any]] = None,
    strict: Optional[bool] = None,
    *,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    annotations: Optional[Sequence[Mapping[str, Any]]] = None,
    label_rows: Optional[Sequence[Any]] = None,
    label_cols: Optional[Sequence[Any]] = None,
    label_gap_mm: Optional[float] = 0.8,
    variable_labels: Optional[Sequence[Any]] = None,
    **kwargs: Any,
) -> str:
    r"""Populate the GE template from a matrix stack.

    IMPORTANT
    ---------
    ``nicematrix`` environments cannot be nested. Therefore this helper must
    *not* place ``pNiceArray`` environments inside an outer ``NiceArray``.
    Instead, this routine *flattens* a "grid of matrices" into a single
    scalar ``NiceArray`` and then uses ``\SubMatrix`` to draw per-block
    delimiters (parentheses) around each matrix block.

    Parameters
    ----------
    matrices:
        A nested list representing the "matrix-of-matrices" layout, typically
        ``[[None, A0], [E1, A1], [E2, A2], ...]``.
    n_rhs:
        Number of RHS columns in the *A-block* matrices, or a list of RHS block
        widths (partition style). This is used to insert an
        augmented-matrix partition bar in the last block-column's preamble.
    format_nrhs:
        Emit RHS separators via the column format when True.
    formatter:
        Scalar formatter for TeX.
    outer_hspace_mm:
        Horizontal spacing between adjacent matrix blocks.
    decorations:
        One-line dicts for backgrounds, separators, outlines, and entry styles.
    annotations:
        Optional label annotation specs. Label entries are merged into
        ``label_rows``/``label_cols``. Use ``callouts`` for arrow labels.

    Returns
    -------
    str
        TeX document (via :func:`tex`).

    Examples
    --------
    Decorate entries in the A-block using a boxed decorator::

        def box(tex): return rf"\\boxed{{{tex}}}"
        decorators = [{"grid": (0, 1), "entries": [(0, 0)], "decorator": box}]
        tex = render_ge_tex(matrices=matrices, decorators=decorators)
    """
    grid_spec = _coerce_grid_spec(spec)
    if body_preamble is not None:
        kwargs["body_preamble"] = body_preamble
    if grid_spec is not None:
        (
            matrices,
            n_rhs,
            formatter,
            outer_hspace_mm,
            block_vspace_mm,
            cell_align,
            block_align,
            block_valign,
            document_preamble,
            fig_scale,
            format_nrhs,
            decorators,
            decorations,
            strict,
            label_rows,
            label_cols,
            label_gap_mm,
            variable_labels,
            kwargs,
        ) = _merge_grid_spec_inputs(
            grid_spec=grid_spec,
            matrices=matrices,
            n_rhs=n_rhs,
            formatter=formatter,
            outer_hspace_mm=outer_hspace_mm,
            block_vspace_mm=block_vspace_mm,
            cell_align=cell_align,
            block_align=block_align,
            block_valign=block_valign,
            document_preamble=document_preamble,
            fig_scale=fig_scale,
            format_nrhs=format_nrhs,
            decorators=decorators,
            decorations=decorations,
            strict=strict,
            label_rows=label_rows,
            label_cols=label_cols,
            label_gap_mm=label_gap_mm,
            variable_labels=variable_labels,
            kwargs=kwargs,
        )

    annotations = _resolve_annotations(annotations=annotations)

    if annotations:
        label_rows, label_cols, decorations = _merge_label_specs(
            annotations=annotations,
            label_rows=label_rows,
            label_cols=label_cols,
            decorations=decorations,
        )

    if n_rhs is None:
        n_rhs = 0
    if format_nrhs is None:
        format_nrhs = True
    if strict is None:
        strict = False

    grid: List[List[Any]] = _normalize_grid_input(matrices)
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    # Normalize ragged outer rows.
    for r in range(n_block_rows):
        if len(grid[r]) < n_block_cols:
            grid[r].extend([None] * (n_block_cols - len(grid[r])))

    # Determine per-block-row height and per-block-column width.
    block_heights: List[int] = [0] * n_block_rows
    block_widths: List[int] = [0] * n_block_cols
    cell_cache: List[List[Tuple[List[List[Any]], int, int]]] = [
        [([], 0, 0) for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]

    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows, h, w = _as_2d_list(grid[br][bc])
            cell_cache[br][bc] = (rows, h, w)
            block_heights[br] = max(block_heights[br], h)
            block_widths[bc] = max(block_widths[bc], w)

    # Heuristic: if a whole block-column is "missing" (e.g. the E-block is None
    # in the first layer), infer a square size from the tallest block-row.
    max_h = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_h > 0:
            block_widths[bc] = max_h

    if any(w <= 0 for w in block_widths) or any(h <= 0 for h in block_heights):
        raise ValueError("Could not infer matrix block sizes from `matrices`.")

    if decorations:
        extra_decorators, extra_sub_locs, extra_callouts, extra_codebefore = _parse_ge_decorations(
            grid,
            decorations,
            block_align=block_align,
            block_valign=block_valign,
        )
        if extra_decorators:
            decorators = list(decorators or []) + extra_decorators
        if extra_sub_locs:
            kwargs["submatrix_locs"] = list(kwargs.get("submatrix_locs", []) or []) + extra_sub_locs
        if extra_callouts:
            kwargs["callouts"] = list(kwargs.get("callouts", []) or []) + extra_callouts
        if extra_codebefore:
            kwargs["codebefore"] = list(kwargs.get("codebefore", []) or []) + extra_codebefore
            if "create_medium_nodes" not in kwargs:
                kwargs["create_medium_nodes"] = True

    legacy_format = bool(kwargs.pop("legacy_format", False))
    if document_preamble is None:
        document_preamble = ""
    if legacy_format:
        if "\\newcolumntype{I}" not in document_preamble:
            document_preamble = document_preamble + "\n\\newcolumntype{I}{|}\n"

    decorator_map = build_ge_decorator_map(
        decorators=decorators,
        cell_cache=cell_cache,
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        formatter=formatter,
        strict=bool(strict),
    )

    # Ensure node coordinates exist when text nodes are requested.
    if "text_annotations" in kwargs and kwargs.get("create_cell_nodes") is None:
        kwargs["create_cell_nodes"] = True

    user_sub = kwargs.pop("submatrix_locs", None)
    use_legacy_names = bool(kwargs.pop("legacy_submatrix_names", False))
    parts = build_ge_grid_render_parts(
        grid=grid,
        cell_cache=cell_cache,
        block_heights=block_heights,
        block_widths=block_widths,
        n_rhs=n_rhs,
        formatter=formatter,
        outer_hspace_mm=outer_hspace_mm,
        block_vspace_mm=block_vspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        format_nrhs=bool(format_nrhs),
        label_rows=label_rows,
        label_cols=label_cols,
        label_gap_mm=label_gap_mm,
        variable_labels=variable_labels,
        decorator_map=decorator_map,
        strict=bool(strict),
        legacy_format=legacy_format,
        legacy_submatrix_names=use_legacy_names,
        user_submatrix_locs=user_sub,
    )

    return tex(
        mat_rep=parts.mat_rep,
        mat_format=parts.mat_format,
        document_preamble=document_preamble,
        fig_scale=fig_scale,
        submatrix_locs=parts.submatrix_locs,
        callouts=kwargs.pop("callouts", None),
        matrix_labels=kwargs.pop("matrix_labels", None),
        callout_name_map=parts.name_map,
        **kwargs,
    )


def _parse_ge_decorations(
    matrices: Sequence[Sequence[Any]],
    decorations: Sequence[Any],
    *,
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]], List[Dict[str, Any]], List[str]]:
    return _parse_ge_decorations_impl(
        matrices,
        decorations,
        as_2d_list=_as_2d_list,
        grid_line_specs=grid_line_specs,
        grid_highlight_specs=grid_highlight_specs,
        grid_submatrix_spans=grid_submatrix_spans,
        block_align=block_align,
        block_valign=block_valign,
    )


def decorations_help() -> str:
    """Return a concise help string for the `decorations` dict schema."""
    return (
        "DECORATIONS SPEC (dict entries)\n"
        "\n"
        "Required\n"
        "- grid: (row, col) of the block. Optional if the grid has a single block.\n"
        "\n"
        "Selectors (shared)\n"
        "- entries: list of (r,c) tuples (overrides rows/cols/submatrix).\n"
        "- rows: (r0,r1) inclusive, 'r0:r1' inclusive, slice(r0,r1+1), [r...], or None.\n"
        "- cols: same forms as rows.\n"
        "- submatrix: (rows, cols) shorthand.\n"
        "\n"
        "Background\n"
        "- background: color string (e.g., 'yellow!25').\n"
        "- padding_pt: float (inner sep in pt).\n"
        "\n"
        "Outline\n"
        "- outline: True (draw rectangle around selected submatrix).\n"
        "- color: stroke color.\n"
        "- line_width_pt: float.\n"
        "- padding_pt: float (expands the box).\n"
        "\n"
        "Lines\n"
        "- hlines / vlines: int | [int,...] | True | 'submatrix' | 'bounds' | 'all'.\n"
        "  * True/'submatrix': line after the last selected row/col.\n"
        "  * 'bounds': internal boundaries around the selection.\n"
        "  * 'all': every interior line in the selection.\n"
        "\n"
        "Entry styles\n"
        "- box: True or color string (box border color).\n"
        "- color: text color.\n"
        "- bold: True.\n"
        "\n"
        "Callout labels\n"
        "- label: LaTeX label string.\n"
        "- side: 'left'|'right' (default auto).\n"
        "- angle_deg: float degrees.\n"
        "- length_mm: float mm.\n"
        "- anchor: 'top'|'bottom'|'center'.\n"
        "- color: label/arrow color.\n"
    )


def resolve_ge_grid_name(
    name: Any,
    *,
    matrices: Sequence[Sequence[Any]],
    legacy_submatrix_names: bool = False,
) -> Optional[Tuple[int, int]]:
    """Resolve a GE submatrix name to a (block_row, block_col) tuple."""
    if not isinstance(name, str):
        return None
    spans = grid_submatrix_spans(matrices, legacy_submatrix_names=legacy_submatrix_names)
    name_map: Dict[str, Tuple[int, int]] = {}
    for span in spans:
        name_map[span.name] = (span.block_row, span.block_col)
        name_map.setdefault(f"A{span.block_row}x{span.block_col}", (span.block_row, span.block_col))
        if span.block_col == 0:
            name_map.setdefault(f"E{span.block_row}", (span.block_row, span.block_col))
        if span.block_col == 1 and any(s.block_col == 0 for s in spans):
            name_map.setdefault(f"A{span.block_row}", (span.block_row, span.block_col))
    return name_map.get(name)


def grid_bundle(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    *,
    n_rhs: int = 0,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    document_preamble: Optional[str] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    decorations: Optional[Sequence[Any]] = None,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    **kwargs: Any,
) -> GEGridBundle:
    """Return both the GE-grid TeX and the resolved ``\\SubMatrix`` spans.

    This is a notebook-oriented convenience wrapper around :func:`render_ge_tex`
    and :func:`grid_submatrix_spans`.

    Unlike :func:`render_ge_tex`, this function returns structured metadata so
    callers can attach TikZ paths/callouts to known delimiter nodes without
    regex-parsing the generated TeX.
    """

    if matrices is None and spec is None:
        raise ValueError("grid_bundle requires `matrices`")

    tex = render_ge_tex(
        matrices=matrices,
        n_rhs=n_rhs,
        formatter=formatter,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        document_preamble=document_preamble,
        fig_scale=fig_scale,
        layout=layout,
        decorations=decorations,
        spec=spec,
        **kwargs,
    )
    use_spec = _coerce_grid_spec(spec)
    if use_spec is not None:
        matrices = use_spec.matrices
        n_rhs = use_spec.n_rhs
        outer_hspace_mm = int(use_spec.outer_hspace_mm)
        cell_align = str(use_spec.cell_align)
        block_align = use_spec.block_align if use_spec.block_align is not None else block_align
        block_valign = use_spec.block_valign if use_spec.block_valign is not None else block_valign
        legacy_submatrix_names = bool(use_spec.legacy_submatrix_names)
        label_rows = use_spec.label_rows
        label_cols = use_spec.label_cols
        variable_labels = use_spec.variable_labels
    else:
        legacy_submatrix_names = bool(kwargs.get("legacy_submatrix_names", False))
        label_rows = None
        label_cols = None
        variable_labels = None
    if matrices is None:
        raise ValueError("grid_bundle requires `matrices`")
    spans = grid_submatrix_spans(
        matrices,
        n_rhs=n_rhs,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        label_rows=label_rows,
        label_cols=label_cols,
        variable_labels=variable_labels,
        legacy_submatrix_names=legacy_submatrix_names,
    )
    return GEGridBundle(tex=tex, submatrix_spans=spans)


def render_ge_svg(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    n_rhs: Any = None,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    block_vspace_mm: int = 1,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    document_preamble: Optional[str] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    format_nrhs: Optional[bool] = None,
    body_preamble: Optional[str] = None,
    nice_options: Optional[str] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = "tight",
    padding: Any = None,
    exact_bbox: Optional[bool] = None,
    decorators: Optional[Sequence[Any]] = None,
    decorations: Optional[Sequence[Any]] = None,
    strict: Optional[bool] = None,
    output_dir: Optional[Union[str, "os.PathLike[str]"]] = None,
    output_stem: str = "output",
    frame: Any = None,
    render_opts: Optional[Mapping[str, Any]] = None,
    *,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    annotations: Optional[Sequence[Mapping[str, Any]]] = None,
    label_rows: Optional[Sequence[Any]] = None,
    label_cols: Optional[Sequence[Any]] = None,
    label_gap_mm: Optional[float] = None,
    variable_labels: Optional[Sequence[Any]] = None,
    **kwargs: Any,
) -> str:
    r"""Render the GE matrix stack to SVG.

    This is a convenience wrapper around :func:`render_ge_tex` and the strict
    rendering boundary (:func:`matrixlayout.render.render_svg`).

    Parameters
    ----------
    matrices, n_rhs, formatter, outer_hspace_mm, block_vspace_mm, cell_align:
        See :func:`render_ge_tex`.
    toolchain_name, crop, padding:
        Passed through to the renderer.
    annotations:
        Additional label/callout mapping specs.

    Returns
    -------
    str
        SVG text.
    """
    if "label_targets" in kwargs:
        raise ValueError("label_targets is removed; use annotations instead.")

    annotations = _resolve_annotations(annotations=annotations)

    tex = render_ge_tex(
        matrices=matrices,
        n_rhs=n_rhs,
        formatter=formatter,
        outer_hspace_mm=outer_hspace_mm,
        block_vspace_mm=block_vspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        document_preamble=document_preamble,
        fig_scale=fig_scale,
        format_nrhs=format_nrhs,
        body_preamble=body_preamble,
        nice_options=nice_options,
        decorators=decorators,
        decorations=decorations,
        strict=strict,
        spec=spec,
        annotations=annotations,
        label_rows=label_rows,
        label_cols=label_cols,
        label_gap_mm=label_gap_mm,
        variable_labels=variable_labels,
        **kwargs,
    )
    opts = _resolve_render_svg_kwargs(
        render_opts,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
        output_stem=output_stem,
        exact_bbox=exact_bbox,
    )
    return _render_svg(tex, **opts)
