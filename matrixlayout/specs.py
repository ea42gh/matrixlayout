from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, Mapping, Iterable


@dataclass(frozen=True)
class SubMatrixLoc:
    """Typed ``\\SubMatrix`` descriptor."""

    opts: str
    start: str  # "r-c"
    end: str  # "r-c"
    left_delim: Optional[str] = None
    right_delim: Optional[str] = None

    def to_tuple(self) -> Tuple[Any, ...]:
        if self.left_delim is None and self.right_delim is None:
            return (self.opts, self.start, self.end)
        span = f"{{{self.start}}}{{{self.end}}}"
        return (self.opts, span, self.left_delim, self.right_delim)


@dataclass(frozen=True)
class PivotBox:
    """Fit-box around a pivot or span."""

    fit_target: str  # "(r-c)(r-c)"
    style: str = ""

    def to_tuple(self) -> Tuple[str, str]:
        return (self.fit_target, self.style)


@dataclass(frozen=True)
class TextAt:
    """Text label positioned at a cell node."""

    coord: str  # "(r-c)"
    text: str
    style: str = ""

    def to_tuple(self) -> Tuple[str, str, str]:
        return (self.coord, self.text, self.style)


@dataclass(frozen=True)
class RowEchelonPath:
    """Raw TikZ command inserted in CodeAfter/tikzpicture."""

    tikz: str

    def to_str(self) -> str:
        return self.tikz


