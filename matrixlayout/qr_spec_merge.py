"""QR spec coercion, labels, and default decoration helpers."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .specs import QRGridSpec

MatrixShape = Callable[[Any], Tuple[int, int]]


def merge_scalar(field: str, explicit: Any, spec_val: Any) -> Any:
    if spec_val is None:
        return explicit
    if explicit is None:
        return spec_val
    if explicit != spec_val:
        raise ValueError(f"Conflicting values for {field}: explicit={explicit!r} spec={spec_val!r}")
    return explicit


def merge_scalar_default(field: str, explicit: Any, spec_val: Any, default: Any) -> Any:
    """Merge a QR spec field, treating renderer defaults as unset."""
    if spec_val is None:
        return explicit
    if spec_val == default:
        return explicit
    if explicit is None or explicit == default:
        return spec_val
    if explicit != spec_val:
        raise ValueError(f"Conflicting values for {field}: explicit={explicit!r} spec={spec_val!r}")
    return explicit


def coerce_qr_spec(spec: Optional[Union[Dict[str, Any], QRGridSpec]]) -> Optional[QRGridSpec]:
    if spec is None:
        return None
    if isinstance(spec, QRGridSpec):
        return spec
    return QRGridSpec.from_dict(spec)


def qr_known_zero_entries(
    matrices: Sequence[Sequence[Any]],
    *,
    mat_shape: MatrixShape,
) -> List[Tuple[Tuple[int, int], List[Tuple[int, int]]]]:
    if not matrices or len(matrices) < 2:
        return []
    try:
        wta = matrices[1][2]
        wtw = matrices[1][3]
    except Exception:
        return []

    m_wta = mat_shape(wta)[0]
    m_wtw = mat_shape(wtw)[0]
    if m_wta <= 0 or m_wtw <= 0:
        return []

    entries_wta = [(i, j) for i in range(m_wta) for j in range(m_wta) if i > j]
    entries_wtw = [(i, j) for i in range(m_wtw) for j in range(m_wtw) if i != j]
    return [((1, 2), entries_wta), ((1, 3), entries_wtw)]


def qr_default_name_specs() -> List[Any]:
    return [
        [(0, 2), "al", r"\mathbf{A}"],
        [(0, 3), "ar", r"\mathbf{W}"],
        [(1, 1), "al", r"\mathbf{W^T}"],
        [(1, 2), "al", r"\mathbf{W^T A}"],
        [(1, 3), "ar", r"\mathbf{W^T W}"],
        [(2, 0), "al", r"\mathbf{S = \left( W^T W \right)^{-\tfrac{1}{2}}}"],
        [(2, 1), "br", r"\mathbf{Q^T = S W^T}"],
        [(2, 2), "br", r"\mathbf{R = S W^T A}"],
    ]


def filter_qr_name_specs(
    name_specs: Sequence[Any],
    *,
    grid: Sequence[Sequence[Any]],
) -> List[Any]:
    """Keep only name specs that target existing non-empty QR grid blocks."""
    n_block_rows = len(grid)
    n_block_cols = max((len(row) for row in grid), default=0)
    filtered_specs: List[Any] = []
    for spec in name_specs:
        if not (isinstance(spec, (list, tuple)) and len(spec) >= 1):
            continue
        target_grid = spec[0]
        if not (isinstance(target_grid, (list, tuple)) and len(target_grid) == 2):
            continue
        gM, gN = int(target_grid[0]), int(target_grid[1])
        if gM < 0 or gN < 0 or gM >= n_block_rows or gN >= n_block_cols:
            continue
        try:
            if grid[gM][gN] is None:
                continue
        except Exception:
            continue
        filtered_specs.append(spec)
    return filtered_specs


def qr_callout_rules(
    *,
    a_rows: int,
    a_cols: int,
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """Return label-shift and length rules for QR matrix-name callouts."""
    r_shift = -1.0
    if a_cols and a_cols < 3:
        r_shift = -2.0
    label_shift_rules = [
        (r"\mathbf{W^T W}", 1.0),
        (r"\mathbf{W^T A}", 1.0),
        (r"\mathbf{W^T}", 1.0),
        (r"\mathbf{S = \left( W^T W \right)^{-\tfrac{1}{2}}}", 1.0),
        (r"\mathbf{W}", 1.0),
        (r"\mathbf{A}", 1.0),
        (r"\mathbf{Q^T = S W^T}", -1.0),
        (r"\mathbf{R = S W^T A}", r_shift),
    ]
    length_rules: List[Tuple[str, float]] = []
    if a_cols and a_cols < 3:
        length_rules = [(r"\mathbf{Q^T = S W^T}", 14.0)]
    if a_rows == 2 and a_cols == 2:
        length_rules = [(r"\mathbf{Q^T = S W^T}", 14.0)]
    return label_shift_rules, length_rules


def qr_label_layouts(
    grid: Sequence[Sequence[Any]],
    label_text_color: str,
    *,
    mat_shape: MatrixShape,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    label_rows: List[Dict[str, Any]] = []
    label_cols: List[Dict[str, Any]] = []
    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    n_cols = 0
    if n_block_rows > 0 and n_block_cols > 2:
        try:
            n_cols = mat_shape(grid[0][2])[1]
        except Exception:
            n_cols = 0
    if n_cols > 0:
        v_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{v_{i+1}}}}}$" for i in range(n_cols)]
        w_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{w_{i+1}}}}}$" for i in range(n_cols)]
        wt_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{w_{{{i+1}}}^T}}}}$" for i in range(n_cols)]
        if n_block_rows > 0 and n_block_cols > 2:
            label_rows.append({"grid": (0, 2), "side": "above", "labels": v_labels})
        if n_block_rows > 0 and n_block_cols > 3:
            label_rows.append({"grid": (0, 3), "side": "above", "labels": w_labels})
        if n_block_rows > 1 and n_block_cols > 1:
            label_cols.append({"grid": (1, 1), "side": "left", "labels": wt_labels})
    return label_rows, label_cols


def qr_name_specs_to_callouts(
    name_specs: Sequence[Any],
    *,
    color: str,
    angle_deg: float = -35.0,
    length_mm: float = 6.0,
    label_shift_rules: Optional[Sequence[Tuple[str, float]]] = None,
    length_rules: Optional[Sequence[Tuple[str, float]]] = None,
) -> List[Dict[str, Any]]:
    side_map = {
        "al": ("left", "top"),
        "tl": ("left", "top"),
        "bl": ("left", "bottom"),
        "ar": ("right", "top"),
        "tr": ("right", "top"),
        "br": ("right", "bottom"),
    }
    out: List[Dict[str, Any]] = []
    for spec in name_specs:
        if not isinstance(spec, (list, tuple)) or len(spec) < 3:
            continue
        grid = spec[0]
        if not (isinstance(grid, (list, tuple)) and len(grid) == 2):
            continue
        loc = str(spec[1]).strip().lower()
        label_str = str(spec[2]).strip()
        side, anchor = side_map.get(loc, ("right", "center"))
        local_angle = angle_deg
        if "Q^T" in label_str or "R =" in label_str:
            local_angle = 40.0
        label_shift_y_mm = None
        if label_shift_rules:
            for needle, shift in label_shift_rules:
                if needle in label_str:
                    label_shift_y_mm = float(shift)
                    break
        local_length = float(length_mm)
        if length_rules:
            for needle, override in length_rules:
                if needle in label_str:
                    local_length = float(override)
                    break
        callout = {
            "grid": (int(grid[0]), int(grid[1])),
            "label": label_str,
            "side": side,
            "anchor": anchor,
            "color": color,
            "angle_deg": float(local_angle),
            "length_mm": float(local_length),
        }
        if label_shift_y_mm is not None:
            callout["label_shift_y_mm"] = float(label_shift_y_mm)
        out.append(callout)
    return out
