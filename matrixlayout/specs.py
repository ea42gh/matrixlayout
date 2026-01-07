from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


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
    submatrix_locs: Optional[Sequence[Any]] = None
    submatrix_names: Optional[Sequence[Any]] = None
    pivot_locs: Optional[Sequence[Any]] = None
    txt_with_locs: Optional[Sequence[Any]] = None
    rowechelon_paths: Optional[Sequence[Any]] = None
    callouts: Optional[Sequence[Any]] = None

    landscape: Optional[bool] = None
    create_cell_nodes: Optional[bool] = None

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
