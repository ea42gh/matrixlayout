"""GE spec coercion and merge helpers.

This module keeps the public GE renderer focused on layout generation.  The
helpers here are intentionally small and side-effect free: they coerce typed or
dict specs and merge those values with explicit renderer keyword arguments.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union

from .formatting import latexify
from .specs import GEGridSpec, GELayoutSpec

LatexFormatter = Callable[[Any], str]


def coerce_layout_spec(layout: Any) -> Optional[GELayoutSpec]:
    """Coerce ``layout`` into a :class:`GELayoutSpec` (or None)."""
    if layout is None:
        return None
    if isinstance(layout, GELayoutSpec):
        return layout
    if isinstance(layout, dict):
        return GELayoutSpec.from_dict(layout)
    raise TypeError(f"layout must be a GELayoutSpec or dict, not {type(layout).__name__}")


def coerce_grid_spec(spec: Any) -> Optional[GEGridSpec]:
    """Coerce ``spec`` into a :class:`GEGridSpec` (or None)."""
    if spec is None:
        return None
    if isinstance(spec, GEGridSpec):
        return spec
    if isinstance(spec, dict):
        return GEGridSpec.from_dict(spec)
    raise TypeError(f"spec must be a GEGridSpec or dict, not {type(spec).__name__}")


def merge_scalar(field: str, explicit: Any, spec_val: Any) -> Any:
    """Merge a scalar field from explicit kwargs and layout spec.

    Raise on conflicting values when both are explicitly provided.
    """
    if spec_val is None:
        return explicit
    if explicit is None:
        return spec_val
    if explicit != spec_val:
        raise ValueError(f"Conflicting values for {field}: explicit={explicit!r} spec={spec_val!r}")
    return explicit


def merge_scalar_prefer_explicit(field: str, explicit: Any, spec_val: Any) -> Any:
    """Merge a scalar field, preferring explicit kwargs when provided."""
    if explicit is None:
        return spec_val
    return explicit


def merge_scalar_default(field: str, explicit: Any, spec_val: Any, default: Any) -> Any:
    """Merge a field whose renderer default is represented as ``None``."""
    _ = (field, default)
    if spec_val is None:
        return explicit
    if explicit is None:
        return spec_val
    return explicit


def grid_spec_defaults(
    outer_hspace_mm: Optional[int],
    block_vspace_mm: Optional[int],
) -> Tuple[Optional[int], Optional[int]]:
    """Treat default spacing values as unset when a grid spec is provided."""
    if outer_hspace_mm == 6:
        outer_hspace_mm = None
    if block_vspace_mm == 1:
        block_vspace_mm = None
    return outer_hspace_mm, block_vspace_mm


def merge_grid_spec_inputs(
    *,
    grid_spec: GEGridSpec,
    matrices: Optional[Sequence[Sequence[Any]]],
    Nrhs: Any,
    formatter: LatexFormatter,
    outer_hspace_mm: int,
    block_vspace_mm: int,
    cell_align: str,
    block_align: Optional[str],
    block_valign: Optional[str],
    extension: str,
    fig_scale: Optional[Union[float, int, str]],
    format_nrhs: Optional[bool],
    decorators: Optional[Sequence[Any]],
    decorations: Optional[Sequence[Any]],
    strict: Optional[bool],
    label_rows: Optional[Sequence[Any]],
    label_cols: Optional[Sequence[Any]],
    label_gap_mm: Optional[float],
    variable_labels: Optional[Sequence[Any]],
    kwargs: Dict[str, Any],
) -> Tuple[
    Optional[Sequence[Sequence[Any]]],
    Any,
    LatexFormatter,
    int,
    int,
    str,
    Optional[str],
    Optional[str],
    str,
    Optional[Union[float, int, str]],
    bool,
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    bool,
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[float],
    Optional[Sequence[Any]],
    Dict[str, Any],
]:
    """Merge grid spec values into explicit kwargs (explicit wins)."""
    default_outer_hspace_mm, default_block_vspace_mm = grid_spec_defaults(outer_hspace_mm, block_vspace_mm)

    matrices = merge_scalar_prefer_explicit("matrices", matrices, grid_spec.matrices)
    Nrhs = merge_scalar_default("Nrhs", Nrhs, grid_spec.Nrhs, 0)
    formatter = merge_scalar_default("formatter", formatter, grid_spec.formatter or latexify, latexify)
    outer_hspace_mm = int(
        merge_scalar_prefer_explicit("outer_hspace_mm", default_outer_hspace_mm, grid_spec.outer_hspace_mm)
    )
    block_vspace_mm = int(
        merge_scalar_prefer_explicit("block_vspace_mm", default_block_vspace_mm, grid_spec.block_vspace_mm)
    )
    cell_align = str(merge_scalar_default("cell_align", cell_align, grid_spec.cell_align, "r"))
    block_align = merge_scalar_prefer_explicit("block_align", block_align, grid_spec.block_align)
    block_valign = merge_scalar_prefer_explicit("block_valign", block_valign, grid_spec.block_valign)
    extension = str(merge_scalar_default("extension", extension, grid_spec.extension, ""))
    fig_scale = merge_scalar_prefer_explicit("fig_scale", fig_scale, grid_spec.fig_scale)
    format_nrhs = bool(merge_scalar_default("format_nrhs", format_nrhs, grid_spec.format_nrhs, True))
    kwargs["legacy_submatrix_names"] = bool(
        merge_scalar_prefer_explicit(
            "legacy_submatrix_names",
            kwargs.get("legacy_submatrix_names"),
            grid_spec.legacy_submatrix_names,
        )
    )
    kwargs["legacy_format"] = bool(
        merge_scalar_prefer_explicit("legacy_format", kwargs.get("legacy_format"), grid_spec.legacy_format)
    )
    if grid_spec.preamble is not None:
        kwargs["preamble"] = merge_scalar_prefer_explicit("preamble", kwargs.get("preamble"), grid_spec.preamble)
    if grid_spec.nice_options is not None:
        kwargs["nice_options"] = merge_scalar_prefer_explicit(
            "nice_options",
            kwargs.get("nice_options"),
            grid_spec.nice_options,
        )
    if grid_spec.outer_delims is not None:
        kwargs["outer_delims"] = bool(
            merge_scalar_prefer_explicit("outer_delims", kwargs.get("outer_delims"), grid_spec.outer_delims)
        )
    if grid_spec.pivot_locs is not None:
        kwargs["pivot_locs"] = merge_scalar_prefer_explicit(
            "pivot_locs",
            kwargs.get("pivot_locs"),
            grid_spec.pivot_locs,
        )
    if grid_spec.txt_with_locs is not None:
        kwargs["txt_with_locs"] = merge_scalar_prefer_explicit(
            "txt_with_locs",
            kwargs.get("txt_with_locs"),
            grid_spec.txt_with_locs,
        )
    if grid_spec.rowechelon_paths is not None:
        kwargs["rowechelon_paths"] = merge_scalar_prefer_explicit(
            "rowechelon_paths",
            kwargs.get("rowechelon_paths"),
            grid_spec.rowechelon_paths,
        )
    if grid_spec.callouts is not None:
        kwargs["callouts"] = merge_scalar_prefer_explicit("callouts", kwargs.get("callouts"), grid_spec.callouts)
    if grid_spec.codebefore is not None:
        kwargs["codebefore"] = merge_scalar_prefer_explicit(
            "codebefore",
            kwargs.get("codebefore"),
            grid_spec.codebefore,
        )
    if grid_spec.create_cell_nodes is not None:
        kwargs["create_cell_nodes"] = merge_scalar_prefer_explicit(
            "create_cell_nodes",
            kwargs.get("create_cell_nodes"),
            grid_spec.create_cell_nodes,
        )
    if grid_spec.create_medium_nodes is not None:
        kwargs["create_medium_nodes"] = merge_scalar_prefer_explicit(
            "create_medium_nodes",
            kwargs.get("create_medium_nodes"),
            grid_spec.create_medium_nodes,
        )
    if grid_spec.layout is not None:
        kwargs["layout"] = merge_scalar_prefer_explicit("layout", kwargs.get("layout"), grid_spec.layout)
    label_rows = merge_scalar_prefer_explicit("label_rows", label_rows, grid_spec.label_rows)
    label_cols = merge_scalar_prefer_explicit("label_cols", label_cols, grid_spec.label_cols)
    label_gap_mm = merge_scalar_default("label_gap_mm", label_gap_mm, grid_spec.label_gap_mm, 0.8)
    variable_labels = merge_scalar_prefer_explicit("variable_labels", variable_labels, grid_spec.variable_labels)
    decorators = merge_scalar_prefer_explicit("decorators", decorators, grid_spec.decorators)
    decorations = merge_scalar_prefer_explicit("decorations", decorations, grid_spec.decorations)
    strict = bool(merge_scalar_default("strict", strict, grid_spec.strict, False))

    return (
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
    )
