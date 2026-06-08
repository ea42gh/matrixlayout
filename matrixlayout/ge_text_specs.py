"""GE text-placement helpers for labels around matrix blocks."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .formatting import _normalize_unicode_tex
from .ge_grid_specs import grid_submatrix_spans
from .ge_labels import escape_label_text_segment, split_label_dollar_segments


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
    mixed = split_label_dollar_segments(s)
    if mixed:
        return f"${mixed}$"
    return escape_label_text_segment(s)


def render_ge_tex_specs(
    matrices: Sequence[Sequence[Any]],
    annotations: Sequence[Mapping[str, Any]],
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
    strict: bool = False,
) -> List[Tuple[str, str, str]]:
    """Return text placements around matrix blocks.

    Each annotation supports:
      - grid: (block_row, block_col)
      - side: right/left/above/below
      - labels: list of strings (rows for left/right; cols for above/below)
      - offset_mm: numeric offset (xshift for left/right; yshift for above/below)
      - style: extra TikZ node style (e.g. "text=blue,align=left")
    """

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
    span_map = {(s.block_row, s.block_col): s for s in spans}
    out: List[Tuple[str, str, str]] = []
    label_rows_count: Dict[Tuple[int, int, str], int] = {}

    for spec_item in label_rows or []:
        if not isinstance(spec_item, MappingABC):
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
        count = _count_label_blocks(spec_item.get("labels"))
        if count:
            label_rows_count[(gM, gN, side)] = label_rows_count.get((gM, gN, side), 0) + count

    for item in annotations:
        if not isinstance(item, MappingABC):
            if strict:
                raise ValueError("render_ge_tex_specs annotations must be mappings")
            continue
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            if strict:
                raise ValueError("render_ge_tex_specs annotations require grid=(row, col)")
            continue
        key = (int(grid[0]), int(grid[1]))
        span = span_map.get(key)
        if span is None:
            if strict:
                raise ValueError(f"render_ge_tex_specs annotation grid {key} is outside the matrix grid")
            continue
        yshift_mm = float(item.get("yshift_mm", item.get("row_offset", 0)) or 0)
        xshift_mm = float(item.get("xshift_mm", item.get("col_offset", 0)) or 0)
        labels_raw = item.get("labels") or []
        labels = list(labels_raw) if isinstance(labels_raw, (list, tuple)) else [labels_raw]
        side = str(item.get("side", "right")).strip().lower()
        if strict and side not in {"right", "left", "above", "below"}:
            raise ValueError("render_ge_tex_specs annotation side must be right/left/above/below")
        offset_raw = item.get("offset_mm")
        if offset_raw is None and "label_gap_mm" in item:
            offset_raw = item.get("label_gap_mm")
        if offset_raw is None:
            offset_raw = 0.0
        offset = float(offset_raw) if offset_raw is not None else 0.0
        style = str(item.get("style", "")).strip()

        if side in ("right", "left"):
            edge = "center"
            col = span.col_end if side == "right" else max(span.col_start - 1, 1)
            line_gap = float(item.get("line_gap_mm", 3.5))
            base_shift = offset
            default_xshift = base_shift + xshift_mm
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
