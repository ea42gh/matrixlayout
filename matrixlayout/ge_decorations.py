"""GE decoration parsing helpers."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .formatting import expand_entry_selectors, make_decorator


As2DList = Callable[[Any], Tuple[List[List[Any]], int, int]]
GridLineSpecs = Callable[..., List[Tuple[str, str, str]]]
GridHighlightSpecs = Callable[..., List[str]]
GridSubmatrixSpans = Callable[..., Sequence[Any]]


def normalize_index_list(val: Any, max_len: int) -> List[int]:
    if max_len <= 0:
        return []
    if val is None:
        return list(range(max_len))
    if isinstance(val, slice):
        start = 0 if val.start is None else int(val.start)
        stop = max_len if val.stop is None else int(val.stop)
        return [i for i in range(start, min(stop, max_len)) if i >= 0]
    if isinstance(val, str):
        txt = val.strip()
        if ":" in txt:
            left, right = txt.split(":", 1)
            start = int(left) if left.strip() else 0
            end = int(right) if right.strip() else (max_len - 1)
            lo, hi = (start, end) if start <= end else (end, start)
            return list(range(max(0, lo), min(max_len - 1, hi) + 1))
    if isinstance(val, (tuple, list)) and len(val) == 2 and all(isinstance(x, int) for x in val):
        a, b = int(val[0]), int(val[1])
        lo, hi = (a, b) if a <= b else (b, a)
        return list(range(max(0, lo), min(max_len - 1, hi) + 1))
    if isinstance(val, (list, tuple, set)):
        return sorted({int(x) for x in val if 0 <= int(x) < max_len})
    if isinstance(val, int):
        return [val] if 0 <= val < max_len else []
    raise ValueError("rows/cols must be None, a range, a list, or a slice")


def normalize_range(val: Any, max_len: int) -> Tuple[int, int]:
    idx = normalize_index_list(val, max_len)
    if not idx:
        return (1, 0)
    return (min(idx), max(idx))


def parse_ge_decorations(
    matrices: Sequence[Sequence[Any]],
    decorations: Sequence[Any],
    *,
    as_2d_list: As2DList,
    grid_line_specs: GridLineSpecs,
    grid_highlight_specs: GridHighlightSpecs,
    grid_submatrix_spans: GridSubmatrixSpans,
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]], List[Dict[str, Any]], List[str]]:
    dec_specs: List[Dict[str, Any]] = []
    sub_locs: List[Tuple[str, str, str]] = []
    callouts: List[Dict[str, Any]] = []
    highlights: List[Dict[str, Any]] = []
    outlines: List[Dict[str, Any]] = []

    for item in decorations or []:
        if not isinstance(item, dict):
            raise ValueError("decorations must be dict specs")
        grid = item.get("grid")
        if grid is None:
            if len(matrices) == 1 and len(matrices[0]) == 1:
                key = (0, 0)
            else:
                raise ValueError("decorations require grid=(row,col)")
        else:
            if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
                raise ValueError("decorations require grid=(row,col)")
            key = (int(grid[0]), int(grid[1]))

        if "label" in item:
            callout: Dict[str, Any] = {"grid_pos": key, "label": str(item["label"])}
            for src, dst in [
                ("side", "side"),
                ("anchor", "anchor"),
                ("angle", "angle_deg"),
                ("angle_deg", "angle_deg"),
                ("length", "length_mm"),
                ("length_mm", "length_mm"),
                ("color", "color"),
                ("line_width_pt", "line_width_pt"),
                ("tip", "tip"),
                ("label_shift_y_mm", "label_shift_y_mm"),
                ("label_shift_x_mm", "label_shift_x_mm"),
            ]:
                if src in item:
                    callout[dst] = item[src]
            callouts.append(callout)
            continue

        if "hlines" in item or "vlines" in item:
            mat = matrices[key[0]][key[1]]
            _, h, w = as_2d_list(mat)
            rows = item.get("rows")
            cols = item.get("cols")
            if "submatrix" in item and item["submatrix"] is not None:
                sub = item["submatrix"]
                if isinstance(sub, (tuple, list)) and len(sub) == 2:
                    rows = sub[0]
                    cols = sub[1]

            def _coerce_line(val: Any, axis_len: int, sel: Any) -> Any:
                if val is True or (isinstance(val, str) and val.strip().lower() == "submatrix"):
                    idx = normalize_index_list(sel, axis_len)
                    if not idx:
                        return None
                    return max(idx) + 1
                if isinstance(val, str) and val.strip().lower() == "bounds":
                    idx = normalize_index_list(sel, axis_len)
                    if not idx:
                        return None
                    lo = min(idx)
                    hi = max(idx)
                    max_line = axis_len - 1
                    if max_line <= 0:
                        return None
                    lines = set()
                    if lo > 0:
                        lines.add(lo)
                    if hi < axis_len - 1:
                        lines.add(hi + 1)
                    if not lines:
                        return None
                    out = sorted(lines)
                    return out[0] if len(out) == 1 else out
                if isinstance(val, str) and val.strip().lower() == "all":
                    idx = normalize_index_list(sel, axis_len)
                    if not idx:
                        return None
                    lo = min(idx)
                    hi = max(idx)
                    return list(range(lo + 1, hi + 1))
                return val

            hlines = _coerce_line(item.get("hlines"), h, rows)
            vlines = _coerce_line(item.get("vlines"), w, cols)
            sub_locs.extend(
                grid_line_specs(
                    matrices,
                    targets=[key],
                    hlines=hlines,
                    vlines=vlines,
                    block_align=block_align,
                    block_valign=block_valign,
                )
            )
            continue

        if item.get("outline"):
            outline_spec: Dict[str, Any] = {"grid": key}
            for field in ("line_width_pt", "padding_pt", "color", "rows", "cols"):
                if field in item:
                    outline_spec[field] = item[field]
            if "submatrix" in item and item["submatrix"] is not None:
                sub = item["submatrix"]
                if isinstance(sub, (tuple, list)) and len(sub) == 2:
                    outline_spec["rows"] = sub[0]
                    outline_spec["cols"] = sub[1]
            outlines.append(outline_spec)
            continue

        if "background" in item:
            highlight_spec: Dict[str, Any] = {"grid": key}
            if item.get("background") is not None:
                highlight_spec["color"] = item.get("background")
            if "padding_pt" in item:
                highlight_spec["padding_pt"] = item["padding_pt"]
            if "entries" in item:
                mat = matrices[key[0]][key[1]]
                _, h, w = as_2d_list(mat)
                for r, c in expand_entry_selectors(item.get("entries"), h, w, filter_bounds=True):
                    entry_spec = dict(highlight_spec)
                    entry_spec["rows"] = (r, r)
                    entry_spec["cols"] = (c, c)
                    highlights.append(entry_spec)
                continue
            if "submatrix" in item and item["submatrix"] is not None:
                sub = item["submatrix"]
                if isinstance(sub, (tuple, list)) and len(sub) == 2:
                    highlight_spec["rows"] = sub[0]
                    highlight_spec["cols"] = sub[1]
            if "rows" in item:
                highlight_spec["rows"] = item["rows"]
            if "cols" in item:
                highlight_spec["cols"] = item["cols"]
            highlights.append(highlight_spec)
            continue

        if "decorator" in item:
            decorator = item["decorator"]
            if not callable(decorator):
                raise ValueError("decorations decorator must be callable")
            entries = item.get("entries")
            if entries is None:
                mat = matrices[key[0]][key[1]]
                _, h, w = as_2d_list(mat)
                rows = item.get("rows")
                cols = item.get("cols")
                if "submatrix" in item and item["submatrix"] is not None:
                    sub = item["submatrix"]
                    if isinstance(sub, (tuple, list)) and len(sub) == 2:
                        rows = sub[0]
                        cols = sub[1]
                row_idx = normalize_index_list(rows, h)
                col_idx = normalize_index_list(cols, w)
                entries = [(r, c) for r in row_idx for c in col_idx]
            dec_specs.append({"grid": key, "entries": entries, "decorator": decorator})
            continue

        boxed = False
        box_color: Optional[str] = None
        text_color: Optional[str] = None
        bf = False
        if "box" in item:
            box = item["box"]
            if box is True:
                boxed = True
            elif isinstance(box, str):
                box_color = str(box)
        if "color" in item:
            text_color = str(item["color"])
        if item.get("bold"):
            bf = True
        if not (boxed or box_color or text_color or bf):
            continue
        decorator = make_decorator(boxed=boxed, box_color=box_color, text_color=text_color or "black", bf=bf)

        entries = item.get("entries")
        if entries is None:
            mat = matrices[key[0]][key[1]]
            _, h, w = as_2d_list(mat)
            rows = item.get("rows")
            cols = item.get("cols")
            if "submatrix" in item and item["submatrix"] is not None:
                sub = item["submatrix"]
                if isinstance(sub, (tuple, list)) and len(sub) == 2:
                    rows = sub[0]
                    cols = sub[1]
            row_idx = normalize_index_list(rows, h)
            col_idx = normalize_index_list(cols, w)
            entries = [(r, c) for r in row_idx for c in col_idx]
        dec_specs.append({"grid": key, "entries": entries, "decorator": decorator})

    codebefore = grid_highlight_specs(
        matrices,
        blocks=highlights,
        block_align=block_align,
        block_valign=block_valign,
    )
    if outlines:
        spans = grid_submatrix_spans(
            matrices,
            block_align=block_align,
            block_valign=block_valign,
        )
        span_map = {(s.block_row, s.block_col): s for s in spans}
        for spec in outlines:
            grid = spec.get("grid")
            if not (isinstance(grid, (tuple, list)) and len(grid) == 2):
                continue
            key = (int(grid[0]), int(grid[1]))
            if key not in span_map:
                continue
            mat = matrices[key[0]][key[1]]
            _, h, w = as_2d_list(mat)
            if h == 0 or w == 0:
                continue
            r0, r1 = normalize_range(spec.get("rows"), h)
            c0, c1 = normalize_range(spec.get("cols"), w)
            if r1 < r0 or c1 < c0:
                continue
            span = span_map[key]
            row_start = span.row_start + r0
            row_end = span.row_start + r1
            col_start = span.col_start + c0
            col_end = span.col_start + c1
            color = str(spec.get("color", "black"))
            width = float(spec.get("line_width_pt", 0.4))
            pad = float(spec.get("padding_pt", 0.0))
            codebefore.append(
                rf"\tikz \node [draw={color}, line width={width}pt, inner sep={pad}pt, fit=({row_start}-{col_start}-medium) ({row_end}-{col_end}-medium)] {{}};"
            )
    return dec_specs, sub_locs, callouts, codebefore
