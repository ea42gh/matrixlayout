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


@dataclass(frozen=True)
class RowEchelonPathSpec:
    """Canonical row-echelon path selector.

    Coordinates are 0-based matrix-entry coordinates within the targeted grid
    block. Legacy ref-path tuple inputs are converted to this shape before any
    staircase geometry is built.
    """

    grid: Tuple[int, int]
    pivots: Sequence[Tuple[int, int]]
    case: str = "hh"
    color: str = "blue,line width=0.4mm"
    adj: Any = 0.1
    left_pad: Any = 0.0
    node_offsets: Any = (0.0, 0.0)


def _normalize_node_offsets(value: Any = (0.0, 0.0)) -> Tuple[float, float]:
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
        return RowEchelonPathSpec(
            grid=(int(grid[0]), int(grid[1])),
            pivots=_normalize_pivots(spec.get("pivots", spec.get("entries", []))),
            case=str(spec.get("case", "hh")),
            color=str(spec.get("color", "blue,line width=0.4mm")),
            adj=spec.get("adj", 0.1),
            left_pad=spec.get("left_pad", 0.0),
            node_offsets=spec.get("node_offsets", (0.0, 0.0)),
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


def _rowechelon_path_commands_from_specs(
    matrices: Sequence[Sequence[Any]],
    specs: Sequence[Any],
    *,
    legacy_submatrix_names: bool = True,
) -> List[str]:
    """Build canonical GE row-echelon staircase path commands."""

    out: List[str] = []
    from .ge_grid_specs import grid_submatrix_spans

    spans = grid_submatrix_spans(matrices, legacy_submatrix_names=legacy_submatrix_names)
    span_map = {(s.block_row, s.block_col): s for s in spans}
    for normalized in _rowechelon_path_specs_from_items(specs):
        gM, gN = normalized.grid
        pivots = normalized.pivots
        case = normalized.case
        color = normalized.color
        _adj = normalized.adj
        left_pad = normalized.left_pad
        raw_node_offsets = normalized.node_offsets
        node_offsets = _normalize_node_offsets(raw_node_offsets)
        span = span_map.get((gM, gN))
        if span is None:
            continue
        shape = (span.row_end - span.row_start + 1, span.col_end - span.col_start + 1)
        if not pivots:
            continue

        tlr = span.row_start - 1
        tlc = span.col_start - 1

        def coords(
            i: int,
            j: int,
            *,
            shape: Tuple[int, int] = shape,
            tlr: int = tlr,
            tlc: int = tlc,
            adj: float = float(_adj),
            left_pad: float = left_pad,
            node_offsets: Tuple[float, float] = node_offsets,
            left_delim_node: str = span.left_delim_node,
        ) -> str:
            if i <= 0:
                row = tlr + 1
            else:
                row_i = min(int(i) - 1, max(shape[0] - 1, 0))
                row = row_i + tlr + 2
            if j == 0:
                dx = adj - float(left_pad) + node_offsets[0]
                dy = node_offsets[1]
                p = f"({row}-|{left_delim_node})"
                if dx or dy:
                    return f"($ {p} + ({dx:g},{dy:g}) $)"
                return p
            elif j >= shape[1]:
                col = tlc + shape[1] + 1
                p = f"({row}-|{col})"
            else:
                col_j = min(max(int(j), 0), max(shape[1] - 1, 0))
                col = col_j + tlc + 1
                p = f"({row}-|{col})"

            return _offset_node(p, node_offsets)

        cur = pivots[0]
        ll = [cur] if (case == "vv") or (case == "vh") else []
        for nxt in pivots[1:]:
            if cur[0] != nxt[0]:
                cur = (cur[0] + 1, cur[1])
                ll.append(cur)
            if nxt[1] != cur[1]:
                cur = (cur[0], nxt[1])
                ll.append(cur)
            if cur != nxt:
                ll.append(nxt)
            cur = nxt

        if len(ll) == 0 and case == "hv":
            ll = [(pivots[0][0] + 1, pivots[0][0]), (shape[0], pivots[0][1])]

        if (case == "hh") or (case == "vh"):
            if cur[0] != shape[0]:
                cur = (cur[0] + 1, cur[1])
                ll.append(cur)
            ll.append((cur[0], shape[1]))
        else:
            ll.append((shape[0], cur[1]))

        compact: List[Tuple[int, int]] = []
        for p in ll:
            if not compact or compact[-1] != p:
                compact.append(p)

        rendered_points: List[str] = []
        for p in compact:
            rendered = coords(*p)
            if not rendered_points or rendered_points[-1] != rendered:
                rendered_points.append(rendered)

        cmd = "\\draw[" + color + "] " + " -- ".join(rendered_points) + ";"
        out.append(cmd)
    return out

def rowechelon_paths_from_specs(
    matrices: Sequence[Sequence[Any]],
    specs: Sequence[Any],
    *,
    legacy_submatrix_names: bool = True,
) -> List[str]:
    """Convert structured GE row-echelon path specs into TikZ draw commands."""

    return _rowechelon_path_commands_from_specs(
        matrices,
        specs,
        legacy_submatrix_names=legacy_submatrix_names,
    )
