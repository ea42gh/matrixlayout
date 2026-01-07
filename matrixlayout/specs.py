from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple


@dataclass(frozen=True)
class GELayoutSpec:
    """Serializable layout spec for GE/GE-grid figures.

    All fields are optional. When a field is ``None`` it has no effect.
    """

    nice_options: Optional[Any] = None
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
