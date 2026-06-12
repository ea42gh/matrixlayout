"""GE label normalization, merging, and placement helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

LabelMap = Dict[Tuple[int, int, str], List[List[Any]]]
CellCache = Sequence[Sequence[Tuple[List[List[Any]], int, int]]]


def _coerce_label_text_for_layout(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("text", ""))
    if isinstance(val, (tuple, list)) and len(val) >= 2:
        return str(val[1])
    return str(val)


_LABEL_TEXT_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
}


def escape_label_text_segment(s: str) -> str:
    """Escape ordinary text that will be placed in TeX label content."""
    return "".join(_LABEL_TEXT_ESCAPES.get(ch, ch) for ch in s)


def split_label_dollar_segments(s: str) -> Optional[str]:
    parts = s.split("$")
    if len(parts) < 3 or len(parts) % 2 == 0:
        return None
    expr_parts: List[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            if part:
                expr_parts.append(rf"\text{{{escape_label_text_segment(part)}}}")
        else:
            expr_parts.append(part)
    return "".join(expr_parts)


def _normalize_label_entries(val: Any) -> List[List[str]]:
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        if val and isinstance(val[0], (list, tuple)):
            return [[_coerce_label_text_for_layout(x) for x in row] for row in val]
        return [[_coerce_label_text_for_layout(x) for x in val]]
    return [[_coerce_label_text_for_layout(val)]]


def grid_label_layouts(
    annotations: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    r"""Convert label annotations into ``label_rows``/``label_cols`` specs."""
    label_rows: List[Dict[str, Any]] = []
    label_cols: List[Dict[str, Any]] = []
    for item in annotations:
        if not isinstance(item, Mapping):
            continue
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            continue
        gM, gN = int(grid[0]), int(grid[1])
        side = str(item.get("side", "right")).strip().lower()
        labels = _normalize_label_entries(item.get("labels") or [])
        if not labels:
            continue
        if side in ("left", "right"):
            label_cols.append({"grid": (gM, gN), "side": side, "labels": labels})
        elif side in ("above", "below"):
            label_rows.append({"grid": (gM, gN), "side": side, "labels": labels})
    return label_rows, label_cols


def annotation_label_specs(
    specs: Optional[Sequence[Mapping[str, Any]]]
) -> List[Dict[str, Any]]:
    """Extract label-row/column specs from generic annotations."""
    if not specs:
        return []
    label_specs: List[Dict[str, Any]] = []
    for item in specs:
        if not isinstance(item, Mapping):
            continue
        grid = item.get("grid")
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
            continue
        side = str(item.get("side", "right")).strip().lower()
        if side not in {"left", "right", "above", "below"}:
            continue
        label_values = item.get("labels")
        if label_values is None:
            continue
        target: Dict[str, Any] = {
            key: value
            for key, value in item.items()
            if key != "labels"
        }
        target["grid"] = (int(grid[0]), int(grid[1]))
        target["side"] = side
        target["labels"] = label_values
        label_specs.append(target)
    return label_specs


def blank_label_specs(
    specs: Sequence[Dict[str, Any]],
    key: str,
) -> List[Dict[str, Any]]:
    """Return copies of ``specs`` with their ``key`` entries replaced by blanks."""
    out: List[Dict[str, Any]] = []
    for item in specs:
        new_item = dict(item)
        values = item.get(key)
        if isinstance(values, list):
            blank_values: List[List[Any]] = []
            for row in values:
                if isinstance(row, (list, tuple)):
                    blank_values.append([{"text": r"\NotEmpty"} for _ in row])
                else:
                    blank_values.append([{"text": r"\NotEmpty"}])
            new_item[key] = blank_values
        out.append(new_item)
    return out


def _normalize_label_rows_for_merge(val: Any) -> List[List[Any]]:
    if val is None:
        return []
    if isinstance(val, (list, tuple)) and val and all(not isinstance(v, (list, tuple)) for v in val):
        return [list(val)]
    if isinstance(val, (list, tuple)):
        out: List[List[Any]] = []
        for row in val:
            if isinstance(row, (list, tuple)):
                out.append(list(row))
            else:
                out.append([row])
        return out
    return [[val]]


def _normalize_label_cols_for_merge(val: Any) -> List[List[Any]]:
    if val is None:
        return []
    if isinstance(val, (list, tuple)) and val and all(not isinstance(v, (list, tuple)) for v in val):
        return [list(val)]
    if isinstance(val, (list, tuple)):
        out: List[List[Any]] = []
        for col in val:
            if isinstance(col, (list, tuple)):
                out.append(list(col))
            else:
                out.append([col])
        return out
    return [[val]]


def _norm_side(side: Any) -> str:
    txt = str(side or "").strip().lower()
    if txt == "top":
        return "above"
    if txt == "bottom":
        return "below"
    return txt


def _is_blank_label(items: Sequence[Any]) -> bool:
    for item in items:
        if isinstance(item, dict):
            txt = str(item.get("text", "")).strip()
        else:
            txt = str(item or "").strip()
        if txt and txt != r"\NotEmpty":
            return False
    return True


def merge_label_specs(
    *,
    annotations: Sequence[Mapping[str, Any]],
    label_rows: Optional[Sequence[Any]],
    label_cols: Optional[Sequence[Any]],
    decorations: Optional[Sequence[Any]],
) -> Tuple[Optional[List[Any]], Optional[List[Any]], Optional[List[Any]]]:
    """Merge annotation labels into explicit label rows/cols."""
    if not annotations:
        return list(label_rows or []) or None, list(label_cols or []) or None, list(decorations or []) or None

    def _collect_items(val: Any) -> List[Mapping[str, Any]]:
        if not val:
            return []
        if isinstance(val, Mapping):
            return [val]
        return [item for item in val if isinstance(item, Mapping)]

    label_specs = annotation_label_specs(annotations)
    if not label_specs:
        return list(label_rows or []) or None, list(label_cols or []) or None, list(decorations or []) or None

    label_rows_from_annotations, label_cols_from_annotations = grid_label_layouts(label_specs)

    if label_rows_from_annotations:
        existing_rows = list(label_rows or [])
        for spec_item in label_rows_from_annotations:
            grid = spec_item.get("grid")
            if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
                continue
            side = _norm_side(spec_item.get("side"))
            rows = _normalize_label_rows_for_merge(spec_item.get("labels"))
            if not rows:
                continue
            matched = False
            for existing in existing_rows:
                if not isinstance(existing, dict):
                    continue
                if tuple(existing.get("grid", ())) != tuple(grid):
                    continue
                if _norm_side(existing.get("side")) != side:
                    continue
                ex_rows = _normalize_label_rows_for_merge(existing.get("labels"))
                if not ex_rows:
                    existing["labels"] = rows
                    matched = True
                    break
                blank_idxs = [idx for idx, row in enumerate(ex_rows) if _is_blank_label(row)]
                if blank_idxs:
                    for i, row in enumerate(rows):
                        if i >= len(blank_idxs):
                            break
                        ex_rows[blank_idxs[i]] = row
                    if len(rows) > len(blank_idxs):
                        ex_rows.extend(rows[len(blank_idxs):])
                    existing["labels"] = ex_rows
                    matched = True
                    break
                ex_rows.extend(rows)
                existing["labels"] = ex_rows
                matched = True
                break
            if not matched:
                existing_rows.append(dict(spec_item))
        label_rows = existing_rows

    if label_cols_from_annotations:
        existing_cols = list(label_cols or [])
        for spec_item in label_cols_from_annotations:
            grid = spec_item.get("grid")
            if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
                continue
            side = _norm_side(spec_item.get("side"))
            cols = _normalize_label_cols_for_merge(spec_item.get("labels"))
            if not cols:
                continue
            matched = False
            for existing in existing_cols:
                if not isinstance(existing, dict):
                    continue
                if tuple(existing.get("grid", ())) != tuple(grid):
                    continue
                if _norm_side(existing.get("side")) != side:
                    continue
                ex_cols = _normalize_label_cols_for_merge(existing.get("labels"))
                if not ex_cols:
                    existing["labels"] = cols
                    matched = True
                    break
                blank_idxs = [idx for idx, col in enumerate(ex_cols) if _is_blank_label(col)]
                if blank_idxs:
                    for i, col in enumerate(cols):
                        if i >= len(blank_idxs):
                            break
                        ex_cols[blank_idxs[i]] = col
                    if len(cols) > len(blank_idxs):
                        ex_cols.extend(cols[len(blank_idxs):])
                    existing["labels"] = ex_cols
                    matched = True
                    break
                ex_cols.extend(cols)
                existing["labels"] = ex_cols
                matched = True
                break
            if not matched:
                existing_cols.append(dict(spec_item))
        label_cols = existing_cols

    return list(label_rows or []) or None, list(label_cols or []) or None, list(decorations or []) or None


def normalize_label_rows(val: Any) -> List[List[Any]]:
    """Normalize label row input into a list of row lists."""
    if val is None:
        return []
    if isinstance(val, (list, tuple)) and val and all(not isinstance(v, (list, tuple)) for v in val):
        return [list(val)]
    if isinstance(val, (list, tuple)):
        out: List[List[Any]] = []
        for row in val:
            if isinstance(row, (list, tuple)):
                out.append(list(row))
            else:
                out.append([row])
        return out
    return [[val]]


def normalize_label_cols(val: Any) -> List[List[Any]]:
    """Normalize label column input into a list of column lists."""
    if val is None:
        return []
    if isinstance(val, (list, tuple)) and val and all(not isinstance(v, (list, tuple)) for v in val):
        return [list(val)]
    if isinstance(val, (list, tuple)):
        if val and all(isinstance(col, (list, tuple)) and len(col) == 1 for col in val):
            return [[col[0] for col in val]]
        out: List[List[Any]] = []
        for col in val:
            if isinstance(col, (list, tuple)):
                out.append(list(col))
            else:
                out.append([col])
        return out
    return [[val]]


def _single_block_default_grid(
    grid: Any,
    *,
    n_block_rows: int,
    n_block_cols: int,
) -> Any:
    if grid is None and n_block_rows == 1 and n_block_cols == 1:
        return (0, 0)
    return grid


def _label_grid_key(
    spec_item: Mapping[str, Any],
    *,
    field: str,
    n_block_rows: int,
    n_block_cols: int,
    strict: bool,
) -> Optional[Tuple[int, int]]:
    grid = _single_block_default_grid(
        spec_item.get("grid"),
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
    )
    if not (isinstance(grid, (list, tuple)) and len(grid) == 2):
        if strict:
            raise ValueError(f"{field} grid must be a (row,col) pair")
        return None
    gM, gN = int(grid[0]), int(grid[1])
    if gM < 0 or gN < 0 or gM >= n_block_rows or gN >= n_block_cols:
        if strict:
            raise ValueError(f"{field} grid position out of range")
        return None
    return (gM, gN)


def _label_side(
    spec_item: Mapping[str, Any],
    *,
    field: str,
    default: str,
    allowed: Tuple[str, str],
    strict: bool,
) -> Optional[str]:
    side = str(spec_item.get("side", default)).strip().lower()
    if side not in allowed:
        if strict:
            joined = " or ".join(repr(item) for item in allowed)
            raise ValueError(f"{field} side must be {joined}")
        return None
    return side


def _is_empty_block(cell_cache: CellCache, br: int, bc: int) -> bool:
    _, h, w = cell_cache[br][bc]
    return h == 0 or w == 0


def build_label_maps(
    *,
    n_block_rows: int,
    n_block_cols: int,
    label_rows: Optional[Sequence[Any]],
    label_cols: Optional[Sequence[Any]],
    allow_overlay: bool = False,
    strict: bool = False,
) -> Tuple[LabelMap, LabelMap, List[Dict[str, Any]]]:
    """Build label-row/label-col maps and collect overlay label specs."""
    label_rows_map: LabelMap = {}
    label_cols_map: LabelMap = {}
    overlay_label_specs: List[Dict[str, Any]] = []

    for spec_item in label_rows or []:
        if not isinstance(spec_item, Mapping):
            if strict:
                raise ValueError("label_rows entries must be dict specs")
            continue
        grid_key = _label_grid_key(
            spec_item,
            field="label_rows",
            n_block_rows=n_block_rows,
            n_block_cols=n_block_cols,
            strict=strict,
        )
        if grid_key is None:
            continue
        side = _label_side(
            spec_item,
            field="label_rows",
            default="above",
            allowed=("above", "below"),
            strict=strict,
        )
        if side is None:
            continue
        rows = normalize_label_rows(spec_item.get("labels"))
        if not rows:
            continue
        gM, gN = grid_key
        label_rows_map[(gM, gN, side)] = label_rows_map.get((gM, gN, side), []) + rows

    for spec_item in label_cols or []:
        if not isinstance(spec_item, Mapping):
            if strict:
                raise ValueError("label_cols entries must be dict specs")
            continue
        grid_key = _label_grid_key(
            spec_item,
            field="label_cols",
            n_block_rows=n_block_rows,
            n_block_cols=n_block_cols,
            strict=strict,
        )
        if grid_key is None:
            continue
        side = _label_side(
            spec_item,
            field="label_cols",
            default="left",
            allowed=("left", "right"),
            strict=strict,
        )
        if side is None:
            continue
        if allow_overlay and spec_item.get("overlay"):
            overlay_label_specs.append(dict(spec_item))
            continue
        cols = normalize_label_cols(spec_item.get("labels"))
        if not cols:
            continue
        gM, gN = grid_key
        label_cols_map[(gM, gN, side)] = label_cols_map.get((gM, gN, side), []) + cols

    return label_rows_map, label_cols_map, overlay_label_specs


def compute_label_extras(
    *,
    n_block_rows: int,
    n_block_cols: int,
    label_rows_map: LabelMap,
    label_cols_map: LabelMap,
) -> Tuple[List[int], List[int], List[int], List[int]]:
    """Compute extra row/column counts needed for label padding."""
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

    return extra_rows_above, extra_rows_below, extra_cols_left, extra_cols_right


def embed_row_labels(
    *,
    n_block_rows: int,
    n_block_cols: int,
    label_rows_map: LabelMap,
    block_heights: Sequence[int],
    block_pad_left: Sequence[Sequence[int]],
    cell_cache: CellCache,
) -> Dict[Tuple[int, int], List[Tuple[int, int, List[Any], int]]]:
    """Embed label rows into empty blocks above/below target blocks."""
    embedded_row_labels: Dict[Tuple[int, int], List[Tuple[int, int, List[Any], int]]] = {}

    def _row_label_target_width(gM: int, gN: int) -> int:
        return cell_cache[gM][gN][2]

    for (gM, gN, side), rows in list(label_rows_map.items()):
        if not rows:
            continue
        remaining = list(rows)
        pad_left = block_pad_left[gM][gN]
        tgt_w = _row_label_target_width(gM, gN)
        if side == "above":
            idx = len(remaining) - 1
            for br in range(gM - 1, -1, -1):
                if not _is_empty_block(cell_cache, br, gN):
                    continue
                H = block_heights[br]
                for offset in range(H - 1, -1, -1):
                    if idx < 0:
                        break
                    row_vals = remaining[idx]
                    embedded_row_labels.setdefault((br, gN), []).append((offset, pad_left, row_vals, tgt_w))
                    idx -= 1
                if idx < 0:
                    break
            remaining = remaining[: idx + 1]
        elif side == "below":
            idx = 0
            for br in range(gM + 1, n_block_rows):
                if not _is_empty_block(cell_cache, br, gN):
                    continue
                H = block_heights[br]
                for offset in range(0, H):
                    if idx >= len(remaining):
                        break
                    row_vals = remaining[idx]
                    embedded_row_labels.setdefault((br, gN), []).append((offset, pad_left, row_vals, tgt_w))
                    idx += 1
                if idx >= len(remaining):
                    break
            remaining = remaining[idx:]

        if remaining:
            label_rows_map[(gM, gN, side)] = remaining
        else:
            label_rows_map.pop((gM, gN, side), None)

    return embedded_row_labels


def embed_col_labels(
    *,
    n_block_rows: int,
    n_block_cols: int,
    label_cols_map: LabelMap,
    block_widths: Sequence[int],
    block_pad_top: Sequence[Sequence[int]],
    cell_cache: CellCache,
) -> Dict[Tuple[int, int], List[Tuple[int, int, List[Any], str]]]:
    """Embed label columns into empty blocks left/right of target blocks."""
    embedded_col_labels: Dict[Tuple[int, int], List[Tuple[int, int, List[Any], str]]] = {}

    def _col_label_target_height(gM: int, gN: int) -> int:
        return cell_cache[gM][gN][1]

    col_counts: Dict[Tuple[int, str], Dict[int, int]] = {}
    for (gM, gN, side), cols in label_cols_map.items():
        col_counts.setdefault((gN, side), {})[gM] = len(cols)

    for (gM, gN, side), cols in list(label_cols_map.items()):
        if not cols:
            continue
        remaining = list(cols)
        other_rows = col_counts.get((gN, side), {})
        other_max = max((count for br, count in other_rows.items() if br != gM), default=0) if other_rows else 0
        if other_max > 0:
            keep = list(remaining)
            embed_queue = []
        else:
            keep = []
            embed_queue = remaining
        pad_top = block_pad_top[gM][gN]
        tgt_h = _col_label_target_height(gM, gN)
        if side == "left":
            idx = len(embed_queue) - 1
            for bc in range(gN - 1, -1, -1):
                if not _is_empty_block(cell_cache, gM, bc):
                    continue
                W = block_widths[bc]
                for offset in range(W - 1, -1, -1):
                    if idx < 0:
                        break
                    col_vals = embed_queue[idx]
                    embedded_col_labels.setdefault((gM, bc), []).append((offset, pad_top, col_vals[:tgt_h], side))
                    idx -= 1
                if idx < 0:
                    break
            leftover = embed_queue[: idx + 1]
            remaining = leftover + keep
        elif side == "right":
            idx = 0
            for bc in range(gN + 1, n_block_cols):
                if not _is_empty_block(cell_cache, gM, bc):
                    continue
                W = block_widths[bc]
                for offset in range(0, W):
                    if idx >= len(embed_queue):
                        break
                    col_vals = embed_queue[idx]
                    embedded_col_labels.setdefault((gM, bc), []).append((offset, pad_top, col_vals[:tgt_h], side))
                    idx += 1
                if idx >= len(embed_queue):
                    break
            leftover = embed_queue[idx:]
            remaining = keep + leftover
        if remaining:
            label_cols_map[(gM, gN, side)] = remaining
        else:
            label_cols_map.pop((gM, gN, side), None)

    return embedded_col_labels
