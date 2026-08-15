"""GE row-echelon path construction helpers.

Staircase invariant:

- vertical path segments follow the left edge of pivot columns;
- horizontal path segments follow the bottom edge of pivot rows;
- paths use NiceMatrix projected rule coordinates, ``(row-|col)``;
- paths do not use cell anchors such as ``.north``, ``.south``, ``.east``, or
  ``.west``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple

__all__ = ["rowechelon_paths_from_specs"]

_REMOVED_ROWECH_PATH_KEYS = frozenset({"node_offsets", "adj", "left_pad"})


@dataclass(frozen=True)
class RowEchelonPathSpec:
    """Canonical row-echelon path selector.

    Coordinates are 0-based matrix-entry coordinates within the targeted grid
    block. Callers pass this shape before any
    staircase geometry is built.
    """

    grid: Tuple[int, int]
    pivots: Sequence[Tuple[int, int]]
    case: str = "hh"
    color: str = "blue,line width=0.4mm"
    path_offsets: Any = (0.0, 0.0)


def _normalize_path_offsets(value: Any = (0.0, 0.0)) -> Tuple[float, float]:
    if isinstance(value, (list, tuple)):
        if not value:
            return (0.0, 0.0)
        if len(value) == 1:
            v = float(value[0])
            return (v, v)
        return (float(value[0]), float(value[1]))
    v = float(value)
    return (v, v)


def _offset_node(point: str, offsets: Tuple[float, float]) -> str:
    dx, dy = offsets
    if not dx and not dy:
        return point
    return f"($ {point} + ({dx:g},{dy:g}) $)"


def _normalize_pivots(pivots: Any) -> List[Tuple[int, int]]:
    return [(int(p[0]), int(p[1])) for p in (pivots or [])]


def _normalize_rowechelon_path_spec(spec: Any) -> RowEchelonPathSpec | None:
    if isinstance(spec, dict):
        grid = spec.get("grid")
        if not isinstance(grid, (list, tuple)) or len(grid) != 2:
            return None
        removed = _REMOVED_ROWECH_PATH_KEYS & set(spec)
        if removed:
            names = ", ".join(sorted(removed))
            raise ValueError(f"{names} is removed; use path_offsets instead")
        return RowEchelonPathSpec(
            grid=(int(grid[0]), int(grid[1])),
            pivots=_normalize_pivots(spec.get("pivots", spec.get("entries", []))),
            case=str(spec.get("case", "hh")),
            color=str(spec.get("color", "blue,line width=0.4mm")),
            path_offsets=spec.get("path_offsets", (0.0, 0.0)),
        )
    if isinstance(spec, RowEchelonPathSpec):
        return spec
    return None


def _rowechelon_path_specs_from_items(items: Sequence[Any]) -> List[RowEchelonPathSpec]:
    out: List[RowEchelonPathSpec] = []
    for item in items:
        normalized = _normalize_rowechelon_path_spec(item)
        if normalized is not None:
            out.append(normalized)
    return out


def _pivot_rule_point(
    i: int,
    j: int,
    *,
    shape: Tuple[int, int],
    top_left_row: int,
    top_left_col: int,
    path_offsets: Tuple[float, float],
    left_delim_node: str,
) -> str:
    if i <= 0:
        row = top_left_row + 1
    else:
        row_i = min(int(i) - 1, max(shape[0] - 1, 0))
        row = row_i + top_left_row + 2
    if j == 0:
        dx = 0.1 + path_offsets[0]
        dy = path_offsets[1]
        p = f"({row}-|{left_delim_node})"
        if dx or dy:
            return f"($ {p} + ({dx:g},{dy:g}) $)"
        return p
    if j >= shape[1]:
        col = top_left_col + shape[1] + 1
        return _offset_node(f"({row}-|{col})", path_offsets)

    col_j = min(max(int(j), 0), max(shape[1] - 1, 0))
    col = col_j + top_left_col + 1
    return _offset_node(f"({row}-|{col})", path_offsets)


def _staircase_points(
    pivots: Sequence[Tuple[int, int]],
    *,
    case: str,
    shape: Tuple[int, int],
) -> List[Tuple[int, int]]:
    cur = pivots[0]
    points = [cur] if (case == "vv") or (case == "vh") else []
    for nxt in pivots[1:]:
        if cur[0] != nxt[0]:
            cur = (cur[0] + 1, cur[1])
            points.append(cur)
        if nxt[1] != cur[1]:
            cur = (cur[0], nxt[1])
            points.append(cur)
        if cur != nxt:
            points.append(nxt)
        cur = nxt

    if len(points) == 0 and case == "hv":
        points = [(pivots[0][0] + 1, pivots[0][0]), (shape[0], pivots[0][1])]

    if (case == "hh") or (case == "vh"):
        if cur[0] != shape[0]:
            cur = (cur[0] + 1, cur[1])
            points.append(cur)
        points.append((cur[0], shape[1]))
    else:
        points.append((shape[0], cur[1]))

    compact: List[Tuple[int, int]] = []
    for p in points:
        if not compact or compact[-1] != p:
            compact.append(p)
    return compact


def _rowechelon_path_commands_from_specs(
    matrices: Sequence[Sequence[Any]],
    specs: Sequence[Any],
    *,
    submatrix_name_style: str = "grid",
) -> List[str]:
    """Build canonical GE row-echelon staircase path commands."""

    out: List[str] = []
    from .ge_grid_specs import grid_submatrix_spans

    spans = grid_submatrix_spans(
        matrices,
        submatrix_name_style=submatrix_name_style,
    )
    span_map = {(s.block_row, s.block_col): s for s in spans}
    for normalized in _rowechelon_path_specs_from_items(specs):
        gM, gN = normalized.grid
        pivots = normalized.pivots
        case = normalized.case
        color = normalized.color
        raw_path_offsets = normalized.path_offsets
        path_offsets = _normalize_path_offsets(raw_path_offsets)
        span = span_map.get((gM, gN))
        if span is None:
            continue
        shape = (span.row_end - span.row_start + 1, span.col_end - span.col_start + 1)
        if not pivots:
            continue

        top_left_row = span.row_start - 1
        top_left_col = span.col_start - 1
        compact = _staircase_points(pivots, case=case, shape=shape)

        rendered_points: List[str] = []
        for p in compact:
            rendered = _pivot_rule_point(
                *p,
                shape=shape,
                top_left_row=top_left_row,
                top_left_col=top_left_col,
                path_offsets=path_offsets,
                left_delim_node=span.left_delim_node,
            )
            if not rendered_points or rendered_points[-1] != rendered:
                rendered_points.append(rendered)

        cmd = "\\draw[" + color + "] " + " -- ".join(rendered_points) + ";"
        out.append(cmd)
    return out


def rowechelon_paths_from_specs(
    matrices: Sequence[Sequence[Any]],
    specs: Sequence[Any],
    *,
    submatrix_name_style: str = "grid",
) -> List[str]:
    """Convert structured GE row-echelon path specs into TikZ draw commands."""

    return _rowechelon_path_commands_from_specs(
        matrices,
        specs,
        submatrix_name_style=submatrix_name_style,
    )
