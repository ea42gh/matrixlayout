"""Decorator helpers for eigen/QR/SVD table layouts."""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple

from .formatting import apply_decorator, expand_entry_selectors


LatexFormatter = Callable[[Any], str]
DecoratorSpec = Tuple[Callable[..., str], set[Tuple[int, int, int]]]


def collect_vector_decorator_specs(
    vec_groups: Sequence[Sequence[Iterable[Any]]],
    decorators: Optional[Sequence[Any]],
    target_name: Optional[str],
) -> List[DecoratorSpec]:
    """Return decorator specs that target vector rows in eigproblem tables."""
    if not decorators or not target_name:
        return []

    target_key = target_name.lower()

    dec_specs: List[DecoratorSpec] = []
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("target")
        if key is None or str(key).lower() != target_key:
            continue
        dec = spec_item.get("decorator")
        if not callable(dec):
            raise ValueError("decorator must be callable")
        entries = spec_item.get("entries")
        expanded: set[Tuple[int, int, int]] = set()
        if entries is None:
            for g_idx, group in enumerate(vec_groups):
                for v_idx, vec in enumerate(group):
                    for i_idx, _ in enumerate(vec):
                        expanded.add((g_idx, v_idx, i_idx))
        else:
            for ent in entries:
                if isinstance(ent, (list, tuple)) and len(ent) == 3:
                    expanded.add((int(ent[0]), int(ent[1]), int(ent[2])))
                    continue
                if isinstance(ent, (list, tuple)) and len(ent) == 2:
                    a, b = ent
                    if (
                        isinstance(a, (list, tuple))
                        and isinstance(b, (list, tuple))
                        and len(a) == 3
                        and len(b) == 3
                        and int(a[0]) == int(b[0])
                        and int(a[1]) == int(b[1])
                    ):
                        g_idx, v_idx = int(a[0]), int(a[1])
                        i0, i1 = int(a[2]), int(b[2])
                        for i_idx in range(min(i0, i1), max(i0, i1) + 1):
                            expanded.add((g_idx, v_idx, i_idx))
        if expanded:
            dec_specs.append((dec, expanded))
    return dec_specs


def apply_vector_decorators(
    cell: str,
    *,
    value: Any,
    group_index: int,
    vector_index: int,
    entry_index: int,
    dec_specs: Sequence[DecoratorSpec],
    applied_counts: List[int],
) -> str:
    """Apply matching vector-row decorators to one vector cell."""
    out = cell
    for idx, (dec, expanded) in enumerate(dec_specs):
        if (group_index, vector_index, entry_index) in expanded:
            out = apply_decorator(dec, entry_index, vector_index, value, out)
            applied_counts[idx] += 1
    return out


def apply_matrix_decorators(
    mat_tex: List[List[str]],
    mat_raw: List[List[Any]],
    decorators: Optional[Sequence[Any]],
    matrix_ids: Sequence[str],
    formatter: LatexFormatter,
    strict: bool,
) -> List[List[str]]:
    """Apply matrix-targeted decorator specs to a rendered table matrix."""
    if not decorators:
        return mat_tex
    id_set = {str(mid).lower() for mid in matrix_ids}
    nrows = len(mat_tex)
    ncols = len(mat_tex[0]) if nrows else 0
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("matrix", spec_item.get("target"))
        if key is None or str(key).lower() not in id_set:
            continue
        dec = spec_item.get("decorator")
        if not callable(dec):
            raise ValueError("decorator must be callable")
        fmt = spec_item.get("formatter", formatter)
        applied = 0
        for i, j in expand_entry_selectors(spec_item.get("entries"), nrows, ncols):
            if i < 0 or j < 0 or i >= nrows or j >= ncols:
                continue
            raw = mat_raw[i][j]
            base = mat_tex[i][j] or str(fmt(raw))
            mat_tex[i][j] = apply_decorator(dec, i, j, raw, base)
            applied += 1
        if strict and applied == 0:
            raise ValueError("decorator selector did not match any entries")
    return mat_tex
