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


def _julia_str(x: Any) -> str:
    """Normalize Julia/PythonCall/PyCall "string-like" values to plain strings.

    Julia Symbols frequently stringify to ``":name"`` (e.g. ``:tight``).
    For interop, strip a single leading colon.
    """
    if x is None:
        return ""
    s = str(x).strip()
    if s.startswith(":"):
        s = s[1:]
    return s


def _coord_token(x: Any) -> str:
    """Convert a coordinate into an ``i-j`` token (1-based indices).

    Accepted forms:
    - ``"(i-j)"`` or ``"i-j"``
    - ``(i, j)`` / ``[i, j]``
    """
    if isinstance(x, (tuple, list)) and len(x) == 2:
        i, j = x
        return f"{int(i)}-{int(j)}"
    s = str(x).strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    return s


def _coord_paren(x: Any) -> str:
    """Convert a coordinate into a parenthesized form ``(i-j)``."""
    tok = _coord_token(x)
    if tok.startswith("(") and tok.endswith(")"):
        return tok
    return f"({tok})"


def _fit_target(x: Any) -> str:
    """Normalize a fit target into the TeX form ``(i-j)(k-l)``.

    Accepted forms:
    - ``"(i-j)(k-l)"``
    - ``"{i-j}{k-l}"``
    - ``((i, j), (k, l))`` or ``[(i, j), (k, l)]``
    """
    if isinstance(x, (tuple, list)) and len(x) == 2 and all(isinstance(t, (tuple, list, str, int)) for t in x):
        first, last = x
        return f"{_coord_paren(first)}{_coord_paren(last)}"

    s = str(x).strip()
    if s.startswith("{") and "}{" in s and s.endswith("}"):
        # "{i-j}{k-l}" -> "(i-j)(k-l)"
        import re
        parts = re.findall(r"\{\s*([^}]+?)\s*\}", s)
        if len(parts) == 2:
            return f"({_coord_token(parts[0])})({_coord_token(parts[1])})"
    return s


def _fit_span(x: Any) -> str:
    """Convert a span-like input into a fit target ``(i-j)(k-l)``."""
    if isinstance(x, str):
        s = x.strip()
        # Already the desired form
        if "(" in s and ")" in s and "{" not in s:
            return s
    if isinstance(x, (tuple, list)) and len(x) == 2:
        a, b = x
        return _coord_paren(a) + _coord_paren(b)
    # Fallback: try to parse braces ``{i-j}{k-l}``
    s = str(x).strip()
    import re
    parts = re.findall(r"\{\s*([^}]+?)\s*\}", s)
    if len(parts) == 2:
        return f"({parts[0]})({parts[1]})"
    return s


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
            opts = _julia_str(opts)

            # Accept a coord-pair span: ((i,j),(k,l))
            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(isinstance(t, (tuple, list)) for t in loc):
                first, last = loc
                first_tok = _coord_token(first)
                last_tok = _coord_token(last)
                span = f"{{{first_tok}}}{{{last_tok}}}"
                out.append((opts, span))
                continue

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
            opts = _julia_str(opts)

            # Coordinates may be tuples/lists.
            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = _coord_token(first)
            else:
                first = str(first).strip()
                if first.startswith("(") and first.endswith(")"):
                    first = first[1:-1].strip()

            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = _coord_token(last)
            else:
                last = str(last).strip()
                if last.startswith("(") and last.endswith(")"):
                    last = last[1:-1].strip()
        else:
            raise ValueError(f"submatrix_locs entry must be a 2- or 3-tuple, got: {item!r}")

        span = f"{{{first}}}{{{last}}}"
        out.append((opts, span))

    return out


def _normalize_pivot_locs(pivot_locs: Optional[Sequence[Tuple[Any, Any]]]) -> List[Tuple[str, str]]:
    """Normalize pivot box descriptors for tikz ``fit``.

    Accepts entries of the form:
    - ``(fit_target, style)`` where ``fit_target`` is either a string
      like ``"(1-1)(1-1)"`` or a pair ``((i,j),(k,l))``.
    """
    if not pivot_locs:
        return []
    out: List[Tuple[str, str]] = []
    for fit_target, style in pivot_locs:
        out.append((_fit_target(fit_target), _julia_str(style)))
    return out


def _normalize_txt_with_locs(txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]]) -> List[Tuple[str, str, str]]:
    """Normalize label descriptors (coord, text, style)."""
    if not txt_with_locs:
        return []
    out: List[Tuple[str, str, str]] = []
    for coord, txt, style in txt_with_locs:
        out.append((_coord_paren(coord), str(txt), _julia_str(style)))
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
        pivot_locs=_normalize_pivot_locs(pivot_locs),
        txt_with_locs=_normalize_txt_with_locs(txt_with_locs),
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


# -----------------------------------------------------------------------------
# Grid helpers: build GE mat_rep/mat_format from a "matrix-of-matrices" stack.
# -----------------------------------------------------------------------------


def _default_formater(x: Any) -> str:
    """Default scalar formatter for TeX.

    - If ``x`` is a string, it is assumed TeX-ready.
    - Otherwise, if SymPy is available, uses ``sympy.latex``.
    - Falls back to ``str(x)``.
    """
    if isinstance(x, str):
        return x
    try:
        import sympy as sym  # type: ignore
        return sym.latex(x)
    except Exception:
        return str(x)


