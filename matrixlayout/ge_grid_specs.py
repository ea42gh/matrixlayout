"""Structured GE grid span, line, and highlight helper utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .ge_grid import as_2d_list as _as_2d_list
from .ge_grid import block_pad_left as _block_pad_left
from .ge_grid import block_pad_top as _block_pad_top
from .ge_grid import normalize_grid_input as _normalize_grid_input
from .ge_labels import build_label_maps as _build_label_maps
from .specs import SubMatrixSpan


def grid_submatrix_spans(
    matrices: Sequence[Sequence[Any]],
    *,
    n_rhs: int = 0,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
    label_rows: Optional[Sequence[Any]] = None,
    label_cols: Optional[Sequence[Any]] = None,
    variable_labels: Optional[Sequence[Any]] = None,
    legacy_submatrix_names: bool = False,
) -> List[SubMatrixSpan]:
    """Return the resolved ``\\SubMatrix`` spans for a GE matrix grid."""

    grid: List[List[Any]] = _normalize_grid_input(matrices)
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(row) for row in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    for row in range(n_block_rows):
        if len(grid[row]) < n_block_cols:
            grid[row].extend([None] * (n_block_cols - len(grid[row])))

    block_heights: List[int] = [0] * n_block_rows
    block_widths: List[int] = [0] * n_block_cols
    cell_cache: List[List[Tuple[List[List[Any]], int, int]]] = [
        [([], 0, 0) for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]

    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows, height, width = _as_2d_list(grid[br][bc])
            cell_cache[br][bc] = (rows, height, width)
            block_heights[br] = max(block_heights[br], height)
            block_widths[bc] = max(block_widths[bc], width)

    max_height = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_height > 0:
            block_widths[bc] = max_height

    if any(width <= 0 for width in block_widths) or any(height <= 0 for height in block_heights):
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

    _ = (n_rhs, outer_hspace_mm, cell_align)

    block_pad_left: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    block_pad_top: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _rows, height, width = cell_cache[br][bc]
            if height == 0 or width == 0:
                continue
            block_pad_left[br][bc] = _block_pad_left(block_widths[bc], width, block_align)
            block_pad_top[br][bc] = _block_pad_top(block_heights[br], height, block_valign)

    row_starts: List[int] = []
    acc = 1
    for height in total_block_heights:
        row_starts.append(acc)
        acc += height

    col_starts: List[int] = []
    acc = 1
    for width in total_block_widths:
        col_starts.append(acc)
        acc += width

    spans: List[SubMatrixSpan] = []
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _rows, height, width = cell_cache[br][bc]
            if height == 0 or width == 0:
                continue

            row_start = row_starts[br] + extra_rows_above[br] + block_pad_top[br][bc]
            col_start = col_starts[bc] + extra_cols_left[bc] + block_pad_left[br][bc]
            row_end = row_start + height - 1
            col_end = col_start + width - 1

            if legacy_submatrix_names:
                name = f"A{br}x{bc}"
            else:
                if n_block_cols == 2:
                    base = "E" if bc == 0 else "A"
                else:
                    base = f"M{bc}"
                name = f"{base}{br}"

            spans.append(
                SubMatrixSpan(
                    name=name,
                    row_start=row_start,
                    col_start=col_start,
                    row_end=row_end,
                    col_end=col_end,
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

    def _normalize_lines(value: Any, max_idx: int) -> List[int]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            items = [int(item) for item in value]
        else:
            items = [int(value)]
        out = [item for item in items if 1 <= item <= max_idx]
        return sorted(set(out))

    targets_set = {(int(row), int(col)) for row, col in targets}
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
        _rows, height, width = _as_2d_list(matrices[key[0]][key[1]])
        if height == 0 or width == 0:
            continue
        hspec = _normalize_lines(hlines, height - 1)
        vspec = _normalize_lines(vlines, width - 1)
        if not hspec and not vspec:
            continue
        opts: List[str] = ["delimiters/color=."]
        if hspec:
            if len(hspec) == 1:
                opts.append(f"hlines={hspec[0]}")
            else:
                opts.append("hlines={" + ",".join(str(item) for item in hspec) + "}")
        if vspec:
            if len(vspec) == 1:
                opts.append(f"vlines={vspec[0]}")
            else:
                opts.append("vlines={" + ",".join(str(item) for item in vspec) + "}")
        out.append((",".join(opts), span.start_token, span.end_token))
    return out


def normalize_range(value: Any, max_len: int) -> Tuple[int, int]:
    if max_len <= 0:
        return (0, -1)
    if value is None:
        return (0, max_len - 1)
    if isinstance(value, slice):
        start = 0 if value.start is None else int(value.start)
        stop = max_len if value.stop is None else int(value.stop)
        return (max(0, start), min(max_len - 1, stop - 1))
    if isinstance(value, str):
        text = value.strip()
        if ":" in text:
            left, right = text.split(":", 1)
            start = int(left) if left.strip() else 0
            end = int(right) if right.strip() else (max_len - 1)
            lo, hi = (start, end) if start <= end else (end, start)
            return (max(0, lo), min(max_len - 1, hi))
    if isinstance(value, (tuple, list)) and len(value) == 2 and all(isinstance(item, int) for item in value):
        a, b = int(value[0]), int(value[1])
        lo, hi = (a, b) if a <= b else (b, a)
        return (max(0, lo), min(max_len - 1, hi))
    if isinstance(value, (list, tuple, set)):
        items = [int(item) for item in value]
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
            item: Dict[str, Any] = {"grid": obj[0]}
            if len(obj) > 1:
                item["rows"] = obj[1]
            if len(obj) > 2:
                item["cols"] = obj[2]
            if len(obj) > 3:
                item["color"] = obj[3]
            return item
        raise ValueError("block highlight must be a dict or a (grid, rows, cols) tuple")

    spans = grid_submatrix_spans(
        matrices,
        block_align=block_align,
        block_valign=block_valign,
    )
    span_map = {(span.block_row, span.block_col): span for span in spans}
    out: List[str] = []
    for spec in blocks:
        item = _coerce_block(spec)
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            raise ValueError("highlight spec requires grid=(row,col)")
        key = (int(grid[0]), int(grid[1]))
        if key not in span_map:
            continue
        matrix = matrices[key[0]][key[1]]
        _rows, height, width = _as_2d_list(matrix)
        if height == 0 or width == 0:
            continue
        row_start_idx, row_end_idx = normalize_range(item.get("rows"), height)
        col_start_idx, col_end_idx = normalize_range(item.get("cols"), width)
        if row_end_idx < row_start_idx or col_end_idx < col_start_idx:
            continue
        span = span_map[key]
        row_start = span.row_start + row_start_idx
        row_end = span.row_start + row_end_idx
        col_start = span.col_start + col_start_idx
        col_end = span.col_start + col_end_idx
        fill = str(item.get("color", color))
        pad = float(item.get("padding_pt", padding_pt))
        out.append(
            rf"\tikz \node [fill={fill}, inner sep={pad}pt, fit=({row_start}-{col_start}) ({row_end}-{col_end})] {{}};"
        )
    return out
