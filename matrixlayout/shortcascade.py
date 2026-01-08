"""Formatting helpers for the LaTeX ``cascade`` package.

This module is intentionally **layout-only**. It does not compute row-reduction,
RREF, pivots, free variables, or substitutions.

Instead, it formats a *back-substitution trace* (typically produced by an
algorithmic package) into TeX lines suitable for inclusion in the migrated
``BACKSUBST_TEMPLATE``.

The legacy ``nicematrix.py`` implementation generated nested ``\\ShortCascade``
expressions programmatically, then injected them into the Jinja template
verbatim. ``matrixlayout`` preserves that separation:

- Algorithmic package: produces the trace (what the equations are)
- matrixlayout: formats the trace (how the equations look)
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping, Sequence, Tuple, TypedDict, Union, cast

from .formatting import latexify


class BackSubStep(TypedDict, total=False):
    """One back-substitution step.

    Fields may be provided as strings (recommended for Julia interop) or as
    symbolic objects (e.g. SymPy expressions / Eq objects). ``matrixlayout``
    will only convert such objects to TeX representation.
    """

    raw: Any
    substituted: Any
    lhs: Any
    rhs: Any


class BackSubTrace(TypedDict, total=False):
    """Back-substitution trace description.

    - ``base``: free-variable assignment(s), either as a TeX string, or as an
      iterable of (variable, parameter) pairs.
    - ``steps``: ordered steps. Each step can be a dict (BackSubStep) or a
      2-tuple/list of (raw, substituted).

    The trace should be ordered from *inner* to *outer* in the resulting
    ``\\ShortCascade`` nesting. In typical echelon back-substitution this is
    bottom-to-top.
    """

    base: Any
    steps: Any
    meta: Any


def _latexify(x: Any) -> str:
    """Convert an object to a TeX-ish string without performing computation."""
    if x is None:
        return ""
    return latexify(x)


def _normalize_base(base: Any) -> str:
    """Normalize the ``base`` field to a single TeX string."""

    if isinstance(base, str):
        return base

    # Allow a list/tuple of (var, param) pairs.
    if isinstance(base, (list, tuple)):
        pairs: list[str] = []
        for item in base:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                v, p = item
                pairs.append(f"{_latexify(v)} = {_latexify(p)}")
            else:
                pairs.append(_latexify(item))
        return ", ".join(pairs)

    return _latexify(base)


def _normalize_steps(steps: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if steps is None:
        return out

    if not isinstance(steps, (list, tuple)):
        raise TypeError("trace['steps'] must be a sequence")

    for step in steps:
        raw: Any
        sub: Any
        if isinstance(step, Mapping):
            raw = step.get("raw", step.get("lhs"))
            sub = step.get("substituted", step.get("rhs"))
        elif isinstance(step, (list, tuple)) and len(step) == 2:
            raw, sub = step
        else:
            raise TypeError(
                "Each step must be a mapping with raw/substituted (or lhs/rhs) or a 2-tuple"
            )

        out.append((_latexify(raw), _latexify(sub)))
    return out


def normalize_backsub_trace(trace: Union[BackSubTrace, Mapping[str, Any], Sequence[Any]]) -> tuple[str, list[tuple[str, str]]]:
    """Normalize a back-substitution trace into ``(base, steps)``.

    Accepted forms:
    - mapping with keys ``base`` and ``steps`` (recommended)
    - 2-sequence ``(base, steps)``
    """

    if isinstance(trace, Mapping):
        base = _normalize_base(trace.get("base", ""))
        steps = _normalize_steps(trace.get("steps", []))
        return base, steps

    if isinstance(trace, (list, tuple)) and len(trace) == 2:
        base, steps = trace
        return _normalize_base(base), _normalize_steps(steps)

    raise TypeError("trace must be a mapping with keys 'base' and 'steps' or a 2-sequence")


def mk_shortcascade_lines(trace: Union[BackSubTrace, Mapping[str, Any], Sequence[Any]]) -> list[str]:
    """Format a back-substitution trace as nested ``\\ShortCascade`` lines.

    Returns a list of TeX strings. The caller typically injects these into a
    Jinja template via a simple loop (one line per list element), mirroring the
    legacy ``nicematrix.py`` behavior.
    """

    base, steps = normalize_backsub_trace(trace)
    n = len(steps)

    # No steps: emit just the boxed base assignment.
    if n == 0:
        if not base:
            return []
        return [rf"{{$\boxed{{ {base} }}$}}%"]

    lines: list[str] = [r"{\ShortCascade%"] * n
    lines.append(rf"{{$\boxed{{ {base} }}$}}%")

    for raw, substituted in steps:
        lines.append(rf"{{${raw}$}}%")
        lines.append(rf"{{$\;\Rightarrow\;\boxed{{{substituted}}}$}}%")
        lines.append(r"}%")

    return lines