def _as_2d_list(M: Any) -> Tuple[List[List[Any]], int, int]:
    """Return (rows, nrows, ncols) from common matrix-like inputs."""
    if M is None:
        return [], 0, 0

    # SymPy / numpy / etc.
    if hasattr(M, 'tolist'):
        rows = M.tolist()
    elif isinstance(M, (list, tuple)):
        rows = list(M)
    else:
        try:
            rows = list(M)
        except Exception as e:
            raise TypeError(f"Unsupported matrix-like object: {type(M)!r}") from e

    rows2: List[List[Any]] = []
    for r in rows:
        if isinstance(r, (list, tuple)):
            rows2.append(list(r))
        else:
            # 1D vector treated as a column
            rows2.append([r])

    nrows = len(rows2)
    ncols = max((len(r) for r in rows2), default=0)

    # Pad ragged rows with blanks.
    for r in rows2:
        if len(r) < ncols:
            r.extend([""] * (ncols - len(r)))

    return rows2, nrows, ncols


def _matrix_body_tex(M: Any, *, formater: LatexFormatter) -> str:
    """Format a matrix-like object into a TeX body: ``a & b \\ c & d``."""
    rows, nrows, ncols = _as_2d_list(M)
    if nrows == 0 or ncols == 0:
        return ""

    body_rows: List[str] = []
    for r in rows:
        cells = [formater(v) for v in r]
        body_rows.append(" & ".join(cells) + r" \\")
    return "\n".join(body_rows)


def _pnicearray_tex(
    M: Any,
    *,
    Nrhs: int = 0,
    formater: LatexFormatter,
    align: str = "r",
) -> str:
    """Wrap a matrix body into a ``pNiceArray`` environment."""
    rows, nrows, ncols = _as_2d_list(M)
    if nrows == 0 or ncols == 0:
        return r"\;"

    # Column format, optionally with an augmented separator.
    if Nrhs and 0 < Nrhs < ncols:
        left = ncols - Nrhs
        fmt = (align * left) + "|" + (align * Nrhs)
    else:
        fmt = align * ncols

    body = _matrix_body_tex(rows, formater=formater)
    return rf"\begin{{pNiceArray}}{{{fmt}}}%\n{body}\n\end{{pNiceArray}}"


def ge_grid_tex(
    matrices: Sequence[Sequence[Any]],
    Nrhs: int = 0,
    formater: LatexFormatter = _default_formater,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    **kwargs: Any,
) -> str:
    r"""Populate the GE template from a matrix stack.

    Parameters
    ----------
    matrices:
        A nested list representing the "matrix-of-matrices" layout, typically
        ``[[None, A0], [E1, A1], [E2, A2], ...]``.
    Nrhs:
        Number of RHS columns in the *A-block* matrices (used to insert a vertical
        bar in their internal ``pNiceArray`` preamble).
    formater:
        Scalar formatter for TeX.
    outer_hspace_mm:
        Horizontal spacing between the E and A blocks (only used for 2-column grids).

    Returns
    -------
    str
        TeX document (via :func:`ge_tex`).
    """
    grid = list(matrices or [])
    nrows = len(grid)
    ncols = max((len(r) for r in grid), default=0)
    if ncols == 0:
        raise ValueError("matrices must be a non-empty nested list")

    if ncols == 2:
        mat_format = rf"c@{{\hspace{{{outer_hspace_mm}mm}}}}c"
    else:
        mat_format = "c" * ncols

    lines: List[str] = []
    for r in range(nrows):
        row = list(grid[r])
        if len(row) < ncols:
            row += [None] * (ncols - len(row))

        cells: List[str] = []
        for c, cell in enumerate(row):
            if cell is None:
                cells.append(r"\;")
                continue
            # Apply Nrhs only to the last column, which is the augmented A-block in the legacy layout.
            nrhs_cell = Nrhs if (Nrhs and c == ncols - 1) else 0
            cells.append(_pnicearray_tex(cell, Nrhs=nrhs_cell, formater=formater, align=cell_align))

        lines.append(" & ".join(cells) + r" \\")

    mat_rep = "\n".join(lines)

    return ge_tex(mat_rep=mat_rep, mat_format=mat_format, **kwargs)
def ge_grid_svg(
    matrices: Sequence[Sequence[Any]],
    Nrhs: int = 0,
    formater: LatexFormatter = _default_formater,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
    **kwargs: Any,
) -> str:
    r"""Render the GE matrix stack to SVG.

    This is a convenience wrapper around :func:`ge_grid_tex` and the strict
    rendering boundary (:func:`matrixlayout.render.render_svg`).

    Parameters
    ----------
    matrices, Nrhs, formater, outer_hspace_mm, cell_align:
        See :func:`ge_grid_tex`.
    toolchain_name, crop, padding:
        Passed through to the renderer.

    Returns
    -------
    str
        SVG text.
    """
    tex = ge_grid_tex(
        matrices=matrices,
        Nrhs=Nrhs,
        formater=formater,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        **kwargs,
    )
    return _render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
