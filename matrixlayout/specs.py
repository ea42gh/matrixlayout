from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, TypedDict, Union


GridCoord = Tuple[int, int]
EntryCoord = Tuple[int, int]
EntryDecorator = Callable[..., str]


def _filtered_dataclass_kwargs(
    d: Optional[Dict[str, Any]],
    *,
    spec_name: str,
    allowed: set[str],
    required: str,
    allow_extra: Optional[bool],
) -> Dict[str, Any]:
    if d is None:
        raise ValueError(f"{spec_name}.from_dict requires a mapping")
    if allow_extra is None:
        allow_extra = not bool(d.get("strict", True))
    extra = set(d.keys()) - allowed
    if extra and not allow_extra:
        raise ValueError(f"Unknown {spec_name} fields: {sorted(extra)}")
    if required not in d:
        raise ValueError(f"{spec_name} requires '{required}'")
    return {k: v for k, v in d.items() if k in allowed}


class GELabelRowsSpec(TypedDict, total=False):
    """Dictionary schema for GE row labels.

    ``grid`` is the zero-based outer grid coordinate. ``side`` is ``"above"``
    or ``"below"``. ``labels`` contains one or more label rows; each inner
    value is rendered as a label cell.
    """

    grid: GridCoord
    side: str
    labels: Sequence[Sequence[Any]]
    overlay: bool


class GELabelColsSpec(TypedDict, total=False):
    """Dictionary schema for GE column labels.

    ``grid`` is the zero-based outer grid coordinate. ``side`` is ``"left"``
    or ``"right"``. ``labels`` contains one or more label columns; each inner
    value is rendered as a label cell.
    """

    grid: GridCoord
    side: str
    labels: Sequence[Sequence[Any]]
    overlay: bool


class GEDecorationSpec(TypedDict, total=False):
    """Dictionary schema for GE decoration entries.

    Decorations style entries, rows, columns, submatrices, lines, and callout
    labels. Flexible selector values are still accepted at runtime for
    Julia/Python interoperability; this TypedDict documents the common public
    keys used by ``render_ge_tex`` and ``render_ge_svg``.
    """

    grid: GridCoord
    entries: Sequence[Any]
    rows: Sequence[int]
    cols: Sequence[int]
    submatrix: Any
    decorator: EntryDecorator
    background: str
    color: str
    bold: bool
    outline: bool
    padding_pt: float
    hlines: Any
    vlines: Any
    label: str
    side: str
    angle_deg: float
    length_mm: float


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
    # ``document_preamble`` is injected into the LaTeX preamble (before \begin{document}).
    # Use this for true preamble directives like \usepackage or \geometry.
    document_preamble: Optional[str] = None
    # ``body_preamble`` is injected into the LaTeX document body (after \begin{document}).
    # It is intended for *content* inserted before the math environment (e.g.,
    # TikZ setup that is safe in the document body). Do not put \usepackage here.
    body_preamble: Optional[str] = None
    codebefore: Optional[Sequence[Any]] = None
    submatrix_locs: Optional[Sequence[Union[SubMatrixLoc, Dict[str, Any], Tuple[Any, ...]]]] = None
    submatrix_names: Optional[Sequence[Any]] = None
    pivot_locs: Optional[Sequence[Union[PivotBox, Dict[str, Any], Tuple[Any, ...]]]] = None
    text_annotations: Optional[Sequence[Union[TextAt, Dict[str, Any], Tuple[Any, ...]]]] = None
    rowechelon_paths: Optional[Sequence[Union[RowEchelonPath, str, Dict[str, Any]]]] = None
    callouts: Optional[Union[Sequence[Any], bool]] = None

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
        allowed = set(GELayoutSpec.__dataclass_fields__.keys())
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
    n_rhs: Any = 0
    formatter: Optional[Any] = None
    outer_hspace_mm: int = 6
    block_vspace_mm: int = 1
    cell_align: str = "r"
    block_align: Optional[str] = None
    block_valign: Optional[str] = None
    document_preamble: Optional[str] = None
    body_preamble: Optional[str] = None
    fig_scale: Optional[Any] = None
    nice_options: Optional[str] = None
    outer_delims: Optional[bool] = None
    layout: Optional[Any] = None
    legacy_submatrix_names: bool = False
    legacy_format: bool = False
    label_rows: Optional[Sequence[Union[GELabelRowsSpec, Mapping[str, Any]]]] = None
    label_cols: Optional[Sequence[Union[GELabelColsSpec, Mapping[str, Any]]]] = None
    label_gap_mm: Optional[float] = 0.8
    variable_labels: Optional[Sequence[Any]] = None
    format_nrhs: bool = True
    decorators: Optional[Sequence[Any]] = None
    decorations: Optional[Sequence[Union[GEDecorationSpec, Mapping[str, Any]]]] = None
    pivot_locs: Optional[Sequence[Any]] = None
    text_annotations: Optional[Sequence[Any]] = None
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
        allowed = set(GEGridSpec.__dataclass_fields__.keys())
        kwargs = _filtered_dataclass_kwargs(
            d,
            spec_name="GEGridSpec",
            allowed=allowed,
            required="matrices",
            allow_extra=allow_extra,
        )
        return GEGridSpec(**kwargs)

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
    callouts: Optional[Sequence[Any]] = None
    array_names: Any = True
    fig_scale: Optional[Any] = None
    document_preamble: Optional[str] = None
    body_preamble: Optional[str] = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n"
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
    annotations: Optional[Sequence[Mapping[str, Any]]] = None

    @staticmethod
    def from_dict(d: Dict[str, Any], *, allow_extra: Optional[bool] = None) -> "QRGridSpec":
        allowed = set(QRGridSpec.__dataclass_fields__.keys())
        kwargs = _filtered_dataclass_kwargs(
            d,
            spec_name="QRGridSpec",
            allowed=allowed,
            required="matrices",
            allow_extra=allow_extra,
        )
        return QRGridSpec(**kwargs)

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


