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

from .formatting import _normalize_unicode_tex, latexify
from . import ge_decorations as _ge_decorations
from . import ge_labels as _ge_labels
from .ge_decorations import parse_ge_decorations as _parse_ge_decorations_impl
from .ge_decorator_map import build_ge_decorator_map
from .ge_spec_merge import (
    coerce_grid_spec as _coerce_grid_spec,
    coerce_layout_spec as _coerce_layout_spec,
    merge_grid_spec_inputs as _merge_grid_spec_inputs,
    merge_scalar as _merge_scalar,
)
from .ge_grid import (
    as_2d_list as _as_2d_list,
    block_pad_left as _block_pad_left,
    block_pad_top as _block_pad_top,
    normalize_grid_input as _normalize_grid_input,
)
from .ge_render_grid import build_ge_grid_render_parts
from .ge_template import (
    coerce_pivot_locs as _coerce_pivot_locs,
    coerce_rowechelon_paths as _coerce_rowechelon_paths,
    coerce_submatrix_locs as _coerce_submatrix_locs,
    coerce_txt_with_locs as _coerce_txt_with_locs,
    guess_shape_from_mat_rep as _guess_shape_from_mat_rep,
    normalize_mat_format as _normalize_mat_format,
    normalize_mat_rep as _normalize_mat_rep,
    normalize_pivot_locs as _normalize_pivot_locs,
    normalize_submatrix_locs as _normalize_submatrix_locs,
    normalize_txt_with_locs as _normalize_txt_with_locs,
)
from .jinja_env import render_template
from .render import merge_render_opts, render_svg as _render_svg
from .specs import (
    GEGridBundle,
    GEGridSpec,
    GELayoutSpec,
    SubMatrixSpan,
)

LatexFormatter = Callable[[Any], str]

_blank_label_specs = _ge_labels.blank_label_specs
_build_label_maps = _ge_labels.build_label_maps
_compute_label_extras = _ge_labels.compute_label_extras
_embed_col_labels = _ge_labels.embed_col_labels
_embed_row_labels = _ge_labels.embed_row_labels
_escape_label_text_segment = _ge_labels.escape_label_text_segment
_normalize_index_list = _ge_decorations.normalize_index_list
_label_targets_from_specs = _ge_labels.label_targets_from_specs
_merge_label_specs = _ge_labels.merge_label_specs
_normalize_label_cols = _ge_labels.normalize_label_cols
_normalize_label_rows = _ge_labels.normalize_label_rows
_split_label_dollar_segments = _ge_labels.split_label_dollar_segments
grid_label_layouts = _ge_labels.grid_label_layouts


_BODY_PREAMBLE_FORBIDDEN = (
    r"\\documentclass",
    r"\\usepackage",
    r"\\RequirePackage",
    # Note: use regex whitespace (\s), not a literal backslash-s.
    r"\\geometry\s*\{",
)


def _validate_body_preamble(preamble: str) -> None:
    """Guardrail for the GE template's ``preamble`` hook.

    The GE template injects ``preamble`` into the document *body* (after
    ``\\begin{document}``). Users must not place LaTeX preamble directives here.
    Use ``extension=...`` for true preamble insertions.
    """
    if not preamble:
        return
    for pat in _BODY_PREAMBLE_FORBIDDEN:
        if re.search(pat, preamble):
            raise ValueError(
                "The `preamble` parameter is injected into the document body. "
                "Do not include LaTeX preamble directives (e.g. \\usepackage, \\geometry). "
                "Use `extension=` for preamble insertions."
            )


def _append_nicematrix_option(nice_options: Optional[str], opt: str) -> str:
    opts = (nice_options or "").strip()
    if not opts:
        return opt
    if opt in opts:
        return opts
    return f"{opts}, {opt}"


