r"""
GE (Gaussian Elimination) template helpers.

This module generates TeX for the GE "matrix-of-matrices" layout. In this layout,
outer delimiters (and block delimiters) are drawn with `nicematrix`'s `\SubMatrix`
inside `\CodeAfter`.

Target: current `nicematrix`
----------------------------
The `\SubMatrix` command syntax (as of current nicematrix releases) uses a single
mandatory argument of the form `({i-j}{k-l})` followed by an *optional* key-value
list *after* the argument: `\SubMatrix({1-1}{3-3})[name=...]`.

Therefore, this module normalizes submatrix locations into `(options, span)` where
`span` is a string like `"{1-1}{2-2}"`, and the template emits:
    `\SubMatrix({span})[options]`
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union, Any

from .jinja_env import render_template
from .render import render_svg as _render_svg


def _normalize_mat_format(mat_format: str) -> str:
    """Normalize a LaTeX array preamble (accepts ``"cc"`` or ``"{cc}"``)."""
    s = (mat_format or "").strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    return s


def _normalize_mat_rep(mat_rep: str) -> str:
    r"""Normalize the matrix body.

    If a user accidentally writes a single backslash followed by whitespace
    instead of TeX's row separator ``\\``, convert it to ``\\``.
    """
    if mat_rep is None:
        return ""
    s = str(mat_rep)
    import re
    return re.sub(r"(?<!\\)\\(?!\\)(\s+)", r"\\\\\1", s)


def _guess_shape_from_mat_rep(mat_rep: str) -> Tuple[int, int]:
    """Best-effort (nrows, ncols) inferred from a TeX body like ``a & b \\\\ c & d``."""
    body = _normalize_mat_rep(mat_rep)
    rows = [r.strip() for r in body.split(r"\\") if r.strip()]
    nrows = len(rows) if rows else 0
    ncols = 0
    for r in rows:
        ncols = max(ncols, r.count("&") + 1)
    return nrows, ncols


def _normalize_submatrix_locs(
    submatrix_locs: Optional[
        Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]
    ]
) -> List[Tuple[str, str]]:
    r"""Normalize submatrix descriptors to ``(options, span)``.

    Accepted input forms:
    - ``(opts, "{1-1}{2-2}")`` (legacy span encoding)
    - ``(opts, "(1-1)(2-2)")`` (two parenthesized tokens)
    - ``(opts, "(1-1)", "(2-2)")`` (explicit first/last, with parentheses)
    - ``(opts, "1-1", "2-2")`` (explicit first/last)

    Output span is always ``"{first}{last}"`` (including braces) and is meant to be
    used inside ``\SubMatrix({span})``.
    """
    if not submatrix_locs:
        return []
    out: List[Tuple[str, str]] = []
    import re

    for item in submatrix_locs:
        if len(item) == 2:
            opts, loc = item
            loc_s = str(loc).strip()

            if "{" in loc_s and "}" in loc_s:
                # legacy "{r1-c1}{r2-c2}"
                parts = re.findall(r"\{\s*([^}]+?)\s*\}", loc_s)
                if len(parts) != 2:
                    raise ValueError(f"Bad legacy span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]
            else:
                # "(r1-c1)(r2-c2)"
                parts = re.findall(r"\(\s*([^)]+?)\s*\)", loc_s)
                if len(parts) != 2:
                    raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]

        elif len(item) == 3:
            opts, first, last = item
            first = str(first).strip()
            last = str(last).strip()
            if first.startswith("(") and first.endswith(")"):
                first = first[1:-1].strip()
            if last.startswith("(") and last.endswith(")"):
                last = last[1:-1].strip()
        else:
            raise ValueError(f"submatrix_locs entry must be a 2- or 3-tuple, got: {item!r}")

        span = f"{{{first}}}{{{last}}}"
        out.append((str(opts).strip(), span))

    return out


def ge_tex(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: str = "vlines-in-sub-matrix = I",
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[str, str]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[str, str, str]]] = None,
    rowechelon_paths: Optional[Sequence[str]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: bool = False,
    create_cell_nodes: bool = True,
    outer_delims: bool = False,
    outer_delims_name: str = "A0x0",
    outer_delims_span: Optional[Tuple[int, int]] = None,
) -> str:
    r"""Populate the GE template and return TeX."""
    mat_format_norm = _normalize_mat_format(mat_format)
    mat_rep_norm = _normalize_mat_rep(mat_rep)

    # figure scale: the GE template currently supports TeX wrappers in the template itself
    fig_scale_open = fig_scale_close = ""
    if fig_scale is not None:
        if isinstance(fig_scale, (int, float)) and float(fig_scale) != 1.0:
            fig_scale_open = rf"\scalebox{{{fig_scale}}}{{%"
            fig_scale_close = "}"
        elif isinstance(fig_scale, str) and fig_scale.strip():
            fig_scale_open = fig_scale
            fig_scale_close = ""

    sub_spans = _normalize_submatrix_locs(submatrix_locs)

    if outer_delims and not sub_spans:
        if outer_delims_span is None:
            outer_delims_span = _guess_shape_from_mat_rep(mat_rep_norm)
        nrows, ncols = outer_delims_span
        if nrows <= 0 or ncols <= 0:
            raise ValueError("Could not infer outer_delims_span; pass outer_delims_span=(nrows,ncols).")
        sub_spans.append((f"name={outer_delims_name}", f"{{1-1}}{{{nrows}-{ncols}}}"))

    ctx = dict(
        extension=extension or "",
        preamble=preamble or "",
        fig_scale_open=fig_scale_open,
        fig_scale_close=fig_scale_close,
        landscape=bool(landscape),
        nice_options=(nice_options or "").strip(),
        mat_format=mat_format_norm,
        create_cell_nodes=bool(create_cell_nodes),
        codebefore=list(codebefore or []),
        mat_rep=mat_rep_norm,
        submatrix_spans=sub_spans,   # list[(opts, "{i-j}{k-l}")]
        submatrix_names=list(submatrix_names or []),
        pivot_locs=list(pivot_locs or []),
        txt_with_locs=list(txt_with_locs or []),
        rowechelon_paths=list(rowechelon_paths or []),
    )
    return render_template("ge.tex.j2", ctx)


def ge_svg(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: str = "vlines-in-sub-matrix = I",
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[str, str]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[str, str, str]]] = None,
    rowechelon_paths: Optional[Sequence[str]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: bool = False,
    create_cell_nodes: bool = True,
    outer_delims: bool = False,
    outer_delims_name: str = "A0x0",
    outer_delims_span: Optional[Tuple[int, int]] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
) -> str:
    """Render the GE template to SVG (strict rendering boundary)."""
    tex = ge_tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        preamble=preamble,
        extension=extension,
        nice_options=nice_options,
        codebefore=codebefore,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
        rowechelon_paths=rowechelon_paths,
        fig_scale=fig_scale,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        outer_delims=outer_delims,
        outer_delims_name=outer_delims_name,
        outer_delims_span=outer_delims_span,
    )
    if toolchain_name:
        return _render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
    return _render_svg(tex, crop=crop, padding=padding)
