"""GE layout merge helpers used by the public renderer wrappers."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Tuple

from .ge_spec_merge import merge_scalar as _merge_scalar
from .ge_template import merge_callouts as _merge_callouts, merge_list as _merge_list
from .specs import GELayoutSpec


def resolve_annotations(
    *,
    annotations: Optional[Sequence[Mapping[str, Any]]],
) -> Optional[Sequence[Mapping[str, Any]]]:
    """Return the canonical label/callout annotation specs."""

    return annotations


def merge_layout_string_hooks(
    *,
    spec: Optional[GELayoutSpec],
    document_preamble: str,
    body_preamble: str,
) -> Tuple[str, str]:
    if spec is None:
        return document_preamble, body_preamble
    spec_document_preamble = spec.document_preamble
    spec_body_preamble = spec.body_preamble
    if spec_document_preamble:
        document_preamble = (
            (spec_document_preamble or "")
            + ("\n" if (spec_document_preamble and document_preamble) else "")
            + (document_preamble or "")
        )
    if spec_body_preamble:
        body_preamble = (
            (spec_body_preamble or "")
            + ("\n" if (spec_body_preamble and body_preamble) else "")
            + (body_preamble or "")
        )
    return document_preamble, body_preamble


def merge_layout_fields(
    *,
    spec: Optional[GELayoutSpec],
    nice_options: Optional[str],
    landscape: Optional[bool],
    create_cell_nodes: Optional[bool],
    create_extra_nodes: Optional[bool],
    create_medium_nodes: Optional[bool],
    outer_delims: Optional[bool],
    outer_delims_name: Optional[str],
    outer_delims_span: Optional[Tuple[int, int]],
    codebefore: Optional[Sequence[str]],
    submatrix_locs: Optional[Sequence[Any]],
    submatrix_names: Optional[Sequence[str]],
    pivot_locs: Optional[Sequence[Any]],
    txt_with_locs: Optional[Sequence[Any]],
    rowechelon_paths: Optional[Sequence[Any]],
    callouts: Optional[Sequence[Any]],
    matrix_labels: Optional[Sequence[Any]],
) -> Tuple[
    Optional[str],
    Optional[bool],
    Optional[bool],
    Optional[bool],
    Optional[bool],
    Optional[bool],
    Optional[str],
    Optional[Tuple[int, int]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
    Optional[Sequence[Any]],
]:
    if spec is None:
        return (
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
            txt_with_locs,
            rowechelon_paths,
            callouts,
        )

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
    callouts = _merge_callouts(callouts, matrix_labels)

    return (
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
        txt_with_locs,
        rowechelon_paths,
        callouts,
    )


