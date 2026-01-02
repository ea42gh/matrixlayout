"""
Gaussian-elimination (GE) figure template helpers.

This module is intentionally *layout-only*: it populates the GE Jinja2 template and
(optionally) renders via the strict boundary call in :func:`matrixlayout.render.render_svg`.

The GE template uses nicematrix (NiceArray family) for matrix typesetting and TikZ
for annotations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple, Union, Any

from .jinja_env import render_template
from .render import render_svg as _render_svg


_ALLOWED_ARRAY_ENVS = {
    "NiceArray",
    "pNiceArray",
    "bNiceArray",
    "BNiceArray",
    "vNiceArray",
    "VNiceArray",
}


def _normalize_mat_format(mat_format: str) -> str:
    """Normalize a LaTeX array preamble.

    Accepts either ``"cc"`` or ``"{cc}"`` and returns the bare preamble (``"cc"``).
    """
    s = (mat_format or "").strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    return s


def _normalize_mat_rep(mat_rep: str) -> str:
    r"""Normalize a matrix body string.

    Jupyter users occasionally write Python strings like ``"1 & 0 \ 0 & 1"``
    (a single backslash followed by whitespace). TeX expects a row separator ``\\``.
    This normalizer converts ``\`` followed by whitespace into ``\\`` + that whitespace,
    while leaving already-correct ``\\`` sequences intact.
    """
    if mat_rep is None:
        return ""
    s = str(mat_rep)
    # Replace a single backslash not already doubled, followed by whitespace, with a doubled backslash.
    # Pattern: backslash not preceded by backslash, not followed by backslash, followed by whitespace.
    import re
    return re.sub(r'(?<!\\)\\(?!\\)(\s+)', r'\\\\\1', s)


def _normalize_fig_scale(fig_scale: Optional[Union[float, int, str]]) -> Tuple[str, str]:
    r"""Normalize ``fig_scale`` to a legacy TeX wrapper pair (open, close).

    - ``None`` or ``1`` => ("", "")
    - number => (r"\scalebox{<v>}{%", "}")
    - string => used verbatim as open wrapper; close is "" (advanced use)
    """
    if fig_scale is None:
        return "", ""
    if isinstance(fig_scale, (int, float)):
        if float(fig_scale) == 1.0:
            return "", ""
        return rf"\scalebox{{{fig_scale}}}{{%", "}"
    # advanced: caller provides their own TeX wrapper
    s = str(fig_scale)
    return s, ""


def _normalize_submatrix_locs(
    submatrix_locs: Optional[Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]]
) -> List[Tuple[str, str, str]]:
    r"""Normalize submatrix location descriptors to ``(options, first, last)`` triples.

    Supported input shapes:
    - ``[(opts, "(1-1)(2-2)"), ...]``
    - ``[(opts, "(1-1)", "(2-2)"), ...]``
    - ``[("", "(1-1)(2-2)"), ...]``

    Output ``first``/``last`` are returned *without* parentheses (e.g., ``"1-1"``),
    ready for emission as: ``\SubMatrix[<options>](<first>)(<last>)``.
    """
    if not submatrix_locs:
        return []
    out: List[Tuple[str, str, str]] = []
    import re

    for item in submatrix_locs:
        if len(item) == 2:
            opts, loc = item
            m = re.findall(r"\(\s*([^)]+?)\s*\)", str(loc))
            if len(m) != 2:
                raise ValueError(f"submatrix_locs entry must contain two '(r-c)' tokens: {item!r}")
            first, last = m[0], m[1]
        elif len(item) == 3:
            opts, first, last = item
            first = str(first).strip()
            last = str(last).strip()
            # Strip optional parentheses
            if first.startswith("(") and first.endswith(")"):
                first = first[1:-1].strip()
            if last.startswith("(") and last.endswith(")"):
                last = last[1:-1].strip()
        else:
            raise ValueError(f"submatrix_locs entry must be a 2- or 3-tuple, got: {item!r}")

        out.append((str(opts).strip(), first, last))
    return out


@dataclass(frozen=True)
class GEContext:
    """Context for populating ``ge.tex.j2``."""

    mat_rep: str
    mat_format: str

    # Display environment (nicematrix). Default is parentheses.
    array_env: str = "pNiceArray"

    # Optional TeX fragments/hooks
    preamble: str = ""
    codebefore: Sequence[str] = ()
    codeafter: Sequence[str] = ()

    # nicematrix / TikZ annotation hooks
    submatrix_locs: Sequence[Union[Tuple[str, str], Tuple[str, str, str]]] = ()
    submatrix_names: Sequence[str] = ()
    pivot_locs: Sequence[Tuple[str, str]] = ()  # (fit_target, extra_style)
    txt_with_locs: Sequence[Tuple[str, str, str]] = ()  # (coord, text, style)
    rowechelon_paths: Sequence[str] = ()

    # Outer wrapper options
    fig_scale: Optional[Union[float, int, str]] = None
    landscape: bool = False


def ge_tex(
    *,
    mat_rep: str,
    mat_format: str,
    array_env: str = "pNiceArray",
    preamble: str = "",
    codebefore: Optional[Sequence[str]] = None,
    codeafter: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[str, str]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[str, str, str]]] = None,
    rowechelon_paths: Optional[Sequence[str]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: bool = False,
) -> str:
    """Populate the GE template and return TeX.

    Parameters
    ----------
    mat_rep:
        The NiceArray body (rows separated by ``\\``; columns separated by ``&``).
    mat_format:
        The array preamble (e.g., ``"cc|c"``). Braces are optional (``"{cc}"`` OK).
    array_env:
        nicematrix environment name. Default is ``"pNiceArray"`` for parentheses.
        Common alternatives: ``"bNiceArray"`` (brackets), ``"NiceArray"`` (no delimiters).
    """
    env = (array_env or "").strip()
    if env not in _ALLOWED_ARRAY_ENVS:
        raise ValueError(f"array_env must be one of {sorted(_ALLOWED_ARRAY_ENVS)}, got {array_env!r}")

    mat_format_norm = _normalize_mat_format(mat_format)
    mat_rep_norm = _normalize_mat_rep(mat_rep)
    scale_open, scale_close = _normalize_fig_scale(fig_scale)
    subm_triples = _normalize_submatrix_locs(submatrix_locs)

    ctx = dict(
        array_env=env,
        mat_format=mat_format_norm,
        mat_rep=mat_rep_norm,
        preamble=preamble or "",
        codebefore=list(codebefore or []),
        codeafter=list(codeafter or []),
        submatrix_triples=subm_triples,
        submatrix_names=list(submatrix_names or []),
        pivot_locs=list(pivot_locs or []),
        txt_with_locs=list(txt_with_locs or []),
        rowechelon_paths=list(rowechelon_paths or []),
        scale_open=scale_open,
        scale_close=scale_close,
        landscape=bool(landscape),
    )
    return render_template("ge.tex.j2", ctx)


def ge_svg(
    *,
    mat_rep: str,
    mat_format: str,
    array_env: str = "pNiceArray",
    preamble: str = "",
    codebefore: Optional[Sequence[str]] = None,
    codeafter: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[str, str]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[str, str, str]]] = None,
    rowechelon_paths: Optional[Sequence[str]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: bool = False,
    toolchain_name: Optional[str] = None,
) -> str:
    """Render the GE template to SVG (strict rendering boundary)."""
    tex = ge_tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        array_env=array_env,
        preamble=preamble,
        codebefore=codebefore,
        codeafter=codeafter,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
        rowechelon_paths=rowechelon_paths,
        fig_scale=fig_scale,
        landscape=landscape,
    )
    if toolchain_name:
        return _render_svg(tex, toolchain_name=toolchain_name)
    return _render_svg(tex)
