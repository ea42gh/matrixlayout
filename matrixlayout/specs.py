"""Layout spec dataclasses.

The migration replaces the legacy, stateful ``itikz.nicematrix.MatrixGridLayout``
with explicit, serializable layout specs.

This module introduces the first such spec: :class:`GELayoutSpec`.

Design goals
------------
- Data-only objects (no LaTeX toolchain behavior).
- JSON-friendly: ``from_dict`` accepts plain mappings.
- Backward compatible: callers can continue passing the older ``dict``-specs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class GELayoutSpec:
    """Explicit layout/decorations spec for :func:`matrixlayout.ge.ge_tex`.

    This spec is intentionally a thin wrapper over the existing keyword
    arguments accepted by ``ge_tex``. The goal is to provide a stable,
    structured input object that can be constructed from Python or other
    languages (via JSON), while keeping the template renderer unchanged.

    Only fields set to non-None values are forwarded into ``ge_tex``.
    """

    # nicematrix / template behavior
    nice_options: Optional[str] = None
    codebefore: Optional[Sequence[str]] = None
    submatrix_locs: Optional[Sequence[Any]] = None
    submatrix_names: Optional[Sequence[str]] = None

    # Decorations rendered in CodeAfter's tikzpicture
    pivot_locs: Optional[Sequence[Any]] = None
    txt_with_locs: Optional[Sequence[Any]] = None
    rowechelon_paths: Optional[Sequence[str]] = None
    callouts: Optional[Sequence[Any]] = None

    # Template toggles
    landscape: Optional[bool] = None
    create_cell_nodes: Optional[bool] = None
    outer_delims: Optional[bool] = None
    outer_delims_name: Optional[str] = None
    outer_delims_span: Optional[Tuple[int, int]] = None

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "GELayoutSpec":
        """Coerce a plain mapping into :class:`GELayoutSpec`.

        Unknown keys are ignored so callers can pass supersets (e.g. QR specs)
        without breaking GE.
        """

        if not isinstance(d, Mapping):
            raise TypeError(f"GELayoutSpec.from_dict expects a mapping, got {type(d)!r}")

        def _get(key: str, default=None):
            return d.get(key, default)

        return cls(
            nice_options=_get("nice_options"),
            codebefore=_get("codebefore"),
            submatrix_locs=_get("submatrix_locs"),
            submatrix_names=_get("submatrix_names"),
            pivot_locs=_get("pivot_locs"),
            txt_with_locs=_get("txt_with_locs"),
            rowechelon_paths=_get("rowechelon_paths"),
            callouts=_get("callouts"),
            landscape=_get("landscape"),
            create_cell_nodes=_get("create_cell_nodes"),
            outer_delims=_get("outer_delims"),
            outer_delims_name=_get("outer_delims_name"),
            outer_delims_span=_get("outer_delims_span"),
        )

    def to_ge_kwargs(self) -> dict[str, Any]:
        """Convert to a kwargs dict consumable by :func:`matrixlayout.ge.ge_tex`.

        The returned mapping contains only non-None fields.
        """

        out: dict[str, Any] = {}
        for k in (
            "nice_options",
            "codebefore",
            "submatrix_locs",
            "submatrix_names",
            "pivot_locs",
            "txt_with_locs",
            "rowechelon_paths",
            "callouts",
            "landscape",
            "create_cell_nodes",
            "outer_delims",
            "outer_delims_name",
            "outer_delims_span",
        ):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        return out
