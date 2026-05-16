"""Assemble flattened GE grid render parts before template rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .formatting import apply_decorator
from .ge_grid import block_pad_left as _block_pad_left
from .ge_grid import block_pad_top as _block_pad_top
from .ge_labels import build_label_maps as _build_label_maps
from .ge_labels import compute_label_extras as _compute_label_extras
from .ge_labels import embed_col_labels as _embed_col_labels
from .ge_labels import embed_row_labels as _embed_row_labels
from .ge_labels import escape_label_text_segment as _escape_label_text_segment
from .ge_labels import split_label_dollar_segments as _split_label_dollar_segments


DecoratorMap = Dict[
    Tuple[int, int],
    List[Tuple[Callable[..., str], set[Tuple[int, int]], Callable[[Any], str]]],
]


@dataclass(frozen=True)
class GEGridRenderParts:
    """Flattened GE grid components consumed by the GE template layer."""

    mat_rep: str
    mat_format: str
    submatrix_locs: List[Tuple[str, str, str]]
    name_map: Dict[Tuple[int, int], str]


def _coerce_label_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text", ""))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return str(value[1])
    return str(value)


def _format_label_cell(value: Any) -> str:
    text = _coerce_label_text(value)
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == "$" and stripped[-1] == "$":
        return stripped[1:-1]
    if "\\" in text:
        return text
    mixed = _split_label_dollar_segments(text)
    if mixed:
        return mixed
    return rf"\text{{{_escape_label_text_segment(text)}}}"


def _pad_label_col(text: str, side: str, label_gap_mm: Optional[float]) -> str:
    if not label_gap_mm:
        return text
    gap = rf"\hspace{{{float(label_gap_mm)}mm}}"
    return f"{text}{gap}" if side == "left" else f"{gap}{text}"


def _total_block_sizes(
    *,
    block_heights: Sequence[int],
    block_widths: Sequence[int],
    extra_rows_above: Sequence[int],
    extra_rows_below: Sequence[int],
    extra_cols_left: Sequence[int],
    extra_cols_right: Sequence[int],
) -> Tuple[List[int], List[int]]:
    total_block_heights = [
        extra_rows_above[br] + block_heights[br] + extra_rows_below[br] for br in range(len(block_heights))
    ]
    total_block_widths = [
        extra_cols_left[bc] + block_widths[bc] + extra_cols_right[bc] for bc in range(len(block_widths))
    ]
    return total_block_heights, total_block_widths


def _rhs_column_format(
    *,
    base_width: int,
    n_rhs: Any,
    cell_align: str,
    sep: str,
    left_extra: int,
    right_extra: int,
) -> Optional[str]:
    if not n_rhs:
        return None
    if isinstance(n_rhs, (list, tuple)):
        rhs = [int(x) for x in n_rhs]
        left = base_width - sum(rhs)
        cuts: List[int] = [left]
        for cut in rhs[:-1]:
            cuts.append(cuts[-1] + cut)
        cur = 0
        fmt = cell_align * left_extra
        for cut in cuts:
            fmt += (cell_align * (cut - cur)) + sep
            cur = cut
        if cur < base_width:
            fmt += cell_align * (base_width - cur)
        return fmt + (cell_align * right_extra)
    if 0 < int(n_rhs) < base_width:
        left = base_width - int(n_rhs)
        return (
            (cell_align * left_extra)
            + (cell_align * left)
            + sep
            + (cell_align * int(n_rhs))
            + (cell_align * right_extra)
        )
    return None


def _matrix_column_format(
    *,
    block_widths: Sequence[int],
    n_rhs: Any,
    format_nrhs: bool,
    cell_align: str,
    outer_hspace_mm: int,
    extra_cols_left: Sequence[int],
    extra_cols_right: Sequence[int],
    legacy_format: bool,
) -> str:
    fmt_parts: List[str] = []
    spacer = rf"@{{\hspace{{{int(outer_hspace_mm)}mm}}}}"
    if legacy_format:
        fmt_parts.append(spacer)

    sep = "I" if legacy_format else "|"
    last_block_col = len(block_widths) - 1
    for bc, base_width in enumerate(block_widths):
        if bc > 0:
            fmt_parts.append(spacer)

        left_extra = extra_cols_left[bc]
        right_extra = extra_cols_right[bc]
        rhs_format = None
        if format_nrhs and bc == last_block_col:
            rhs_format = _rhs_column_format(
                base_width=base_width,
                n_rhs=n_rhs,
                cell_align=cell_align,
                sep=sep,
                left_extra=left_extra,
                right_extra=right_extra,
            )
        fmt_parts.append(rhs_format or (cell_align * (left_extra + base_width + right_extra)))

    return "".join(fmt_parts)


def _starts_from_sizes(sizes: Sequence[int]) -> List[int]:
    starts: List[int] = []
    acc = 1
    for size in sizes:
        starts.append(acc)
        acc += size
    return starts


def _submatrix_name(
    *,
    br: int,
    bc: int,
    n_block_cols: int,
    legacy_submatrix_names: bool,
) -> str:
    if legacy_submatrix_names:
        return f"A{br}x{bc}"
    if n_block_cols == 2:
        base = "E" if bc == 0 else "A"
    else:
        base = f"M{bc}"
    return f"{base}{br}"


def _submatrix_locations(
    *,
    n_block_rows: int,
    n_block_cols: int,
    cell_cache: Sequence[Sequence[Tuple[List[List[Any]], int, int]]],
    row_starts: Sequence[int],
    col_starts: Sequence[int],
    extra_rows_above: Sequence[int],
    extra_cols_left: Sequence[int],
    pad_top: Sequence[Sequence[int]],
    pad_left: Sequence[Sequence[int]],
    legacy_submatrix_names: bool,
) -> Tuple[List[Tuple[str, str, str]], Dict[Tuple[int, int], str]]:
    submatrix_locs: List[Tuple[str, str, str]] = []
    name_map: Dict[Tuple[int, int], str] = {}
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, height, width = cell_cache[br][bc]
            if height == 0 or width == 0:
                continue
            r0 = row_starts[br] + extra_rows_above[br] + pad_top[br][bc]
            c0 = col_starts[bc] + extra_cols_left[bc] + pad_left[br][bc]
            r1 = r0 + height - 1
            c1 = c0 + width - 1
            name = _submatrix_name(
                br=br,
                bc=bc,
                n_block_cols=n_block_cols,
                legacy_submatrix_names=legacy_submatrix_names,
            )
            submatrix_locs.append((f"name={name}", f"{r0}-{c0}", f"{r1}-{c1}"))
            name_map[(br, bc)] = name
    return submatrix_locs, name_map


def build_ge_grid_render_parts(
    *,
    grid: Sequence[Sequence[Any]],
    cell_cache: Sequence[Sequence[Tuple[List[List[Any]], int, int]]],
    block_heights: Sequence[int],
    block_widths: Sequence[int],
    n_rhs: Any,
    formatter: Callable[[Any], str],
    outer_hspace_mm: int,
    block_vspace_mm: int,
    cell_align: str,
    block_align: Optional[str],
    block_valign: Optional[str],
    format_nrhs: bool,
    label_rows: Optional[Sequence[Any]],
    label_cols: Optional[Sequence[Any]],
    label_gap_mm: Optional[float],
    variable_labels: Optional[Sequence[Any]],
    decorator_map: Optional[DecoratorMap] = None,
    strict: bool = False,
    legacy_format: bool = False,
    legacy_submatrix_names: bool = False,
    user_submatrix_locs: Optional[Sequence[Any]] = None,
) -> GEGridRenderParts:
    """Build the flattened matrix body, column format, block spans, and names."""

    n_block_rows = len(grid)
    n_block_cols = max((len(row) for row in grid), default=0)
    blank = r"\NotEmpty"
    decorator_map = decorator_map or {}

    def _fmt(value: Any) -> str:
        if value is None:
            return blank
        text = formatter(value)
        return text if (isinstance(text, str) and text.strip()) else blank

    label_rows_map, label_cols_map, _overlay_label_specs = _build_label_maps(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        label_rows=label_rows,
        label_cols=label_cols,
        variable_labels=variable_labels,
        allow_overlay=True,
        strict=strict,
    )

    pad_left: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    pad_top: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, height, width = cell_cache[br][bc]
            if height == 0 or width == 0:
                continue
            pad_left[br][bc] = _block_pad_left(block_widths[bc], width, block_align)
            pad_top[br][bc] = _block_pad_top(block_heights[br], height, block_valign)

    embedded_row_labels = _embed_row_labels(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        label_rows_map=label_rows_map,
        block_heights=list(block_heights),
        block_pad_left=pad_left,
        cell_cache=cell_cache,
    )
    embedded_col_labels = _embed_col_labels(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        label_cols_map=label_cols_map,
        block_widths=list(block_widths),
        block_pad_top=pad_top,
        cell_cache=cell_cache,
    )

    extra_rows_above, extra_rows_below, extra_cols_left, extra_cols_right = _compute_label_extras(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        label_rows_map=label_rows_map,
        label_cols_map=label_cols_map,
    )

    total_block_heights, total_block_widths = _total_block_sizes(
        block_heights=block_heights,
        block_widths=block_widths,
        extra_rows_above=extra_rows_above,
        extra_rows_below=extra_rows_below,
        extra_cols_left=extra_cols_left,
        extra_cols_right=extra_cols_right,
    )
    mat_format = _matrix_column_format(
        block_widths=block_widths,
        n_rhs=n_rhs,
        format_nrhs=format_nrhs,
        cell_align=cell_align,
        outer_hspace_mm=outer_hspace_mm,
        extra_cols_left=extra_cols_left,
        extra_cols_right=extra_cols_right,
        legacy_format=legacy_format,
    )

    lines: List[str] = []
    for br in range(n_block_rows):
        height = block_heights[br]
        total_height = total_block_heights[br]
        for i in range(total_height):
            in_matrix = extra_rows_above[br] <= i < (extra_rows_above[br] + height)
            src_i = i - extra_rows_above[br]
            above_rows = extra_rows_above[br]
            below_rows = extra_rows_below[br]
            row_cells: List[str] = []
            matrix_i_for_gap: Optional[int] = None
            for bc in range(n_block_cols):
                width = block_widths[bc]
                total_width = total_block_widths[bc]
                rows, cell_height, cell_width = cell_cache[br][bc]
                if cell_height == 0 or cell_width == 0:
                    out_cells: List[str] = [blank] * total_width
                    if in_matrix:
                        matrix_i = src_i
                        for row_idx, start_col, row_vals, target_width in embedded_row_labels.get((br, bc), []):
                            if matrix_i != row_idx:
                                continue
                            vals = list(row_vals)
                            if len(vals) < target_width:
                                vals.extend([""] * (target_width - len(vals)))
                            for j, value in enumerate(vals[:target_width]):
                                idx = start_col + j
                                if 0 <= idx < total_width:
                                    out_cells[idx] = _format_label_cell(value)
                        for col_idx, start_row, col_vals, side in embedded_col_labels.get((br, bc), []):
                            rel = matrix_i - start_row
                            if 0 <= rel < len(col_vals) and 0 <= col_idx < total_width:
                                out_cells[col_idx] = _pad_label_col(
                                    _format_label_cell(col_vals[rel]),
                                    side,
                                    label_gap_mm,
                                )
                    row_cells.extend(out_cells)
                    continue

                out_cells = [blank] * total_width
                left_cols = extra_cols_left[bc]
                matrix_start = left_cols
                matrix_end = left_cols + width
                matrix_i = src_i - pad_top[br][bc]
                matrix_i_for_gap = matrix_i

                if not in_matrix:
                    if i < above_rows:
                        rows_above = label_rows_map.get((br, bc, "above"), [])
                        if rows_above:
                            start_row = above_rows - len(rows_above)
                            label_idx = i - start_row
                            if 0 <= label_idx < len(rows_above):
                                row_vals = list(rows_above[label_idx])
                                if len(row_vals) < width:
                                    row_vals.extend([""] * (width - len(row_vals)))
                                for j, value in enumerate(row_vals[:width]):
                                    out_cells[matrix_start + pad_left[br][bc] + j] = _format_label_cell(value)
                    else:
                        rows_below = label_rows_map.get((br, bc, "below"), [])
                        if rows_below:
                            label_idx = i - (above_rows + height)
                            if 0 <= label_idx < len(rows_below):
                                row_vals = list(rows_below[label_idx])
                                if len(row_vals) < width:
                                    row_vals.extend([""] * (width - len(row_vals)))
                                for j, value in enumerate(row_vals[:width]):
                                    out_cells[matrix_start + pad_left[br][bc] + j] = _format_label_cell(value)
                    row_cells.extend(out_cells)
                    continue

                if matrix_i < 0 or matrix_i >= cell_height:
                    row_cells.extend(out_cells)
                    continue

                src = list(rows[matrix_i]) if matrix_i < len(rows) else []
                if len(src) < cell_width:
                    src.extend([None] * (cell_width - len(src)))

                cols_left = label_cols_map.get((br, bc, "left"), [])
                if cols_left:
                    start_col = max(left_cols - len(cols_left), 0)
                    for col_j, col_vals in enumerate(cols_left):
                        if matrix_i < len(col_vals):
                            out_cells[start_col + col_j] = _pad_label_col(
                                _format_label_cell(col_vals[matrix_i]),
                                "left",
                                label_gap_mm,
                            )
                cols_right = label_cols_map.get((br, bc, "right"), [])
                if cols_right:
                    start_col = matrix_end
                    for col_j, col_vals in enumerate(cols_right):
                        if matrix_i < len(col_vals) and start_col + col_j < total_width:
                            out_cells[start_col + col_j] = _pad_label_col(
                                _format_label_cell(col_vals[matrix_i]),
                                "right",
                                label_gap_mm,
                            )

                dec_specs = decorator_map.get((br, bc), [])
                for j, value in enumerate(src[:cell_width]):
                    if not dec_specs:
                        out_cells[matrix_start + pad_left[br][bc] + j] = _fmt(value)
                        continue
                    cell_tex = _fmt(value)
                    for decorator, selected, entry_formatter in dec_specs:
                        if (matrix_i, j) in selected and value is not None:
                            base = entry_formatter(value)
                            if not (isinstance(base, str) and base.strip()):
                                base = blank
                            cell_tex = apply_decorator(decorator, matrix_i, j, value, base)
                    out_cells[matrix_start + pad_left[br][bc] + j] = cell_tex
                row_cells.extend(out_cells)
            line = " & ".join(row_cells) + r" \\"
            if not in_matrix and above_rows and i == above_rows - 1 and label_gap_mm:
                line += rf"\noalign{{\vskip{float(label_gap_mm)}mm}}"
            if in_matrix and matrix_i_for_gap == height - 1 and below_rows and label_gap_mm:
                line += rf"\noalign{{\vskip{float(label_gap_mm)}mm}}"
            lines.append(line)
        if block_vspace_mm and br < n_block_rows - 1:
            lines[-1] += rf"\noalign{{\vskip{int(block_vspace_mm)}mm}}"

    row_starts = _starts_from_sizes(total_block_heights)
    col_starts = _starts_from_sizes(total_block_widths)
    submatrix_locs, name_map = _submatrix_locations(
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        cell_cache=cell_cache,
        row_starts=row_starts,
        col_starts=col_starts,
        extra_rows_above=extra_rows_above,
        extra_cols_left=extra_cols_left,
        pad_top=pad_top,
        pad_left=pad_left,
        legacy_submatrix_names=legacy_submatrix_names,
    )

    if user_submatrix_locs:
        submatrix_locs.extend(list(user_submatrix_locs))

    return GEGridRenderParts(
        mat_rep="\n".join(lines),
        mat_format=mat_format,
        submatrix_locs=submatrix_locs,
        name_map=name_map,
    )
