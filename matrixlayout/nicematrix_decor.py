r"""Descriptor-based nicematrix decorations.

This module provides *data-only* decoration descriptors intended to be rendered
into TikZ snippets by layout routines (e.g., :func:`matrixlayout.ge.ge_tex`).

Why descriptors?
----------------
For migration and Julia interop, decorations should not require constructing TeX
strings at the call site. Instead, callers provide structured data (plain dicts)
that can be serialized and generated from other languages.

The renderer in this module converts those descriptors into TikZ commands that
attach to nicematrix submatrix delimiter nodes created by ``\SubMatrix``.

Nicematrix delimiter nodes
--------------------------
When a submatrix delimiter is declared as ``\SubMatrix(...)[name=Foo]``,
``nicematrix`` creates (at least) the nodes ``Foo-left``, ``Foo``, and
``Foo-right``. The ``Foo-left`` / ``Foo-right`` nodes correspond to the left
and right delimiters (parentheses/brackets). These are the intended attachment
points for QR-style callouts.

This module does not import ``nicematrix``; it only emits TeX strings.

"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple, TypedDict, Union


Side = Literal["left", "right", "auto"]
Anchor = Literal["north", "south", "center", "top", "bottom", "mid"]


class DelimCalloutDict(TypedDict, total=False):
    """JSON-serializable descriptor for a delimiter-attached callout."""

    # Required
    name: str
    label: str

    # Optional
    side: Side
    anchor: Anchor
    angle_deg: float
    length_mm: float
    color: str
    line_width_pt: float
    tip: str
    extra_style: str
    math_mode: bool


@dataclass(frozen=True)
class DelimCallout:
    """Delimiter-attached callout descriptor.

    This class is a convenience for Python callers. The renderer accepts either
    :class:`DelimCallout` or the JSON-serializable :class:`DelimCalloutDict`.
    """

    name: str
    label: str
    side: Side = "auto"
    anchor: Anchor = "top"
    angle_deg: float = 25.0
    length_mm: float = 10.0
    color: str = "blue"
    line_width_pt: float = 0.35
    # Uses arrows.meta. Templates that render these callouts should include it.
    tip: str = r"-{Stealth[length=2.4mm]}"
    extra_style: str = ""
    math_mode: bool = True


CalloutLike = Union[DelimCallout, DelimCalloutDict, Mapping[str, Any]]


def _coerce_callout(obj: CalloutLike) -> DelimCallout:
    """Coerce a callout-like object into :class:`DelimCallout`."""

    if isinstance(obj, DelimCallout):
        return obj
    if isinstance(obj, Mapping):
        d = dict(obj)
        try:
            return DelimCallout(
                name=str(d["name"]),
                label=str(d["label"]),
                side=str(d.get("side", "auto")),
                anchor=str(d.get("anchor", "top")),
                angle_deg=float(d.get("angle_deg", 25.0)),
                length_mm=float(d.get("length_mm", 10.0)),
                color=str(d.get("color", "blue")),
                line_width_pt=float(d.get("line_width_pt", 0.35)),
                tip=str(d.get("tip", r"-{Stealth[length=2.4mm]}")),
                extra_style=str(d.get("extra_style", "")),
                math_mode=bool(d.get("math_mode", True)),
            )
        except KeyError as e:
            raise ValueError(f"Callout descriptor missing required key: {e}") from e
    raise TypeError(f"Unsupported callout type: {type(obj)!r}")


def _norm_anchor(anchor: Anchor) -> Literal["north", "south", "center"]:
    a = str(anchor).strip().lower()
    if a in {"north", "top"}:
        return "north"
    if a in {"south", "bottom"}:
        return "south"
    if a in {"center", "mid"}:
        return "center"
    raise ValueError(f"Invalid anchor: {anchor!r} (expected top/bottom/center)")


def _infer_side(name: str, side: Side) -> Literal["left", "right"]:
    s = str(side).strip().lower()
    if s in {"left", "right"}:
        return s  # type: ignore[return-value]
    # Heuristic for GE: E* blocks are on the left; A* blocks on the right.
    nm = str(name)
    if nm.startswith("E"):
        return "left"
    if nm.startswith("A"):
        return "right"
    # Fall back to right (typical for labels of the main matrix).
    return "right"


def render_delim_callout(callout: CalloutLike) -> str:
    r"""Render a :class:`DelimCallout` into a TikZ ``\draw`` command.

    The returned string is intended to be inserted *inside* a ``tikzpicture``.

    Semantics
    ---------
    - Arrow head attaches to a nicematrix delimiter node:
      ``(<name>-left.<anchor>)`` or ``(<name>-right.<anchor>)``.
    - Arrow tail is offset by (angle, length). All callouts with the same
      ``angle_deg`` and ``length_mm`` produce parallel arrows.
    - Label is placed at the tail (start) of the arrow.

    Angle convention
    ----------------
    ``angle_deg`` is the acute angle above the x-axis used for the *left*
    callouts (arrow points toward +x). Right callouts mirror it as
    ``180 - angle_deg``.
    """

    c = _coerce_callout(callout)
    which = _infer_side(c.name, c.side)
    anch = _norm_anchor(c.anchor)

    delim_node = f"{c.name}-{'left' if which == 'left' else 'right'}"
    head = f"({delim_node}.{anch})"

    # Mirror direction for right-side callouts.
    theta = float(c.angle_deg) if which == "left" else (180.0 - float(c.angle_deg))

    # Place tail at head + (theta+180 : length).
    tail = rf"($ {head} + ({theta + 180.0:.6f}:{float(c.length_mm)}mm) $)"

    # Label anchor: extend outward from the matrix.
    node_anchor = "east" if which == "left" else "west"

    label = c.label
    if c.math_mode:
        label = rf"$ {label} $"

    # Build draw options.
    opts: List[str] = [
        f"draw={c.color}",
        f"text={c.color}",
        f"line width={float(c.line_width_pt)}pt",
        c.tip,
    ]
    if c.extra_style.strip():
        opts.append(c.extra_style.strip().strip(","))

    opt_str = ", ".join(opts)

    # NOTE: This string is inserted verbatim inside a tikzpicture by the GE
    # template. It must therefore begin with a single TeX control sequence
    # "\\draw". Do not double-escape backslashes here; emitting "\\\\draw" would
    # cause LaTeX to interpret the first "\\" as a newline command, and the
    # remaining "draw" tokens would render as plain text.
    # TikZ does not recognize bare keys like `east`/`west` in node options.
    # Use explicit anchors so the label text sits outside the matrix while the
    # arrow tail stays at the computed point.
    return rf"\draw[{opt_str}] {tail} node[anchor={node_anchor}] {{{label}}} -- {head};"


def render_delim_callouts(
    callouts: Sequence[CalloutLike],
    *,
    available_names: Optional[Iterable[str]] = None,
    strict: bool = True,
) -> List[str]:
    """Render multiple callouts, optionally validating submatrix names."""

    avail = set(available_names or []) if available_names is not None else None

    out: List[str] = []
    for obj in callouts or []:
        c = _coerce_callout(obj)
        if avail is not None and c.name not in avail:
            msg = f"Callout references unknown SubMatrix name {c.name!r}. Available: {sorted(avail)}"
            if strict:
                raise ValueError(msg)
            continue
        out.append(render_delim_callout(c))
    return out


def infer_ge_layer_callouts(
    matrices: Sequence[Sequence[Any]],
    *,
    include_A: bool = True,
    include_E: bool = True,
    label_A: str = r"A_{%d}",
    label_E: str = r"E_{%d}",
    **style: Any,
) -> List[DelimCalloutDict]:
    """Build callout descriptors for a GE-style 2-column matrix stack.

    Parameters
    ----------
    matrices:
        The GE "matrix-of-matrices" stack as consumed by :func:`matrixlayout.ge.ge_grid_tex`,
        typically ``[[None, A0], [E1, A1], [E2, A2], ...]``.

    Returns
    -------
    list[dict]
        A list of :class:`DelimCalloutDict` with names matching ``ge_grid_tex``'s
        naming convention (A0, E1, A1, ...).

    Notes
    -----
    The returned callouts use only primitives and are suitable for Julia interop.
    Extra style keys are forwarded into each callout descriptor (e.g. ``angle_deg``,
    ``length_mm``, ``color``).
    """

    layers = list(matrices or [])
    out: List[DelimCalloutDict] = []

    for br, row in enumerate(layers):
        # Column role naming matches ge_grid_tex when n_block_cols == 2.
        if include_A:
            out.append(
                {
                    "name": f"A{br}",
                    "label": (label_A % br) if "%d" in label_A else label_A,
                    "side": "right",
                    **style,
                }
            )

        if include_E and row and len(row) >= 1 and row[0] is not None:
            out.append(
                {
                    "name": f"E{br}",
                    "label": (label_E % br) if "%d" in label_E else label_E,
                    "side": "left",
                    **style,
                }
            )

    return out
