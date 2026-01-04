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


def _normalize_symbol_like(x: Any) -> str:
    """Normalize Julia/Python "symbol-like" values to a plain string.

    Julia interop note
    ------------------
    When calling Python from Julia, PyCall and PythonCall can represent
    ``Symbol`` values differently. Some arrive as native Python strings; others
    arrive as wrapper objects whose ``str(x)`` renders with a leading colon
    (e.g. ``":tight"``). This helper normalizes both cases.
    """

    if x is None:
        return ""
    s = str(x).strip()
    if s.startswith(":"):
        s = s[1:].strip()
    return s


def _normalize_cell_coord(coord: Any) -> str:
    """Normalize a cell coordinate into TeX form ``"(i-j)"``.

    Accepted input forms:
    - ``"(i-j)"`` or ``"i-j"``
    - ``(i, j)`` / ``[i, j]``
    """

    if coord is None:
        return ""
    if isinstance(coord, (tuple, list)) and len(coord) == 2:
        i, j = coord
        return f"({int(i)}-{int(j)})"
    s = str(coord).strip()
    if not s:
        return ""
    if s.startswith("(") and s.endswith(")"):
        return s
    # "i-j" -> "(i-j)"
    if "-" in s and any(ch.isdigit() for ch in s):
        return f"({s})"
    return s


def _normalize_fit_span(span: Any) -> str:
    r"""Normalize a TikZ ``fit`` target to ``"(i-j)(k-l)"``.

    Accepted input forms:
    - ``"(i-j)(k-l)"``
    - ``"{i-j}{k-l}"``
    - ``((i, j), (k, l))``
    """

    if span is None:
        return ""
    if isinstance(span, (tuple, list)) and len(span) == 2 and all(
        isinstance(x, (tuple, list)) and len(x) == 2 for x in span
    ):
        (i, j), (k, l) = span
        return f"({int(i)}-{int(j)})({int(k)}-{int(l)})"

    s = str(span).strip()
    if not s:
        return ""

    import re

    # legacy brace form: "{i-j}{k-l}"
    parts = re.findall(r"\{\s*([^}]+?)\s*\}", s)
    if len(parts) == 2:
        return f"({parts[0]})({parts[1]})"

    # parenthesis form: "(i-j)(k-l)" or "(i-j) (k-l)"
    parts = re.findall(r"\(\s*([^)]+?)\s*\)", s)
    if len(parts) == 2:
        return f"({parts[0]})({parts[1]})"

    return s


def _normalize_pivot_locs(pivot_locs: Optional[Sequence[Tuple[Any, Any]]]) -> List[Tuple[str, str]]:
    """Normalize pivot boxes to ``[(fit_target, extra_style), ...]``.

    Each ``fit_target`` becomes ``"(i-j)(k-l)"`` and style is symbol-normalized.
    """

    if not pivot_locs:
        return []
    out: List[Tuple[str, str]] = []
    for fit_target, extra_style in pivot_locs:
        out.append((_normalize_fit_span(fit_target), _normalize_symbol_like(extra_style)))
    return out


