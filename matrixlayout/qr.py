"""QR (Gram–Schmidt) layout helpers using the GE template.

This module mirrors the legacy MatrixGridLayout-based QR rendering by building
the same grid layout (matrix-of-matrices) and emitting TeX through the
GE template. The algorithmic inputs (A, W, etc.) are handled upstream in
la_figures; this module focuses on layout + formatting only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, Callable, Iterable, Mapping
import re

from .formatting import latexify
from .ge import grid_tex
from .render import render_svg
from .specs import QRGridSpec


def _as_grid(matrices: Any) -> List[List[Any]]:
    if matrices is None:
        return []
    if not isinstance(matrices, list):
        return [[None, matrices]]
    out: List[List[Any]] = []
    for row in matrices:
        if isinstance(row, list):
            out.append(list(row))
        else:
            out.append([row])
    return out


def _mat_shape(mat: Any) -> Tuple[int, int]:
    if mat is None:
        return (0, 0)
    shp = getattr(mat, "shape", None)
    if shp is not None:
        try:
            return (int(shp[0]), int(shp[1]))
        except Exception:
            pass
    if isinstance(mat, (list, tuple)) and mat:
        rows = len(mat)
        first = mat[0]
        if isinstance(first, (list, tuple)):
            return (rows, len(first))
    return (0, 0)


def _mat_entry(mat: Any, i: int, j: int) -> Any:
    if mat is None:
        return ""
    try:
        return mat[i, j]
    except Exception:
        return mat[i][j]


def _set_extra(extra: Optional[Union[int, Sequence[int]]], n: int) -> List[int]:
    if isinstance(extra, int):
        return [0] * n + [int(extra)]
    if extra is None:
        return [0] * (n + 1)
    return [int(x) for x in extra]


class QRGridLayout:
    """Compute the grid layout used in the legacy QR figure."""

    def __init__(self, matrices: Sequence[Sequence[Any]], *, extra_rows: Any = None, extra_cols: Any = None):
        self.matrices = _as_grid(matrices)
        self.nGridRows = len(self.matrices)
        self.nGridCols = max((len(row) for row in self.matrices), default=0)

        self._set_shapes()
        self.mat_row_height = [max((self.array_shape[i][j][0] for j in range(self.nGridCols)), default=0) for i in range(self.nGridRows)]
        self.mat_col_width = [max((self.array_shape[i][j][1] for i in range(self.nGridRows)), default=0) for j in range(self.nGridCols)]

        self.adjust_positions(extra_cols, extra_rows)
        self.array_names: List[str] = []
        self.submatrix_name = "QR"
        self.locs: List[List[str]] = []
        self.tex_list: List[str] = []
        self.codebefore: List[str] = []

    def _set_shapes(self) -> None:
        self.array_shape: List[List[Tuple[int, int]]] = [
            [(_mat_shape(self.matrices[i][j]) if j < len(self.matrices[i]) else (0, 0)) for j in range(self.nGridCols)]
            for i in range(self.nGridRows)
        ]

    def adjust_positions(self, extra_cols: Any = None, extra_rows: Any = None) -> None:
        self.extra_cols = _set_extra(extra_cols, self.nGridCols)
        self.extra_rows = _set_extra(extra_rows, self.nGridRows)

        self.cs_extra_cols = _cumsum(self.extra_cols)
        self.cs_extra_rows = _cumsum(self.extra_rows)
        self.cs_mat_row_height = _cumsum([0] + self.mat_row_height)
        self.cs_mat_col_width = _cumsum([0] + self.mat_col_width)

        self.tex_shape = (
            self.cs_mat_row_height[-1] + self.cs_extra_rows[-1],
            self.cs_mat_col_width[-1] + self.cs_extra_cols[-1],
        )

    def _top_left_bottom_right(self, gM: int, gN: int) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        shape = self.array_shape[gM][gN]
        row_offset = self.cs_extra_rows[gM] + self.cs_mat_row_height[gM] + self.mat_row_height[gM] - shape[0]
        col_offset = self.cs_extra_cols[gN] + self.cs_mat_col_width[gN] + self.mat_col_width[gN] - shape[1]
        tl = (row_offset, col_offset)
        br = (row_offset + shape[0] - 1, col_offset + shape[1] - 1)
        return tl, br, shape

    @staticmethod
    def matrix_array_format(ncols: int, *, p_str: str = "I", vpartitions: Optional[Sequence[int]] = None) -> str:
        if not vpartitions:
            return "r" * ncols
        s = ""
        cur = 0
        for p in vpartitions:
            s_r = "r" * (p - cur)
            s += f"{s_r}{p_str}"
            cur = p
        if cur < ncols:
            s += "r" * (ncols - cur)
        return s

    def array_format_string_list(
        self,
        *,
        partitions: Optional[Dict[int, Sequence[int]]] = None,
        spacer_string: str = r"@{\hspace{9mm}}",
        p_str: str = "I",
        last_col_format: str = r"l@{\hspace{2cm}}",
    ) -> None:
        if partitions is None:
            partitions = {}
        for i in range(self.nGridCols):
            if i not in partitions:
                partitions[i] = None

        fmt = "r" * self.extra_cols[0]
        last = self.nGridCols - 1
        for i in range(self.nGridCols):
            n = self.mat_col_width[i]
            fmt += spacer_string + self.matrix_array_format(n, p_str=p_str, vpartitions=partitions[i])

            extra = self.extra_cols[i + 1]
            if extra > 0:
                if i == last:
                    if extra > 1:
                        fmt += spacer_string + ("r" * (extra - 1)) + last_col_format
                    else:
                        fmt += spacer_string + last_col_format
                else:
                    fmt += spacer_string + ("r" * extra)

        self.format = fmt

    def array_of_tex_entries(self, *, formatter: Any = latexify) -> None:
        rows, cols = self.tex_shape
        a_tex: List[List[str]] = [["" for _ in range(cols)] for __ in range(rows)]
        for i in range(self.nGridRows):
            for j in range(self.nGridCols):
                tl, _, shape = self._top_left_bottom_right(i, j)
                if shape[0] == 0 or shape[1] == 0:
                    continue
                mat = self.matrices[i][j] if j < len(self.matrices[i]) else None
                for ia in range(shape[0]):
                    for ja in range(shape[1]):
                        a_tex[tl[0] + ia][tl[1] + ja] = str(formatter(_mat_entry(mat, ia, ja)))
        self.a_tex = a_tex

    def decorate_tex_entries(self, gM: int, gN: int, decorate: Any, *, entries: Optional[Sequence[Tuple[int, int]]] = None) -> None:
        try:
            tl, _, shape = self._top_left_bottom_right(gM, gN)
        except Exception:
            return

        if entries is None:
            for i in range(shape[0]):
                for j in range(shape[1]):
                    self.a_tex[tl[0] + i][tl[1] + j] = decorate(self.a_tex[tl[0] + i][tl[1] + j])
        else:
            for i, j in entries:
                self.a_tex[tl[0] + i][tl[1] + j] = decorate(self.a_tex[tl[0] + i][tl[1] + j])

    def tl_shape_above(self, gM: int, gN: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        tl, _, _ = self._top_left_bottom_right(gM, gN)
        free_tl = (tl[0] - self.extra_rows[gM], tl[1])
        shape = (self.extra_rows[gM], self.tex_shape[1] - free_tl[1])
        return free_tl, shape

    def tl_shape_left(self, gM: int, gN: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        tl, _, _ = self._top_left_bottom_right(gM, gN)
        return (tl[0], tl[1] - self.extra_cols[gN]), (self.tex_shape[0] - tl[0], self.extra_cols[gN])

    def add_row_above(self, gM: int, gN: int, m: Sequence[Any], *, formatter: Any = latexify, offset: int = 0) -> None:
        tl, _ = self.tl_shape_above(gM, gN)
        for j, v in enumerate(m):
            self.a_tex[tl[0] + offset][tl[1] + j] = str(formatter(v))

    def add_col_left(self, gM: int, gN: int, m: Sequence[Any], *, formatter: Any = latexify, offset: int = 0) -> None:
        tl, _ = self.tl_shape_left(gM, gN)
        for i, v in enumerate(m):
            self.a_tex[tl[0] + i][tl[1] + offset - 1] = str(formatter(v))

    def nm_submatrix_locs(
        self,
        name: str = "A",
        *,
        color: str = "blue",
        name_specs: Optional[Sequence[Any]] = None,
        line_specs: Optional[Sequence[Any]] = None,
    ) -> None:
        self.submatrix_name = name
        smat_args: List[List[str]] = [[ "" for _ in range(self.nGridCols)] for __ in range(self.nGridRows)]
        if line_specs is not None:
            for pos, h_lines, v_lines in line_specs:
                gM, gN = pos
                if h_lines is not None:
                    if isinstance(h_lines, int):
                        smat_args[gM][gN] = f",hlines={h_lines}"
                    else:
                        smat_args[gM][gN] = ",hlines={" + ",".join(str(s) for s in h_lines) + "}"
                if v_lines is not None:
                    if isinstance(v_lines, int):
                        smat_args[gM][gN] += f",vlines={v_lines}"
                    else:
                        smat_args[gM][gN] += ",vlines={" + ",".join(str(s) for s in v_lines) + "}"

        locs: List[List[str]] = []
        for i in range(self.nGridRows):
            for j in range(self.nGridCols):
                if self.array_shape[i][j][0] != 0:
                    tl, br, _ = self._top_left_bottom_right(i, j)
                    smat_arg = f"name={name}{i}x{j}" + smat_args[i][j]
                    locs.append([smat_arg, f"{{{tl[0] + 1}-{tl[1] + 1}}}{{{br[0] + 1}-{br[1] + 1}}}"])
        self.locs = locs

        if name_specs is not None:
            array_names: List[str] = []
            ar = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.north east) + (0.02,0.02) $) -- +(40:0.6cm)    node[COLOR, above right=-3pt]{TXT};".replace(
                "COLOR", color
            )
            al = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.north west) + (-0.02,0.02) $) -- +(140:0.6cm) node[COLOR, above left=-3pt] {TXT};".replace(
                "COLOR", color
            )
            a = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.north) + (0,0) $) -- +(0cm,0.6cm) node[COLOR, above=1pt] {TXT};".replace(
                "COLOR", color
            )
            bl = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.south west) + (-0.02,-0.02) $) -- +(220:0.6cm)  node[COLOR, below left=-3pt]{TXT};".replace(
                "COLOR", color
            )
            br = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.south east) + (0.02,-0.02) $) -- +(-40:0.6cm)   node[COLOR, below right=-3pt]{TXT};".replace(
                "COLOR", color
            )
            b = r"\tikz \draw[<-,>=stealth,COLOR,thick] ($ (NAME.south) + (0,0) $) -- +(0cm,-0.6cm) node[COLOR, below=1pt] {TXT};".replace(
                "COLOR", color
            )

            for (gM, gN), pos, txt in name_specs:
                nm = f"{name}{gM}x{gN}"
                t = None
                if pos == "a":
                    t = a.replace("NAME", nm).replace("TXT", txt)
                elif pos == "al":
                    t = al.replace("NAME", nm).replace("TXT", txt)
                elif pos == "ar":
                    t = ar.replace("NAME", nm).replace("TXT", txt)
                elif pos == "b":
                    t = b.replace("NAME", nm).replace("TXT", txt)
                elif pos == "bl":
                    t = bl.replace("NAME", nm).replace("TXT", txt)
                elif pos == "br":
                    t = br.replace("NAME", nm).replace("TXT", txt)
                if t is not None:
                    array_names.append(t)
            self.array_names = array_names

    def tex_repr(self, *, blockseps: str = r"\noalign{\vskip3mm} ") -> None:
        self.tex_list = [" & ".join(row) for row in self.a_tex]
        for i in range(len(self.tex_list) - 1):
            self.tex_list[i] += r" \\"

        idxs = []
        for i, a, b, c in zip(
            range(len(self.cs_mat_row_height[1:-1])),
            self.cs_mat_row_height[1:-1],
            self.cs_extra_rows[1:-1],
            self.extra_rows[1:-1],
        ):
            idxs.append(int(a + b - c))
        for i in idxs:
            if i - 1 >= 0:
                self.tex_list[i - 1] += blockseps

        if self.extra_rows[-1] != 0:
            idx = self.tex_shape[0] - self.extra_rows[-1] - 1
            if 0 <= idx < len(self.tex_list):
                self.tex_list[idx] += blockseps


def _cumsum(vals: Sequence[int]) -> List[int]:
    out: List[int] = []
    total = 0
    for v in vals:
        total += int(v)
        out.append(total)
    return out


def _make_decorator(
    *,
    text_color: str = "black",
    bg_color: Optional[str] = None,
    text_bg: Optional[str] = None,
    boxed: Optional[bool] = None,
    box_color: Optional[str] = None,
    bf: Optional[bool] = None,
    move_right: bool = False,
    delim: Optional[str] = None,
) -> Any:
    box_decorator = r"\boxed<{a}>"
    coloredbox_decorator = r"\colorboxed<{color}><{a}>"
    color_decorator = r"\Block[draw={text_color},fill={bg_color}]<><{a}>"
    txt_color_decorator = r"\color<{color}><{a}>"
    bg_color_decorator = r"\colorbox<{color}><{a}>"
    bf_decorator = r"\mathbf<{a}>"
    rlap_decorator = r"\mathrlap<{a}>"
    delim_decorator = r"<{delim}{a}{delim}>"

    x = "{a}"
    if bf is not None:
        x = bf_decorator.format(a=x)
    if boxed is not None:
        x = box_decorator.format(a=x)
    if box_color is not None:
        x = coloredbox_decorator.format(a=x, color=box_color)
    if bg_color is not None:
        x = bg_color_decorator.format(a=x, color=bg_color)
    if text_bg is not None:
        x = color_decorator.format(a=x, text_color=text_color, bg_color=text_bg)
    elif text_color != "black":
        x = txt_color_decorator.format(color=text_color, a=x)
    if move_right:
        x = rlap_decorator.format(a=x)
    if delim is not None:
        x = delim_decorator.format(delim=delim, a=x)

    x = x.replace("<", "{{").replace(">", "}}")
    return lambda a: x.format(a=a)


def _qr_known_zero_entries(matrices: Sequence[Sequence[Any]]) -> List[Tuple[Tuple[int, int], List[Tuple[int, int]]]]:
    if not matrices or len(matrices) < 2:
        return []
    WtA = None
    WtW = None
    try:
        WtA = matrices[1][2]
        WtW = matrices[1][3]
    except Exception:
        return []

    m_wta = _mat_shape(WtA)[0]
    m_wtw = _mat_shape(WtW)[0]
    if m_wta <= 0 or m_wtw <= 0:
        return []

    entries_wta = [(i, j) for i in range(m_wta) for j in range(m_wta) if i > j]
    entries_wtw = [(i, j) for i in range(m_wtw) for j in range(m_wtw) if i != j]
    return [((1, 2), entries_wta), ((1, 3), entries_wtw)]


def _qr_default_name_specs() -> List[Any]:
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


def _qr_name_specs_to_callouts(
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
            "grid_pos": (int(grid[0]), int(grid[1])),
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


def _merge_scalar(field: str, explicit: Any, spec_val: Any) -> Any:
    if spec_val is None:
        return explicit
    if explicit is None:
        return spec_val
    if explicit != spec_val:
        raise ValueError(f"Conflicting values for {field}: explicit={explicit!r} spec={spec_val!r}")
    return explicit


def _coerce_qr_spec(spec: Optional[Union[Dict[str, Any], QRGridSpec]]) -> Optional[QRGridSpec]:
    if spec is None:
        return None
    if isinstance(spec, QRGridSpec):
        return spec
    return QRGridSpec.from_dict(spec)


def qr_grid_tex(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    *,
    spec: Optional[Union[Dict[str, Any], QRGridSpec]] = None,
    specs: Optional[Sequence[Mapping[str, Any]]] = None,
    formatter: Any = latexify,
    array_names: Any = True,
    fig_scale: Optional[Any] = None,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n",
    extension: str = "",
    nice_options: Optional[str] = "vlines-in-sub-matrix = I",
    label_color: str = "blue",
    label_text_color: str = "red",
    known_zero_color: str = "brown",
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = True,
    create_extra_nodes: Optional[bool] = True,
    create_medium_nodes: Optional[bool] = True,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
) -> str:
    """Return a QR layout TeX document.

    Examples
    --------
    Decorate the (0,0) entry in the A-block::

        def box(tex): return rf"\\boxed{{{tex}}}"
        decorators = [{"grid": (0, 2), "entries": [(0, 0)], "decorator": box}]
        tex = qr_grid_tex(matrices=matrices, decorators=decorators)
    """
    spec_obj = _coerce_qr_spec(spec)
    if spec_obj is not None:
        matrices = _merge_scalar("matrices", matrices, spec_obj.matrices)
        formatter = _merge_scalar("formatter", formatter, spec_obj.formatter)
        array_names = _merge_scalar("array_names", array_names, spec_obj.array_names)
        fig_scale = _merge_scalar("fig_scale", fig_scale, spec_obj.fig_scale)
        preamble = _merge_scalar("preamble", preamble, spec_obj.preamble)
        extension = _merge_scalar("extension", extension, spec_obj.extension)
        nice_options = _merge_scalar("nice_options", nice_options, spec_obj.nice_options)
        label_color = _merge_scalar("label_color", label_color, spec_obj.label_color)
        label_text_color = _merge_scalar("label_text_color", label_text_color, spec_obj.label_text_color)
        known_zero_color = _merge_scalar("known_zero_color", known_zero_color, spec_obj.known_zero_color)
        landscape = _merge_scalar("landscape", landscape, spec_obj.landscape)
        create_cell_nodes = _merge_scalar("create_cell_nodes", create_cell_nodes, spec_obj.create_cell_nodes)
        create_extra_nodes = _merge_scalar("create_extra_nodes", create_extra_nodes, spec_obj.create_extra_nodes)
        create_medium_nodes = _merge_scalar("create_medium_nodes", create_medium_nodes, spec_obj.create_medium_nodes)
        decorators = _merge_scalar("decorators", decorators, spec_obj.decorators)
        strict = _merge_scalar("strict", strict, spec_obj.strict)
        if spec_obj.specs is not None:
            specs = _merge_scalar("specs", specs, spec_obj.specs)

    if matrices is None:
        raise ValueError("qr_grid_tex requires `matrices`")
    if formatter is None:
        formatter = latexify

    grid = _as_grid(matrices)

    # Known-zero decorators.
    qr_decorators: List[Dict[str, Any]] = list(decorators or [])
    brown = _make_decorator(text_color=known_zero_color, bf=True)
    for (gM, gN), entries in _qr_known_zero_entries(grid):
        qr_decorators.append(
            {"grid": (gM, gN), "entries": entries, "decorator": brown},
        )

    # Gram–Schmidt labels via label rows/cols.
    label_rows: List[Dict[str, Any]] = []
    label_cols: List[Dict[str, Any]] = []
    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    n_cols = 0
    if n_block_rows > 0 and n_block_cols > 2:
        try:
            n_cols = _mat_shape(grid[0][2])[1]
        except Exception:
            n_cols = 0
    if n_cols > 0:
        v_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{v_{i+1}}}}}$" for i in range(n_cols)]
        w_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{w_{i+1}}}}}$" for i in range(n_cols)]
        wt_labels = [rf"$\textcolor{{{label_text_color}}}{{\mathbf{{w_{{{i+1}}}^T}}}}$" for i in range(n_cols)]
        if n_block_rows > 0 and n_block_cols > 2:
            label_rows.append({"grid": (0, 2), "side": "above", "rows": v_labels})
        if n_block_rows > 0 and n_block_cols > 3:
            label_rows.append({"grid": (0, 3), "side": "above", "rows": w_labels})
        if n_block_rows > 1 and n_block_cols > 1:
            label_cols.append(
                {"grid": (1, 1), "side": "left", "cols": wt_labels}
            )

    callouts: Optional[List[Dict[str, Any]]] = None
    if array_names:
        name_specs = _qr_default_name_specs() if array_names is True else array_names
        a_rows = a_cols = 0
        if n_block_rows > 0 and n_block_cols > 2:
            try:
                a_rows, a_cols = _mat_shape(grid[0][2])
            except Exception:
                a_rows = a_cols = 0
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
        length_rules = []
        if a_cols and a_cols < 3:
            length_rules = [(r"\mathbf{Q^T = S W^T}", 8.0)]
        if a_rows == 2 and a_cols == 2:
            length_rules = [(r"\mathbf{Q^T = S W^T}", 14.0)]
        callouts = _qr_name_specs_to_callouts(
            name_specs,
            color=label_color,
            angle_deg=-35.0,
            length_mm=6.0,
            label_shift_rules=label_shift_rules,
            length_rules=length_rules,
        )

    return grid_tex(
        matrices=grid,
        formatter=formatter,
        preamble=preamble,
        extension=extension,
        nice_options=nice_options,
        fig_scale=fig_scale,
        decorators=qr_decorators or None,
        label_rows=label_rows or None,
        label_cols=label_cols or None,
        callouts=callouts,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        create_extra_nodes=create_extra_nodes,
        create_medium_nodes=create_medium_nodes,
        strict=bool(strict),
        specs=specs,
    )


def qr_grid_svg(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    *,
    spec: Optional[Union[Dict[str, Any], QRGridSpec]] = None,
    specs: Optional[Sequence[Mapping[str, Any]]] = None,
    formatter: Any = latexify,
    array_names: Any = True,
    fig_scale: Optional[Any] = None,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n",
    extension: str = "",
    nice_options: Optional[str] = "vlines-in-sub-matrix = I",
    label_color: str = "blue",
    label_text_color: str = "red",
    known_zero_color: str = "brown",
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = True,
    create_extra_nodes: Optional[bool] = True,
    create_medium_nodes: Optional[bool] = True,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
    output_dir: Optional[Union[str, "os.PathLike[str]"]] = None,
    frame: Any = None,
) -> str:
    tex = qr_grid_tex(
        matrices=matrices,
        spec=spec,
        formatter=formatter,
        array_names=array_names,
        fig_scale=fig_scale,
        preamble=preamble,
        extension=extension,
        nice_options=nice_options,
        label_color=label_color,
        label_text_color=label_text_color,
        known_zero_color=known_zero_color,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        create_extra_nodes=create_extra_nodes,
        create_medium_nodes=create_medium_nodes,
        decorators=decorators,
        strict=strict,
        specs=specs,
    )
    return render_svg(
        tex,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
    )


def resolve_qr_grid_name(
    name: Any,
    *,
    matrices: Sequence[Sequence[Any]],
) -> Optional[Tuple[int, int]]:
    """Resolve a QR submatrix name (e.g., 'QR0x2') to a (block_row, block_col) tuple."""
    if not isinstance(name, str):
        return None
    layout = QRGridLayout(matrices)
    name_map: Dict[str, Tuple[int, int]] = {}
    for gM in range(layout.nGridRows):
        for gN in range(layout.nGridCols):
            if layout.array_shape[gM][gN][0] != 0:
                name_map[f"QR{gM}x{gN}"] = (gM, gN)
    if name in name_map:
        return name_map[name]
    m = re.match(r"([A-Za-z]+)(\d+)x(\d+)$", name)
    if m:
        return (int(m.group(2)), int(m.group(3)))
    return None