def _merge_list(explicit: Optional[Sequence[Any]], spec_val: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    """Merge list-like fields by concatenation (explicit first)."""
    if explicit is None and spec_val is None:
        return None
    out: List[Any] = []
    if explicit is not None:
        out.extend(list(explicit))
    if spec_val is not None:
        out.extend(list(spec_val))
    return out


def _merge_callouts(explicit: Optional[Any], spec_val: Optional[Any]) -> Optional[Any]:
    """Merge callouts, preserving boolean auto-callout flags."""
    if isinstance(explicit, bool) or isinstance(spec_val, bool):
        if explicit is None:
            return spec_val
        if spec_val is None:
            return explicit
        if explicit != spec_val:
            raise ValueError(f"Conflicting values for callouts: explicit={explicit!r} spec={spec_val!r}")
        return explicit
    return _merge_list(explicit, spec_val)



def tex(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    txt_with_locs: Optional[Sequence[Any]] = None,
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
    # Merge string hooks from layout spec *before* validation, so guardrails
    # apply consistently regardless of whether the user supplies values via
    # explicit kwargs or the layout object.
    if spec is not None:
        if getattr(spec, "extension", None):
            # Layout spec is treated as the "base" template configuration.
            # Explicit kwargs are appended so users can override definitions.
            extension = (spec.extension or "") + ("\n" if (spec.extension and extension) else "") + (extension or "")
        if getattr(spec, "preamble", None):
            preamble = (spec.preamble or "") + ("\n" if (spec.preamble and preamble) else "") + (preamble or "")

    _validate_body_preamble(preamble or "")

    # Merge remaining layout fields.
    if spec is not None:
        nice_options = _merge_scalar("nice_options", nice_options, spec.nice_options)
        landscape = _merge_scalar("landscape", landscape, spec.landscape)
        create_cell_nodes = _merge_scalar("create_cell_nodes", create_cell_nodes, spec.create_cell_nodes)
        create_extra_nodes = _merge_scalar("create_extra_nodes", create_extra_nodes, spec.create_extra_nodes)
        create_medium_nodes = _merge_scalar("create_medium_nodes", create_medium_nodes, spec.create_medium_nodes)
        outer_delims = _merge_scalar("outer_delims", outer_delims, spec.outer_delims)
        outer_delims_name = _merge_scalar("outer_delims_name", outer_delims_name, spec.outer_delims_name)
        outer_delims_span = _merge_scalar("outer_delims_span", outer_delims_span, spec.outer_delims_span)

        codebefore = _merge_list(codebefore, spec.codebefore)
        submatrix_locs = _merge_list(submatrix_locs, spec.submatrix_locs)
        submatrix_names = _merge_list(submatrix_names, spec.submatrix_names)
        pivot_locs = _merge_list(pivot_locs, spec.pivot_locs)
        txt_with_locs = _merge_list(txt_with_locs, spec.txt_with_locs)
        rowechelon_paths = _merge_list(rowechelon_paths, spec.rowechelon_paths)
        callouts = _merge_callouts(callouts, spec.callouts)
        callouts = _merge_callouts(callouts, spec.matrix_labels)

    submatrix_locs = _coerce_submatrix_locs(submatrix_locs)
    pivot_locs = _coerce_pivot_locs(pivot_locs)
    txt_with_locs = _coerce_txt_with_locs(txt_with_locs)
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

    # figure scale: the GE template currently supports TeX wrappers in the template itself
    fig_scale_open = fig_scale_close = ""
    if fig_scale is not None:
        if isinstance(fig_scale, (int, float)) and float(fig_scale) != 1.0:
            fig_scale_open = rf"\scalebox{{{fig_scale}}}{{%"
            fig_scale_close = "}"
        elif isinstance(fig_scale, str) and fig_scale.strip():
            fig_scale_open = fig_scale
            fig_scale_close = ""

    sub_spans = _normalize_submatrix_locs(submatrix_locs)

    if outer_delims and not sub_spans:
        if outer_delims_span is None:
            outer_delims_span = _guess_shape_from_mat_rep(mat_rep_norm)
        nrows, ncols = outer_delims_span
        if nrows <= 0 or ncols <= 0:
            raise ValueError("Could not infer outer_delims_span; pass outer_delims_span=(nrows,ncols).")
        sub_spans.append((f"name={outer_delims_name}", f"{{1-1}}{{{nrows}-{ncols}}}"))

    # Descriptor-based callouts (rendered to TikZ draw commands).
    # We validate against the set of SubMatrix names declared in sub_spans.
    rendered_callouts: List[str] = []
    if matrix_labels is not None:
        callouts = _merge_callouts(callouts, matrix_labels)
    if callouts:
        try:
            import re

            def _extract_names(spans: Sequence[Tuple[Any, ...]]) -> List[str]:
                """Extract declared SubMatrix names from normalized spans.

                ``_normalize_submatrix_locs`` can return tuples of length 2
                ``(opts, span)`` or length 4 ``(opts, span, left, right)``.
                We only care about the ``opts`` field.
                """
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

            from .nicematrix_decor import render_delim_callouts

            rendered_callouts = render_delim_callouts(
                callouts,
                available_names=_extract_names(sub_spans),
                name_map=callout_name_map,
                strict=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to render callouts: {e}") from e

    ctx = dict(
        extension=extension or "",
        preamble=preamble or "",
        fig_scale_open=fig_scale_open,
        fig_scale_close=fig_scale_close,
        landscape=bool(landscape),
        nice_options=(nice_options or "").strip(),
        mat_format=mat_format_norm,
        create_cell_nodes=bool(create_cell_nodes),
        create_extra_nodes=bool(create_extra_nodes),
        create_medium_nodes=bool(create_medium_nodes),
        codebefore=list(codebefore or []),
        mat_rep=mat_rep_norm,
        submatrix_spans=sub_spans,   # list[(opts, "{i-j}{k-l}")]
        submatrix_names=list(submatrix_names or []),
        pivot_locs=_normalize_pivot_locs(pivot_locs),
        txt_with_locs=_normalize_txt_with_locs(txt_with_locs),
        rowechelon_paths=list(rowechelon_paths or []) + rendered_callouts,
    )
    return render_template("ge.tex.j2", ctx)


def svg(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    txt_with_locs: Optional[Sequence[Any]] = None,
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
    crop: Optional[str] = None,
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
        preamble=preamble,
        extension=extension,
        nice_options=nice_options,
        layout=layout,
        codebefore=codebefore,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
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
    opts = merge_render_opts(
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
    Nrhs: Any = None,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    block_vspace_mm: int = 1,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    extension: str = "",
    fig_scale: Optional[Union[float, int, str]] = None,
    format_nrhs: Optional[bool] = None,
    decorators: Optional[Sequence[Any]] = None,
    decorations: Optional[Sequence[Any]] = None,
    strict: Optional[bool] = None,
    *,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    specs: Optional[Sequence[Mapping[str, Any]]] = None,
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
    Nrhs:
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
        One-line dicts for backgrounds, separators, callouts, and entry styles.
    specs:
        Optional decoration/label specs. Label entries are merged into
        ``label_rows``/``label_cols``; callout labels are merged into decorations.

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
    if grid_spec is not None:
        (
            matrices,
            Nrhs,
            formatter,
            outer_hspace_mm,
            block_vspace_mm,
            cell_align,
            block_align,
            block_valign,
            extension,
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
            Nrhs=Nrhs,
            formatter=formatter,
            outer_hspace_mm=outer_hspace_mm,
            block_vspace_mm=block_vspace_mm,
            cell_align=cell_align,
            block_align=block_align,
            block_valign=block_valign,
            extension=extension,
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

    if specs:
        label_rows, label_cols, decorations = _merge_label_specs(
            specs=specs,
            label_rows=label_rows,
            label_cols=label_cols,
            decorations=decorations,
        )

    if Nrhs is None:
        Nrhs = 0
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
    if legacy_format:
        if extension is None:
            extension = ""
        if "\\newcolumntype{I}" not in extension:
            extension = extension + "\n\\newcolumntype{I}{|}\n"

    use_legacy_names_for_decorators = bool(kwargs.get("legacy_submatrix_names", False))
    decorator_map = build_ge_decorator_map(
        decorators=decorators,
        matrices=grid,
        cell_cache=cell_cache,
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        formatter=formatter,
        strict=bool(strict),
        legacy_submatrix_names=use_legacy_names_for_decorators,
        resolve_grid_name=lambda name, matrices, legacy: resolve_ge_grid_name(
            name,
            matrices=matrices,
            legacy_submatrix_names=legacy,
        ),
    )

    # Ensure node coordinates exist when text nodes are requested.
    if "txt_with_locs" in kwargs and kwargs.get("create_cell_nodes") is None:
        kwargs["create_cell_nodes"] = True

    user_sub = kwargs.pop("submatrix_locs", None)
    use_legacy_names = bool(kwargs.pop("legacy_submatrix_names", False))
    parts = build_ge_grid_render_parts(
        grid=grid,
        cell_cache=cell_cache,
        block_heights=block_heights,
        block_widths=block_widths,
        Nrhs=Nrhs,
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
        extension=extension,
        fig_scale=fig_scale,
        submatrix_locs=parts.submatrix_locs,
        callouts=kwargs.pop("callouts", None),
        matrix_labels=kwargs.pop("matrix_labels", None),
        callout_name_map=parts.name_map,
        **kwargs,
    )


def grid_submatrix_spans(
    matrices: Sequence[Sequence[Any]],
    *,
    Nrhs: int = 0,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    label_rows: Optional[Sequence[Any]] = None,
    label_cols: Optional[Sequence[Any]] = None,
    variable_labels: Optional[Sequence[Any]] = None,
    legacy_submatrix_names: bool = False,
) -> List[SubMatrixSpan]:
    """Return the resolved ``\\SubMatrix`` spans for a GE matrix grid.

    This helper exposes the same naming and inferred-block-dimension logic used
    by :func:`render_ge_tex`, but returns structured metadata rather than a TeX
    document. It exists primarily to support notebook workflows that want to
    attach TikZ paths to delimiter nodes without regex-parsing the generated TeX.

    Notes
    -----
    * Coordinates are 1-based nicematrix coordinates.
    * Blocks that are ``None`` (or empty) are omitted.
    * The first block-column width is inferred as square when it is entirely
      missing (common for the top E-block in the 2-column layout).
    """

    # Keep this logic intentionally aligned with render_ge_tex.
    grid: List[List[Any]] = _normalize_grid_input(matrices)
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    for r in range(n_block_rows):
        if len(grid[r]) < n_block_cols:
            grid[r].extend([None] * (n_block_cols - len(grid[r])))

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

    max_h = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_h > 0:
            block_widths[bc] = max_h

    if any(w <= 0 for w in block_widths) or any(h <= 0 for h in block_heights):
        raise ValueError("Could not infer matrix block sizes from `matrices`.")

    label_rows_map, label_cols_map, _overlay = _build_label_maps(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        label_rows=label_rows,
        label_cols=label_cols,
        variable_labels=variable_labels,
        allow_overlay=False,
        strict=False,
    )

    extra_rows_above = [0] * n_block_rows
    extra_rows_below = [0] * n_block_rows
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows_above = label_rows_map.get((br, bc, "above"), [])
            rows_below = label_rows_map.get((br, bc, "below"), [])
            extra_rows_above[br] = max(extra_rows_above[br], len(rows_above))
            extra_rows_below[br] = max(extra_rows_below[br], len(rows_below))

    extra_cols_left = [0] * n_block_cols
    extra_cols_right = [0] * n_block_cols
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            cols_left = label_cols_map.get((br, bc, "left"), [])
            cols_right = label_cols_map.get((br, bc, "right"), [])
            extra_cols_left[bc] = max(extra_cols_left[bc], len(cols_left))
            extra_cols_right[bc] = max(extra_cols_right[bc], len(cols_right))

    total_block_heights = [
        extra_rows_above[br] + block_heights[br] + extra_rows_below[br] for br in range(n_block_rows)
    ]
    total_block_widths = [
        extra_cols_left[bc] + block_widths[bc] + extra_cols_right[bc] for bc in range(n_block_cols)
    ]

    # Build a single NiceArray format string so we keep the same inferred widths
    # as render_ge_tex (including Nrhs behavior). We don't return it here, but the
    # computation is intentionally mirrored.
    _ = (Nrhs, outer_hspace_mm, cell_align)  # for signature parity / future use

    block_pad_left: List[List[int]] = [
        [0 for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]
    block_pad_top: List[List[int]] = [
        [0 for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, h, w = cell_cache[br][bc]
            if h == 0 or w == 0:
                continue
            W = block_widths[bc]
            H = block_heights[br]
            block_pad_left[br][bc] = _block_pad_left(W, w, block_align)
            block_pad_top[br][bc] = _block_pad_top(H, h, block_valign)

    row_starts: List[int] = []
    acc = 1
    for H in total_block_heights:
        row_starts.append(acc)
        acc += H

    col_starts: List[int] = []
    acc = 1
    for W in total_block_widths:
        col_starts.append(acc)
        acc += W

    spans: List[SubMatrixSpan] = []
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, h, w = cell_cache[br][bc]
            if h == 0 or w == 0:
                continue

            r0 = row_starts[br] + extra_rows_above[br] + block_pad_top[br][bc]
            c0 = col_starts[bc] + extra_cols_left[bc] + block_pad_left[br][bc]
            r1 = r0 + h - 1
            c1 = c0 + w - 1

            if legacy_submatrix_names:
                name = f"A{br}x{bc}"
            else:
                if n_block_cols == 2:
                    base = ("E" if bc == 0 else "A")
                else:
                    base = f"M{bc}"
                name = f"{base}{br}"

            spans.append(
                SubMatrixSpan(
                    name=name,
                    row_start=r0,
                    col_start=c0,
                    row_end=r1,
                    col_end=c1,
                    block_row=br,
                    block_col=bc,
                )
            )

    return spans


def grid_line_specs(
    matrices: Sequence[Sequence[Any]],
    *,
    targets: Sequence[Tuple[int, int]],
    hlines: Optional[Union[int, Sequence[int]]] = None,
    vlines: Optional[Union[int, Sequence[int]]] = None,
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
) -> List[Tuple[str, str, str]]:
    """Return ``submatrix_locs`` entries that draw hlines/vlines in targets."""

    def _normalize_lines(val: Any, max_idx: int) -> List[int]:
        if val is None:
            return []
        if isinstance(val, (list, tuple, set)):
            items = [int(x) for x in val]
        else:
            items = [int(val)]
        out = [x for x in items if 1 <= x <= max_idx]
        return sorted(set(out))

    targets_set = {(int(r), int(c)) for r, c in targets}
    spans = grid_submatrix_spans(
        matrices,
        block_align=block_align,
        block_valign=block_valign,
    )
    out: List[Tuple[str, str, str]] = []
    for span in spans:
        key = (span.block_row, span.block_col)
        if key not in targets_set:
            continue
        rows, h, w = _as_2d_list(matrices[key[0]][key[1]])
        if h == 0 or w == 0:
            continue
        hspec = _normalize_lines(hlines, h - 1)
        vspec = _normalize_lines(vlines, w - 1)
        if not hspec and not vspec:
            continue
        opts: List[str] = ["delimiters/color=."]
        if hspec:
            if len(hspec) == 1:
                opts.append(f"hlines={hspec[0]}")
            else:
                opts.append("hlines={" + ",".join(str(x) for x in hspec) + "}")
        if vspec:
            if len(vspec) == 1:
                opts.append(f"vlines={vspec[0]}")
            else:
                opts.append("vlines={" + ",".join(str(x) for x in vspec) + "}")
        out.append((",".join(opts), span.start_token, span.end_token))
    return out


def _normalize_range(val: Any, max_len: int) -> Tuple[int, int]:
    if max_len <= 0:
        return (0, -1)
    if val is None:
        return (0, max_len - 1)
    if isinstance(val, slice):
        start = 0 if val.start is None else int(val.start)
        stop = max_len if val.stop is None else int(val.stop)
        return (max(0, start), min(max_len - 1, stop - 1))
    if isinstance(val, str):
        txt = val.strip()
        if ":" in txt:
            left, right = txt.split(":", 1)
            start = int(left) if left.strip() else 0
            end = int(right) if right.strip() else (max_len - 1)
            lo, hi = (start, end) if start <= end else (end, start)
            return (max(0, lo), min(max_len - 1, hi))
    if isinstance(val, (tuple, list)) and len(val) == 2 and all(isinstance(x, int) for x in val):
        a, b = int(val[0]), int(val[1])
        lo, hi = (a, b) if a <= b else (b, a)
        return (max(0, lo), min(max_len - 1, hi))
    if isinstance(val, (list, tuple, set)):
        items = [int(x) for x in val]
        if not items:
            return (0, -1)
        lo, hi = min(items), max(items)
        return (max(0, lo), min(max_len - 1, hi))
    raise ValueError("rows/cols must be None, a (start,end) pair, or a list of indices")


def grid_highlight_specs(
    matrices: Sequence[Sequence[Any]],
    *,
    blocks: Sequence[Any],
    color: str = "yellow!25",
    padding_pt: float = 1.0,
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
) -> List[str]:
    """Return ``codebefore`` entries that highlight rectangular sub-blocks."""

    def _coerce_block(obj: Any) -> Dict[str, Any]:
        if isinstance(obj, dict):
            return dict(obj)
        if isinstance(obj, (list, tuple)) and len(obj) >= 1:
            d: Dict[str, Any] = {"grid": obj[0]}
            if len(obj) > 1:
                d["rows"] = obj[1]
            if len(obj) > 2:
                d["cols"] = obj[2]
            if len(obj) > 3:
                d["color"] = obj[3]
            return d
        raise ValueError("block highlight must be a dict or a (grid, rows, cols) tuple")

    spans = grid_submatrix_spans(
        matrices,
        block_align=block_align,
        block_valign=block_valign,
    )
    span_map = {(s.block_row, s.block_col): s for s in spans}
    out: List[str] = []
    for spec in blocks:
        item = _coerce_block(spec)
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            raise ValueError("highlight spec requires grid=(row,col)")
        key = (int(grid[0]), int(grid[1]))
        if key not in span_map:
            continue
        mat = matrices[key[0]][key[1]]
        rows, h, w = _as_2d_list(mat)
        if h == 0 or w == 0:
            continue
        r0, r1 = _normalize_range(item.get("rows"), h)
        c0, c1 = _normalize_range(item.get("cols"), w)
        if r1 < r0 or c1 < c0:
            continue
        span = span_map[key]
        row_start = span.row_start + r0
        row_end = span.row_start + r1
        col_start = span.col_start + c0
        col_end = span.col_start + c1
        fill = str(item.get("color", color))
        pad = float(item.get("padding_pt", padding_pt))
        out.append(
            rf"\tikz \node [fill={fill}, inner sep={pad}pt, fit=({row_start}-{col_start}-medium) ({row_end}-{col_end}-medium)] {{}};"
        )
    return out



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
        "- angle: float degrees (alias: angle_deg).\n"
        "- length: float mm (alias: length_mm).\n"
        "- anchor: 'top'|'bottom'|'center'.\n"
        "- color: label/arrow color.\n"
    )


def render_ge_tex_specs(
    matrices: Sequence[Sequence[Any]],
    targets: Sequence[Mapping[str, Any]],
    *,
    Nrhs: int = 0,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    label_rows: Optional[Sequence[Any]] = None,
    label_cols: Optional[Sequence[Any]] = None,
    variable_labels: Optional[Sequence[Any]] = None,
    legacy_submatrix_names: bool = False,
) -> List[Tuple[str, str, str]]:
    """Return text placements around matrix blocks.

    Each target supports:
      - grid: (block_row, block_col)
      - side: right/left/above/below
      - labels: list of strings (rows for left/right; cols for above/below)
      - offset_mm: numeric offset (xshift for left/right; yshift for above/below)
      - style: extra TikZ node style (e.g. "text=blue,align=left")
    """

    spans = grid_submatrix_spans(
        matrices,
        Nrhs=Nrhs,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        label_rows=label_rows,
        label_cols=label_cols,
        variable_labels=variable_labels,
        legacy_submatrix_names=legacy_submatrix_names,
    )
    span_map = {(s.block_row, s.block_col): s for s in spans}
    out: List[Tuple[str, str, str]] = []
    label_rows_count: Dict[Tuple[int, int, str], int] = {}

    from collections.abc import Mapping as _Mapping

    def _count_label_blocks(val: Any) -> int:
        if val is None:
            return 0
        if isinstance(val, (list, tuple)):
            if not val:
                return 0
            if isinstance(val[0], (list, tuple)):
                return len(val)
            return 1
        return 1

    for spec_item in label_rows or []:
        if not isinstance(spec_item, _Mapping):
            continue
        grid = spec_item.get("grid")
        if grid is None and len(spans) == 1:
            grid = (0, 0)
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            continue
        gM, gN = int(grid[0]), int(grid[1])
        side = str(spec_item.get("side", "above")).strip().lower()
        if side not in ("above", "below"):
            continue
        count = _count_label_blocks(spec_item.get("rows", spec_item.get("labels")))
        if count:
            label_rows_count[(gM, gN, side)] = label_rows_count.get((gM, gN, side), 0) + count

    for item in targets:
        if not isinstance(item, _Mapping):
            continue
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            continue
        key = (int(grid[0]), int(grid[1]))
        span = span_map.get(key)
        if span is None:
            continue
        yshift_mm = float(item.get("yshift_mm", item.get("row_offset", 0)) or 0)
        xshift_mm = float(item.get("xshift_mm", item.get("col_offset", 0)) or 0)
        labels_raw = item.get("labels") or []
        labels = list(labels_raw) if isinstance(labels_raw, (list, tuple)) else [labels_raw]
        side = str(item.get("side", "right")).strip().lower()
        if side == "top":
            side = "above"
        elif side == "bottom":
            side = "below"
        offset_raw = item.get("offset_mm")
        if offset_raw is None and "label_gap_mm" in item:
            offset_raw = item.get("label_gap_mm")
        if offset_raw is None:
            offset_raw = 0.0
        offset = float(offset_raw) if offset_raw is not None else 0.0
        style = str(item.get("style", "")).strip()

        def _wrap_math(text: Any) -> str:
            if isinstance(text, dict):
                s = str(text.get("text", ""))
            elif isinstance(text, (tuple, list)) and len(text) == 2:
                s = str(text[1])
            else:
                s = str(text)
            s = _normalize_unicode_tex(s)
            stripped = s.strip()
            if len(stripped) >= 2 and stripped[0] == "$" and stripped[-1] == "$":
                return stripped
            if "\\" in s:
                return s
            mixed = _split_label_dollar_segments(s)
            if mixed:
                return f"${mixed}$"
            return _escape_label_text_segment(s)

        if side in ("right", "left"):
            edge = "center"
            col = span.col_end if side == "right" else max(span.col_start - 1, 1)
            line_gap = float(item.get("line_gap_mm", 3.5))
            outward_shift = 0
            base_shift = offset
            default_xshift = base_shift + outward_shift + xshift_mm
            direction = 1 if side == "right" else -1
            anchor = "center"
            if labels and isinstance(labels[0], (list, tuple)):
                for col_idx, col_vals in enumerate(labels):
                    gap_shift = direction * col_idx * line_gap
                    for i, text in enumerate(col_vals):
                        row = span.row_start + i
                        coord = f"({row}-{col}.{edge})"
                        opts = f"anchor={anchor}"
                        xshift = default_xshift + gap_shift
                        if xshift:
                            opts += f", xshift={xshift}mm"
                        if yshift_mm:
                            opts += f", yshift={yshift_mm}mm"
                        opts += ", align=center"
                        if style:
                            opts += f", {style}"
                        out.append((coord, _wrap_math(text), opts))
            else:
                for i, text in enumerate(labels):
                    row = span.row_start + i
                    coord = f"({row}-{col}.{edge})"
                    opts = f"anchor={anchor}"
                    if default_xshift:
                        opts += f", xshift={default_xshift}mm"
                    if yshift_mm:
                        opts += f", yshift={yshift_mm}mm"
                    opts += ", align=center"
                    if style:
                        opts += f", {style}"
                    out.append((coord, _wrap_math(text), opts))
            continue

        if side in ("above", "below"):
            h_anchor = "center"
            anchor = h_anchor
            row = span.row_start if side == "above" else span.row_end
            base_shift = offset
            default_gap = 3.5 if side == "above" else 4.5
            line_gap = float(item.get("line_gap_mm", default_gap))
            row_shift = yshift_mm
            row_count = label_rows_count.get((key[0], key[1], side), 0)
            if side == "above" and row_count:
                label_row_start = span.row_start - row_count
            elif side == "below" and row_count:
                label_row_start = span.row_end + 1
            else:
                label_row_start = row
            if labels and isinstance(labels[0], (list, tuple)):
                for row_idx, row_vals in enumerate(labels):
                    if row_count:
                        row = label_row_start + row_idx
                        yshift = base_shift + row_shift
                    else:
                        row = span.row_start if side == "above" else span.row_end
                        yshift = base_shift + row_shift + (row_idx * line_gap if side == "above" else -row_idx * line_gap)
                    for j, text in enumerate(row_vals):
                        col = span.col_start + j
                        coord = f"({row}-{col}.{h_anchor})"
                        opts = f"anchor={anchor}"
                        if yshift:
                            opts += f", yshift={yshift}mm"
                        if style:
                            opts += f", {style}"
                        out.append((coord, _wrap_math(text), opts))
            else:
                for j, text in enumerate(labels):
                    col = span.col_start + j
                    row = label_row_start
                    coord = f"({row}-{col}.{h_anchor})"
                    opts = f"anchor={anchor}"
                    yshift = base_shift + row_shift
                    if yshift:
                        opts += f", yshift={yshift}mm"
                    if style:
                        opts += f", {style}"
                    out.append((coord, _wrap_math(text), opts))
            continue

    return out


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
    Nrhs: int = 0,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    extension: str = "",
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

    tex = render_ge_tex(
        matrices=matrices,
        Nrhs=Nrhs,
        formatter=formatter,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        extension=extension,
        fig_scale=fig_scale,
        layout=layout,
        decorations=decorations,
        spec=spec,
        **kwargs,
    )
    use_spec = _coerce_grid_spec(spec)
    if use_spec is not None:
        matrices = use_spec.matrices
        Nrhs = use_spec.Nrhs
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
    spans = grid_submatrix_spans(
        matrices,
        Nrhs=Nrhs,
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
    Nrhs: Any = None,
    formatter: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    block_vspace_mm: int = 1,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    extension: str = "",
    fig_scale: Optional[Union[float, int, str]] = None,
    format_nrhs: Optional[bool] = None,
    preamble: Optional[str] = None,
    nice_options: Optional[str] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
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
    specs: Optional[Sequence[Mapping[str, Any]]] = None,
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
    matrices, Nrhs, formatter, outer_hspace_mm, block_vspace_mm, cell_align:
        See :func:`render_ge_tex`.
    toolchain_name, crop, padding:
        Passed through to the renderer.
    specs:
        Additional mapping specs that can include ``labels`` entries.

    Returns
    -------
    str
        SVG text.
    """
    if "label_targets" in kwargs:
        raise ValueError("label_targets is removed; use specs instead.")

    tex = render_ge_tex(
        matrices=matrices,
        Nrhs=Nrhs,
        formatter=formatter,
        outer_hspace_mm=outer_hspace_mm,
        block_vspace_mm=block_vspace_mm,
        cell_align=cell_align,
        block_align=block_align,
        block_valign=block_valign,
        extension=extension,
        fig_scale=fig_scale,
        format_nrhs=format_nrhs,
        preamble=preamble,
        nice_options=nice_options,
        decorators=decorators,
        decorations=decorations,
        strict=strict,
        spec=spec,
        specs=specs,
        label_rows=label_rows,
        label_cols=label_cols,
        label_gap_mm=label_gap_mm,
        variable_labels=variable_labels,
        **kwargs,
    )
    opts = merge_render_opts(
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