def _normalize_txt_with_locs(
    txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]]
) -> List[Tuple[str, str, str]]:
    """Normalize text labels to ``[(coord, txt, style), ...]``."""

    if not txt_with_locs:
        return []
    out: List[Tuple[str, str, str]] = []
    for coord, txt, style in txt_with_locs:
        out.append((_normalize_cell_coord(coord), str(txt), _normalize_symbol_like(style)))
    return out


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
        Sequence[Union[Tuple[Any, Any], Tuple[Any, Any, Any]]]
    ]
) -> List[Tuple[str, str]]:
    r"""Normalize submatrix descriptors to ``(options, span)``.

    Accepted input forms:
    - ``(opts, "{1-1}{2-2}")`` (legacy span encoding)
    - ``(opts, "(1-1)(2-2)")`` (two parenthesized tokens)
    - ``(opts, "(1-1)", "(2-2)")`` (explicit first/last, with parentheses)
    - ``(opts, "1-1", "2-2")`` (explicit first/last)
    - ``(opts, (i, j), (k, l))`` (explicit first/last as integer pairs)
    - ``(opts, ((i, j), (k, l)))`` (2-tuple of integer pairs)

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
            # Allow ((i,j),(k,l)) as a span.
            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(
                isinstance(x, (tuple, list)) and len(x) == 2 for x in loc
            ):
                (i, j), (k, l) = loc
                first, last = f"{int(i)}-{int(j)}", f"{int(k)}-{int(l)}"
                span = f"{{{first}}}{{{last}}}"
                out.append((_normalize_symbol_like(opts), span))
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
            # Allow integer-pair coordinates.
            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = f"{int(first[0])}-{int(first[1])}"
            else:
                first = str(first).strip()
            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = f"{int(last[0])}-{int(last[1])}"
            else:
                last = str(last).strip()
            if first.startswith("(") and first.endswith(")"):
                first = first[1:-1].strip()
            if last.startswith("(") and last.endswith(")"):
                last = last[1:-1].strip()
        else:
            raise ValueError(f"submatrix_locs entry must be a 2- or 3-tuple, got: {item!r}")

        span = f"{{{first}}}{{{last}}}"
        out.append((_normalize_symbol_like(opts), span))

    return out


def ge_tex(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: str = "vlines-in-sub-matrix = I",
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Union[Tuple[Any, Any], Tuple[Any, Any, Any]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[Any, Any]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]] = None,
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
    pivot_locs_norm = _normalize_pivot_locs(pivot_locs)
    txt_with_locs_norm = _normalize_txt_with_locs(txt_with_locs)

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
        submatrix_names=[str(x) for x in (submatrix_names or [])],
        pivot_locs=pivot_locs_norm,
        txt_with_locs=txt_with_locs_norm,
        rowechelon_paths=[str(x) for x in (rowechelon_paths or [])],
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
    submatrix_locs: Optional[Sequence[Union[Tuple[Any, Any], Tuple[Any, Any, Any]]]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Tuple[Any, Any]]] = None,
    txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]] = None,
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


def _matrix_shape(M: Any) -> Tuple[int, int]:
    """Best-effort (nrows, ncols) for common matrix containers.

    Supports:
    - objects with ``shape`` (NumPy/SymPy)
    - objects with ``rows`` / ``cols`` (SymPy)
    - nested sequences (list-of-lists)
    """

    if M is None:
        return (0, 0)
    if hasattr(M, "shape"):
        sh = getattr(M, "shape")
        try:
            return int(sh[0]), int(sh[1])
        except Exception:
            pass
    if hasattr(M, "rows") and hasattr(M, "cols"):
        return int(getattr(M, "rows")), int(getattr(M, "cols"))
    # list-of-lists
    try:
        r = len(M)
        c = len(M[0]) if r else 0
        return int(r), int(c)
    except Exception:
        return (0, 0)


def _matrix_entry(M: Any, i: int, j: int) -> Any:
    """Best-effort ``M[i,j]`` for common containers."""

    try:
        return M[i, j]
    except Exception:
        return M[i][j]


def _pnicearray_cell(
    M: Any,
    *,
    formater: Any = str,
    vline_cuts: Optional[Sequence[int]] = None,
) -> str:
    r"""Render a matrix cell as a ``pNiceArray`` fragment (no surrounding ``$``).

    Parameters
    ----------
    M:
        Matrix-like object.
    formater:
        Entry -> TeX formatter.
    vline_cuts:
        Optional cut positions (after these coefficient column counts) where a
        vertical bar should be inserted in the array format string.

    Notes
    -----
    This produces a fragment intended to be embedded inside an outer
    ``NiceArray`` that is already in math mode.
    """

    if M is None:
        return ""

    nrows, ncols = _matrix_shape(M)
    if nrows <= 0 or ncols <= 0:
        return ""

    cuts = sorted(set(int(c) for c in (vline_cuts or []) if int(c) > 0 and int(c) < ncols))
    # Build array preamble such as "rr|r|rr".
    preamble_parts: List[str] = []
    for j in range(1, ncols + 1):
        preamble_parts.append("r")
        if j in cuts:
            preamble_parts.append("|")
    mat_format = "".join(preamble_parts)

    rows: List[str] = []
    for i in range(nrows):
        entries: List[str] = []
        for j in range(ncols):
            v = _matrix_entry(M, i, j)
            try:
                tex = formater(v)
            except Exception:
                tex = str(v)
            entries.append(str(tex))
        rows.append(" & ".join(entries))

    body = " \\\\ ".join(rows)
    return rf"\begin{{pNiceArray}}{{{mat_format}}}{body}\end{{pNiceArray}}"


def _rhs_cuts_from_Nrhs(total_cols: int, Nrhs: Union[int, Sequence[int]]) -> List[int]:
    """Compute vertical cut positions for an augmented matrix.

    Parameters
    ----------
    total_cols:
        Total columns in the augmented matrix.
    Nrhs:
        Either an integer RHS width, or a list of segment widths.

    Returns
    -------
    list[int]
        Cut positions in 1-based column counts (i.e., insert a bar after these).
    """

    if Nrhs is None:
        return []
    if isinstance(Nrhs, (int, float)):
        nrhs = int(Nrhs)
        if nrhs <= 0 or nrhs >= total_cols:
            return []
        return [total_cols - nrhs]

    segs = [int(x) for x in Nrhs]
    if not segs or any(x <= 0 for x in segs):
        return []
    rhs_total = sum(segs)
    if rhs_total <= 0 or rhs_total >= total_cols:
        return []
    coef = total_cols - rhs_total
    cuts: List[int] = [coef]
    acc = coef
    for w in segs[:-1]:
        acc += w
        if 0 < acc < total_cols:
            cuts.append(acc)
    return cuts


def ge_grid_tex(
    matrices: Sequence[Sequence[Any]],
    *,
    Nrhs: Union[int, Sequence[int]] = 0,
    formater: Any = str,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n",
    nice_options: str = "vlines-in-sub-matrix = I",
    col_gap: str = "8mm",
    partition_col: int = 1,
    **kwargs: Any,
) -> str:
    r"""Build a GE TeX document from a legacy-style matrix stack.

    Parameters
    ----------
    matrices:
        Nested list structure such as ``[[None, A0], [E1, A1], ...]``.
    Nrhs:
        RHS width (or segment widths) used to insert partition bars in the
        augmented matrix column.
    partition_col:
        Grid column index (0-based) that should receive RHS partition bars.
        For the canonical GE layout this is the *second* column (index 1).

    Notes
    -----
    This is a layout-only helper: it does not perform elimination.
    """

    if not matrices:
        raise ValueError("matrices must be a non-empty nested sequence")

    ngrid_cols = max(len(r) for r in matrices)
    if ngrid_cols <= 0:
        raise ValueError("matrices rows must contain at least one column")

    gap = (col_gap or "").strip()
    if gap:
        mat_format = ("c" + rf"@{{\hspace{{{gap}}}}}") * (ngrid_cols - 1) + "c"
    else:
        mat_format = "c" * ngrid_cols

    rep_rows: List[str] = []
    for r in matrices:
        cells: List[str] = []
        for c in range(ngrid_cols):
            M = r[c] if c < len(r) else None
            vcuts: Optional[List[int]] = None
            if c == partition_col and Nrhs:
                _, ncols = _matrix_shape(M)
                vcuts = _rhs_cuts_from_Nrhs(ncols, Nrhs)
            cells.append(_pnicearray_cell(M, formater=formater, vline_cuts=vcuts))
        rep_rows.append(" & ".join(cells))

    mat_rep = " \\\\ ".join(rep_rows)
    return ge_tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        preamble=preamble,
        nice_options=nice_options,
        **kwargs,
    )


def ge_grid_svg(
    matrices: Sequence[Sequence[Any]],
    *,
    Nrhs: Union[int, Sequence[int]] = 0,
    formater: Any = str,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 2pt}" + "\n",
    nice_options: str = "vlines-in-sub-matrix = I",
    col_gap: str = "8mm",
    partition_col: int = 1,
    toolchain_name: Optional[Any] = None,
    crop: Optional[Any] = None,
    padding: Any = None,
    **kwargs: Any,
) -> str:
    """Render a GE matrix stack to SVG via the strict rendering boundary."""

    tex = ge_grid_tex(
        matrices,
        Nrhs=Nrhs,
        formater=formater,
        preamble=preamble,
        nice_options=nice_options,
        col_gap=col_gap,
        partition_col=partition_col,
        **kwargs,
    )

    tname = _normalize_symbol_like(toolchain_name) or None
    crop_s = _normalize_symbol_like(crop) or None
    if tname:
        return _render_svg(tex, toolchain_name=tname, crop=crop_s, padding=padding)
    return _render_svg(tex, crop=crop_s, padding=padding)