def _is_grid_coord(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and len(value) == 2


def _validate_grid_coord(value: Any, *, field: str, grid: Optional[Tuple[int, int]]) -> List[str]:
    if not _is_grid_coord(value):
        return [f"{field} must be a (row, col) grid coordinate"]
    try:
        row, col = int(value[0]), int(value[1])
    except Exception:
        return [f"{field} must contain integer row/col values"]
    if row < 0 or col < 0:
        return [f"{field} must be non-negative"]
    if grid is not None:
        nrows, ncols = grid
        if row >= nrows or col >= ncols:
            return [f"{field} {row, col} is outside matrix grid {grid}"]
    return []


def _validate_label_specs(
    specs: Optional[Sequence[Any]],
    *,
    field: str,
    allowed_sides: Sequence[str],
    grid: Optional[Tuple[int, int]],
    strict: bool,
) -> List[str]:
    errors: List[str] = []
    if specs is None:
        return errors
    allowed_keys = {"grid", "side", "labels", "overlay"}
    for idx, item in enumerate(specs):
        if not isinstance(item, Mapping):
            errors.append(f"{field}[{idx}] must be a mapping")
            continue
        if strict:
            extra = set(item) - allowed_keys
            if extra:
                errors.append(f"{field}[{idx}] has unknown field(s): {sorted(extra)}")
        if "grid" in item:
            errors.extend(_validate_grid_coord(item["grid"], field=f"{field}[{idx}].grid", grid=grid))
        side = str(item.get("side", allowed_sides[0])).strip().lower()
        if side not in allowed_sides:
            errors.append(f"{field}[{idx}].side must be one of {tuple(allowed_sides)}")
        if "labels" not in item:
            errors.append(f"{field}[{idx}] must include 'labels'")
    return errors


_GE_SPEC_ALLOWED_KEYS = {
    "grid",
    "entries",
    "rows",
    "cols",
    "labels",
    "overlay",
    "submatrix",
    "decorator",
    "background",
    "color",
    "bold",
    "outline",
    "padding_pt",
    "hlines",
    "vlines",
    "box",
}


_ANNOTATION_ALLOWED_KEYS = {
    "grid",
    "side",
    "labels",
    "overlay",
}


def _validate_annotation_specs(
    annotations: Optional[Sequence[Any]],
    *,
    grid: Optional[Tuple[int, int]],
    strict: bool,
    field: str = "annotations",
) -> List[str]:
    errors: List[str] = []
    if annotations is None:
        return errors
    for idx, item in enumerate(annotations):
        if not isinstance(item, Mapping):
            errors.append(f"{field}[{idx}] must be a mapping")
            continue
        if strict:
            extra = set(item) - _ANNOTATION_ALLOWED_KEYS
            if extra:
                errors.append(f"{field}[{idx}] has unknown field(s): {sorted(extra)}")
        if "grid" in item:
            errors.extend(_validate_grid_coord(item["grid"], field=f"{field}[{idx}].grid", grid=grid))
        elif grid != (1, 1):
            errors.append(f"{field}[{idx}] requires grid=(row, col) for multi-block grids")
        if "labels" not in item:
            errors.append(f"{field}[{idx}] must include 'labels'")
        if "side" in item:
            side = str(item["side"]).strip().lower()
            if side not in {"left", "right", "above", "below"}:
                errors.append(f"{field}[{idx}].side must be left/right/above/below")
    return errors


def _validate_ge_decorations(
    decorations: Optional[Sequence[Any]],
    *,
    grid: Optional[Tuple[int, int]],
    strict: bool,
    field: str = "decorations",
) -> List[str]:
    errors: List[str] = []
    if decorations is None:
        return errors
    for idx, item in enumerate(decorations):
        if not isinstance(item, Mapping):
            errors.append(f"{field}[{idx}] must be a mapping")
            continue
        if strict:
            extra = set(item) - _GE_SPEC_ALLOWED_KEYS
            if extra:
                errors.append(f"{field}[{idx}] has unknown field(s): {sorted(extra)}")
        if "grid" in item:
            errors.extend(_validate_grid_coord(item["grid"], field=f"{field}[{idx}].grid", grid=grid))
        elif grid != (1, 1):
            errors.append(f"{field}[{idx}] requires grid=(row, col) for multi-block grids")
        if "decorator" in item and not callable(item["decorator"]):
            errors.append(f"{field}[{idx}].decorator must be callable")
        if "side" in item:
            side = str(item["side"]).strip().lower()
            if side not in {"left", "right", "above", "below"}:
                errors.append(f"{field}[{idx}].side must be left/right/above/below")
    return errors


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


def _spec_mapping(spec: Any, *, name: str) -> Tuple[Optional[Mapping[str, Any]], List[str]]:
    if isinstance(spec, Mapping):
        return spec, []
    if is_dataclass(spec) and not isinstance(spec, type):
        return asdict(spec), []
    return None, [f"{name} must be a mapping or typed spec object"]


def _validated_spec_mapping_and_matrices(
    spec: Any,
    *,
    name: str,
    factory: Callable[..., Any],
    strict: bool,
    missing_message: str,
) -> Tuple[Optional[Mapping[str, Any]], Optional[Any], List[str]]:
    mapping, errors = _spec_mapping(spec, name=name)
    if mapping is None:
        return None, None, errors
    try:
        factory(dict(mapping), allow_extra=not strict)
    except Exception as exc:
        errors.append(str(exc))
    mats = mapping.get("matrices")
    if mats is None:
        if not any("requires 'matrices'" in e for e in errors):
            errors.append(missing_message)
        return mapping, None, errors
    return mapping, mats, errors


def validate_ge_spec(spec: Any, *, strict: bool = True) -> List[str]:
    """Validate a GE spec dict and return a list of errors.

    This is intended as a lightweight preflight before rendering.
    """
    mapping, mats, errors = _validated_spec_mapping_and_matrices(
        spec,
        name="GE spec",
        factory=GEGridSpec.from_dict,
        strict=strict,
        missing_message="GE spec requires 'matrices'",
    )
    if mapping is None or mats is None:
        return errors
    grid = _grid_size(mats)
    errors.extend(_validate_grid_matrices(mats))
    errors.extend(
        _validate_label_specs(
            mapping.get("label_rows"),
            field="label_rows",
            allowed_sides=("above", "below"),
            grid=grid,
            strict=strict,
        )
    )
    errors.extend(
        _validate_label_specs(
            mapping.get("label_cols"),
            field="label_cols",
            allowed_sides=("left", "right"),
            grid=grid,
            strict=strict,
        )
    )
    errors.extend(_validate_ge_decorations(mapping.get("decorations"), grid=grid, strict=strict))
    return errors


def validate_qr_spec(spec: Any, *, strict: bool = True) -> List[str]:
    """Validate a QR spec dict and return a list of errors."""
    mapping, mats, errors = _validated_spec_mapping_and_matrices(
        spec,
        name="QR spec",
        factory=QRGridSpec.from_dict,
        strict=strict,
        missing_message="QR spec requires 'matrices'",
    )
    if mapping is None or mats is None:
        return errors
    grid = _grid_size(mats)
    annotations = mapping.get("annotations")
    if annotations is not None and (isinstance(annotations, (str, bytes)) or not isinstance(annotations, Sequence)):
        errors.append("annotations must be a sequence of mappings")
    elif annotations is not None:
        errors.extend(_validate_annotation_specs(annotations, grid=grid, strict=strict, field="annotations"))
    decorators = mapping.get("decorators")
    if decorators is not None and (isinstance(decorators, (str, bytes)) or not isinstance(decorators, Sequence)):
        errors.append("decorators must be a sequence of mappings")
    elif decorators is not None:
        errors.extend(_validate_ge_decorations(decorators, grid=grid, strict=strict, field="decorators"))
    callouts = mapping.get("callouts")
    if callouts is not None and (isinstance(callouts, (str, bytes)) or not isinstance(callouts, Sequence)):
        errors.append("callouts must be a sequence of mappings")
    errors.extend(_validate_grid_matrices(mats))
    return errors