@dataclass(frozen=True)
class GELayoutSpec:
    """Serializable layout spec for GE/GE-grid figures.

    All fields are optional. When a field is ``None`` it has no effect.
    """

    nice_options: Optional[Any] = None
    # ``extension`` is injected into the LaTeX preamble (before \begin{document}).
    # Use this for true preamble directives like \usepackage or \geometry.
    extension: Optional[str] = None
    # ``preamble`` is injected into the LaTeX document body (after \begin{document}).
    # It is intended for *content* inserted before the math environment (e.g.,
    # TikZ setup that is safe in the document body). Do not put \usepackage here.
    preamble: Optional[str] = None
    codebefore: Optional[Sequence[Any]] = None
    submatrix_locs: Optional[Sequence[Union[SubMatrixLoc, Dict[str, Any], Tuple[Any, ...]]]] = None
    submatrix_names: Optional[Sequence[Any]] = None
    pivot_locs: Optional[Sequence[Union[PivotBox, Dict[str, Any], Tuple[Any, ...]]]] = None
    txt_with_locs: Optional[Sequence[Union[TextAt, Dict[str, Any], Tuple[Any, ...]]]] = None
    rowechelon_paths: Optional[Sequence[Union[RowEchelonPath, str, Dict[str, Any]]]] = None
    callouts: Optional[Union[Sequence[Any], bool]] = None
    matrix_labels: Optional[Union[Sequence[Any], bool]] = None

    landscape: Optional[bool] = None
    create_cell_nodes: Optional[bool] = None
    create_extra_nodes: Optional[bool] = None
    create_medium_nodes: Optional[bool] = None

    outer_delims: Optional[bool] = None
    outer_delims_name: Optional[str] = None
    outer_delims_span: Optional[Tuple[int, int]] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "GELayoutSpec":
        if d is None:
            return GELayoutSpec()
        allowed = set(GELayoutSpec.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        extra = set(d.keys()) - allowed
        if extra:
            raise ValueError(f"Unknown GELayoutSpec fields: {sorted(extra)}")
        return GELayoutSpec(**d)

    def to_dict(self, *, drop_none: bool = True) -> Dict[str, Any]:
        """Convert to a plain ``dict`` suitable for serialization.

        Parameters
        ----------
        drop_none:
            If True, omit keys whose values are ``None``.
        """
        d = asdict(self)
        if drop_none:
            return {k: v for k, v in d.items() if v is not None}
        return d


@dataclass(frozen=True)
class SubMatrixSpan:
    """A resolved nicematrix ``\\SubMatrix`` span.

    Coordinates are 1-based nicematrix coordinates.

    This is primarily intended for notebooks and higher-level helpers that want
    to attach TikZ paths (e.g., arrows/callouts) to a known ``\\SubMatrix`` name
    without re-parsing TeX.
    """

    name: str
    row_start: int
    col_start: int
    row_end: int
    col_end: int
    block_row: int
    block_col: int

    @property
    def start_token(self) -> str:
        return f"{self.row_start}-{self.col_start}"

    @property
    def end_token(self) -> str:
        return f"{self.row_end}-{self.col_end}"

    @property
    def submatrix_loc(self) -> Tuple[str, str, str]:
        """Return the canonical ``(opts, start, end)`` tuple for templates."""

        return (f"name={self.name}", self.start_token, self.end_token)

    @property
    def left_delim_node(self) -> str:
        return f"{self.name}-left"

    @property
    def right_delim_node(self) -> str:
        return f"{self.name}-right"


@dataclass(frozen=True)
class GEGridBundle:
    """A TeX document plus structured metadata for a GE matrix grid.

    This is intended for notebook workflows where users want both the rendered
    TeX and the resolved ``\\SubMatrix`` spans (for attaching arrows/callouts)
    without regex-parsing the TeX.
    """

    tex: str
    submatrix_spans: List[SubMatrixSpan]


@dataclass(frozen=True)
class QRGridBundle:
    """A TeX document plus structured metadata for a QR matrix grid."""

    tex: str
    submatrix_spans: List[SubMatrixSpan]


@dataclass(frozen=True)
class GEGridSpec:
    """Serializable spec for a GE matrix grid + layout options."""

    matrices: Sequence[Sequence[Any]]
    Nrhs: Any = 0
    formatter: Optional[Any] = None
    outer_hspace_mm: int = 6
    block_vspace_mm: int = 1
    cell_align: str = "r"
    block_align: Optional[str] = None
    block_valign: Optional[str] = None
    extension: str = ""
    fig_scale: Optional[Any] = None
    preamble: Optional[str] = None
    nice_options: Optional[str] = None
    outer_delims: Optional[bool] = None
    layout: Optional[Any] = None
    legacy_submatrix_names: bool = False
    legacy_format: bool = False
    label_rows: Optional[Sequence[Any]] = None
    label_cols: Optional[Sequence[Any]] = None
    label_gap_mm: Optional[float] = 0.8
    variable_labels: Optional[Sequence[Any]] = None
    format_nrhs: bool = True
    decorators: Optional[Sequence[Any]] = None
    decorations: Optional[Sequence[Any]] = None
    pivot_locs: Optional[Sequence[Any]] = None
    txt_with_locs: Optional[Sequence[Any]] = None
    rowechelon_paths: Optional[Sequence[Any]] = None
    callouts: Optional[Sequence[Any]] = None
    codebefore: Optional[Sequence[Any]] = None
    create_cell_nodes: Optional[bool] = None
    create_extra_nodes: Optional[bool] = None
    create_medium_nodes: Optional[bool] = None
    strict: Optional[bool] = None
    array_names: Optional[Any] = None
    label_color: Optional[str] = None
    label_text_color: Optional[str] = None
    known_zero_color: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any], *, allow_extra: Optional[bool] = None) -> "GEGridSpec":
        if d is None:
            raise ValueError("GEGridSpec.from_dict requires a mapping")
        if allow_extra is None:
            allow_extra = not bool(d.get("strict", True))
        allowed = set(GEGridSpec.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        extra = set(d.keys()) - allowed
        if extra and not allow_extra:
            raise ValueError(f"Unknown GEGridSpec fields: {sorted(extra)}")
        if "matrices" not in d:
            raise ValueError("GEGridSpec requires 'matrices'")
        filtered = {k: v for k, v in d.items() if k in allowed}
        return GEGridSpec(**filtered)

    def to_dict(self, *, drop_none: bool = True) -> Dict[str, Any]:
        d = asdict(self)
        if drop_none:
            return {k: v for k, v in d.items() if v is not None}
        return d


@dataclass(frozen=True)
class QRGridSpec:
    """Serializable spec for a QR matrix grid + layout options."""

    matrices: Sequence[Sequence[Any]]
    formatter: Optional[Any] = None
    array_names: Any = True
    fig_scale: Optional[Any] = None
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n"
    extension: str = ""
    nice_options: Optional[str] = "vlines-in-sub-matrix = I"
    label_color: str = "blue"
    label_text_color: str = "red"
    known_zero_color: str = "brown"
    decorators: Optional[Sequence[Any]] = None
    strict: Optional[bool] = None
    landscape: Optional[bool] = None
    create_cell_nodes: Optional[bool] = True
    create_extra_nodes: Optional[bool] = True
    create_medium_nodes: Optional[bool] = True
    specs: Optional[Sequence[Mapping[str, Any]]] = None

    @staticmethod
    def from_dict(d: Dict[str, Any], *, allow_extra: Optional[bool] = None) -> "QRGridSpec":
        if d is None:
            raise ValueError("QRGridSpec.from_dict requires a mapping")
        if allow_extra is None:
            allow_extra = not bool(d.get("strict", True))
        allowed = set(QRGridSpec.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        extra = set(d.keys()) - allowed
        if extra and not allow_extra:
            raise ValueError(f"Unknown QRGridSpec fields: {sorted(extra)}")
        if "matrices" not in d:
            raise ValueError("QRGridSpec requires 'matrices'")
        filtered = {k: v for k, v in d.items() if k in allowed}
        return QRGridSpec(**filtered)

    def to_dict(self, *, drop_none: bool = True) -> Dict[str, Any]:
        d = asdict(self)
        if drop_none:
            return {k: v for k, v in d.items() if v is not None}
        return d


def _matrix_shape(mat: Any) -> Optional[Tuple[int, int]]:
    if mat is None:
        return None
    shape = getattr(mat, "shape", None)
    if shape is not None:
        try:
            if len(shape) >= 2:
                return (int(shape[0]), int(shape[1]))
        except Exception:
            pass
    if isinstance(mat, (list, tuple)):
        if len(mat) == 0:
            return (0, 0)
        first = mat[0]
        if isinstance(first, (list, tuple)):
            return (len(mat), len(first))
    return None


def _grid_size(mats: Any) -> Optional[Tuple[int, int]]:
    if not isinstance(mats, (list, tuple)) or not mats:
        return None
    ncols = None
    for row in mats:
        if not isinstance(row, (list, tuple)):
            return None
        if ncols is None:
            ncols = len(row)
        elif len(row) != ncols:
            return None
    return (len(mats), ncols or 0)


def _validate_grid_matrices(mats: Sequence[Sequence[Any]]) -> List[str]:
    errors: List[str] = []
    grid = _grid_size(mats)
    if grid is None:
        errors.append("matrices must be a rectangular 2D list")
        return errors
    nrows, ncols = grid
    col_shapes: List[Optional[Tuple[int, int]]] = [None] * ncols
    for r, row in enumerate(mats):
        row_shapes: List[Tuple[int, int]] = []
        for c, item in enumerate(row):
            shape = _matrix_shape(item)
            if shape is None:
                continue
            row_shapes.append(shape)
            if col_shapes[c] is None:
                col_shapes[c] = shape
            elif col_shapes[c] != shape:
                errors.append(f"column {c} shape mismatch: expected {col_shapes[c]}, got {shape}")
        if row_shapes:
            row_rows = {s[0] for s in row_shapes}
            if len(row_rows) > 1:
                errors.append(f"row {r} has inconsistent row counts: {sorted(row_rows)}")
    return errors


def validate_ge_spec(spec: Mapping[str, Any], *, strict: bool = True) -> List[str]:
    """Validate a GE spec dict and return a list of errors.

    This is intended as a lightweight preflight before rendering.
    """
    errors: List[str] = []
    try:
        GEGridSpec.from_dict(dict(spec), allow_extra=not strict)
    except Exception as exc:
        errors.append(str(exc))
    mats = spec.get("matrices") if isinstance(spec, Mapping) else None
    if mats is None:
        if not any("requires 'matrices'" in e for e in errors):
            errors.append("GE spec requires 'matrices'")
        return errors
    errors.extend(_validate_grid_matrices(mats))
    return errors


def validate_qr_spec(spec: Mapping[str, Any], *, strict: bool = True) -> List[str]:
    """Validate a QR spec dict and return a list of errors."""
    errors: List[str] = []
    try:
        QRGridSpec.from_dict(dict(spec), allow_extra=not strict)
    except Exception as exc:
        errors.append(str(exc))
    mats = spec.get("matrices") if isinstance(spec, Mapping) else None
    if mats is None:
        if not any("requires 'matrices'" in e for e in errors):
            errors.append("QR spec requires 'matrices'")
        return errors
    errors.extend(_validate_grid_matrices(mats))
    return errors
