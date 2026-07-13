"""GE row-echelon path construction helpers.

Staircase invariant:

- vertical path segments follow the left edge of pivot columns;
- horizontal path segments follow the bottom edge of pivot rows;
- paths use NiceMatrix projected rule coordinates, ``(row-|col)``;
- paths do not use cell anchors such as ``.north``, ``.south``, ``.east``, or
  ``.west``.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple


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


def _normalize_ref_path_spec(spec: Any) -> Tuple[int, int, Any, str, str, Any, Any, Any] | None:
    if isinstance(spec, dict):
        grid = spec.get("grid")
        if not isinstance(grid, (list, tuple)) or len(grid) != 2:
            return None
        return (
            int(grid[0]),
            int(grid[1]),
            list(spec.get("pivots", spec.get("entries", [])) or []),
            str(spec.get("case", "hh")),
            str(spec.get("color", "blue,line width=0.4mm")),
            spec.get("adj", 0.1),
            spec.get("left_pad", 0.0),
            spec.get("node_offsets", (0.0, 0.0)),
        )
    if isinstance(spec, (list, tuple)) and len(spec) >= 3:
        return (
            int(spec[0]),
            int(spec[1]),
            spec[2],
            spec[3] if len(spec) > 3 else "hh",
            spec[4] if len(spec) > 4 else "blue,line width=0.4mm",
            spec[5] if len(spec) > 5 else 0.1,
            spec[6] if len(spec) > 6 else 0.0,
            spec[7] if len(spec) > 7 else (0.0, 0.0),
        )
    return None


def rowechelon_paths_from_specs(
    matrices: Sequence[Sequence[Any]],
    specs: Sequence[Any],
    *,
    legacy_submatrix_names: bool = True,
) -> List[str]:
    """Convert GE row-echelon path specs into TikZ draw commands."""

    out: List[str] = []
    from .ge_grid_specs import grid_submatrix_spans

    spans = grid_submatrix_spans(matrices, legacy_submatrix_names=legacy_submatrix_names)
    span_map = {(s.block_row, s.block_col): s for s in spans}
    for spec in specs:
        normalized = _normalize_ref_path_spec(spec)
        if normalized is None:
            continue
        gM, gN, pivots, case, color, _adj, left_pad, raw_node_offsets = normalized
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


def ref_path_list_to_rowechelon_paths(
    matrices: Sequence[Sequence[Any]],
    ref_path_list: Sequence[Any],
    *,
    legacy_submatrix_names: bool = True,
) -> List[str]:
    return rowechelon_paths_from_specs(
        matrices,
        ref_path_list,
        legacy_submatrix_names=legacy_submatrix_names,
    )
