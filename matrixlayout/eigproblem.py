"""Eigen/SVD table layout template.

This module implements the ``EIGPROBLEM_TEMPLATE`` layout using the package
template at ``matrixlayout/templates/eigproblem.tex.j2``.

Responsibilities (layout-only):
- Format already-computed eigen/singular values, multiplicities, and vector
  groups into TeX fragments.
- Render the document TeX via the shared Jinja2 environment.
- Optionally render SVG through the strict rendering boundary
  :func:`jupyter_tikz.render_svg`.

Out of scope:
- Computing eigenvalues/eigenvectors, QR/SVD, Gram–Schmidt, etc.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

import sympy as sym

from .eigproblem_decorations import apply_matrix_decorators as _apply_matrix_decorators
from .eigproblem_decorations import apply_vector_decorators as _apply_vector_decorators
from .eigproblem_decorations import collect_vector_decorator_specs as _collect_vector_decorator_specs
from .formatting import latexify, norm_str
from .jinja_env import render_template
from .render import _resolve_render_svg_kwargs, render_svg


LatexFormatter = Callable[[Any], str]


def _positive_rational_gcd(values: Sequence[Any]) -> Any:
    rats: List[sym.Rational] = []
    for v in values:
        try:
            rv = sym.Rational(v)
        except Exception:
            return sym.Integer(1)
        if rv == 0:
            continue
        rats.append(abs(rv))
    if not rats:
        return sym.Integer(1)
    nums = [int(r.p) for r in rats]
    dens = [int(r.q) for r in rats]
    gnum = nums[0]
    for n in nums[1:]:
        gnum = int(sym.igcd(gnum, n))
    lden = dens[0]
    for d in dens[1:]:
        lden = int(sym.ilcm(lden, d))
    return sym.Rational(gnum, lden)


def _display_vector_factor(vec: Sequence[Any]) -> tuple[Any, Optional[List[Any]]]:
    """Extract a common multiplicative factor for display, if helpful."""

    exprs = [sym.factor_terms(sym.together(sym.sympify(v))) for v in vec]
    nonzero = [e for e in exprs if e != 0]
    if not nonzero:
        return sym.Integer(1), None

    coeffs: List[Any] = []
    factor_counts: dict[Any, int] = {}
    first = True
    for e in nonzero:
        coeff, rest = e.as_coeff_Mul()
        coeffs.append(coeff)
        counts: dict[Any, int] = {}
        for f in sym.Mul.make_args(rest):
            counts[f] = counts.get(f, 0) + 1
        if first:
            factor_counts = counts
            first = False
        else:
            factor_counts = {f: min(factor_counts.get(f, 0), counts.get(f, 0)) for f in list(factor_counts)}
            factor_counts = {f: c for f, c in factor_counts.items() if c > 0}

    coeff_factor = _positive_rational_gcd(coeffs)
    factor = sym.sympify(coeff_factor)
    for f, count in factor_counts.items():
        factor *= f**count
    factor = sym.factor_terms(sym.cancel(sym.together(factor)))

    if sym.simplify(factor - 1) == 0:
        return sym.Integer(1), None

    reduced = [sym.factor_terms(sym.cancel(sym.together(sym.simplify(e / factor)))) for e in exprs]
    return factor, reduced


def _format_vector_for_display(
    vec: Sequence[Any],
    *,
    formatter: LatexFormatter,
    nl: str,
    factor_common: bool,
    decorators_apply: Optional[Callable[[int, Any, str], str]] = None,
) -> str:
    factor = sym.Integer(1)
    entries_source: Sequence[Any] = list(vec)
    if factor_common:
        factor, reduced = _display_vector_factor(vec)
        if reduced is not None:
            entries_source = reduced

    entries: List[str] = []
    for i_idx, v in enumerate(entries_source):
        cell = formatter(v)
        if decorators_apply is not None:
            cell = decorators_apply(i_idx, v, cell)
        entries.append(cell)

    body = r"\begin{pNiceArray}{r}" + nl.join(entries) + r" \end{pNiceArray}"
    if sym.simplify(factor - 1) == 0:
        return "$" + body + "$"
    return "$" + formatter(factor) + r"\," + body + "$"


def _is_zero_like(x: Any) -> bool:
    """Best-effort check for whether x represents numeric zero."""
    if x is None:
        return False
    if isinstance(x, str):
        return x.strip() == "0"
    # SymPy-ish: x.is_zero is True/False/None
    try:
        iz = x.is_zero
        if iz is True:
            return True
        if iz is False:
            return False
    except Exception:
        pass
    try:
        return float(x) == 0.0
    except Exception:
        return False


def _mk_values(values: Sequence[Any], *, formatter: LatexFormatter, zero_blank: bool = False) -> List[str]:
    """Return interleaved value cells matching the table column scheme."""
    l: List[str] = []
    for v in values:
        if zero_blank and _is_zero_like(v):
            s = ""
        else:
            s = formatter(v)
        l.append(f"${s}$")

    if not l:
        return []

    interleaved: List[str] = [l[0]]
    for cell in l[1:]:
        interleaved.append("")  # gap column
        interleaved.append(cell)
    return interleaved


def _mk_table_format(num_distinct: int) -> str:
    ncols = max(0, 2 * num_distinct - 1)
    return r"{@{}l" + ("c" * ncols) + r"@{}}"


def _mk_rule_format(num_distinct: int) -> str:
    # One cmidrule under each value column (columns 2,4,6,... in the tabular)
    return "".join([rf" \cmidrule{{{2*i}-{2*i}}}" for i in range(1, num_distinct + 1)])


def _coerce_matrix_size(value: Any, *, default: Tuple[int, int]) -> Tuple[int, int]:
    """Return a concrete two-integer matrix size."""
    if value is None:
        return default
    try:
        items = tuple(value)
    except Exception as exc:
        raise ValueError("sz must be a 2-item matrix size") from exc
    if len(items) != 2:
        raise ValueError("sz must be a 2-item matrix size")
    return (int(items[0]), int(items[1]))


def _mk_vector_blocks(
    vec_groups: Sequence[Sequence[Iterable[Any]]],
    *,
    formatter: LatexFormatter,
    add_height_mm: int = 0,
    decorators: Optional[Sequence[Any]] = None,
    target_name: Optional[str] = None,
    strict: bool = False,
) -> str:
    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    dec_specs = _collect_vector_decorator_specs(vec_groups, decorators, target_name)
    factor_common = getattr(formatter, "__name__", "") == "latexify"
    groups_out: List[str] = []
    applied_counts = [0 for _ in dec_specs]
    for g_idx, vecs in enumerate(vec_groups):
        vec_tex: List[str] = []
        for v_idx, vec in enumerate(vecs):
            def _decorate(i_idx: int, v: Any, cell: str, *, _g_idx: int = g_idx, _v_idx: int = v_idx) -> str:
                if not dec_specs:
                    return cell
                return _apply_vector_decorators(
                    cell,
                    value=v,
                    group_index=_g_idx,
                    vector_index=_v_idx,
                    entry_index=i_idx,
                    dec_specs=dec_specs,
                    applied_counts=applied_counts,
                )

            vec_tex.append(
                _format_vector_for_display(
                    list(vec),
                    formatter=formatter,
                    nl=nl,
                    factor_common=factor_common,
                    decorators_apply=_decorate if dec_specs else None,
                )
            )
        groups_out.append(", ".join(vec_tex))
    if strict and dec_specs:
        for count in applied_counts:
            if count == 0:
                raise ValueError("decorator selector did not match any entries")
    return " & & ".join(groups_out)


def _mk_diag_matrix(
    values: Sequence[Any],
    multiplicities: Sequence[int],
    *,
    formatter: LatexFormatter,
    sz: Tuple[int, int],
    mm: int = 8,
    span_cols: Optional[int] = None,
    extra_space: str = "",
    add_height_mm: int = 0,
    decorators: Optional[Sequence[Any]] = None,
    matrix_ids: Optional[Sequence[str]] = None,
    strict: bool = False,
) -> str:
    # Expand distinct values by multiplicity to length N (diagonal entries)
    diag: List[Any] = []
    for v, m in zip(values, multiplicities, strict=False):
        diag.extend([v] * int(m))
    n = len(diag)

    space = r"@{\hspace{" + str(mm) + r"mm}}"
    # Legacy itikz implementation spans *distinct* eigen/singular-value columns
    # (len(multiplicities)) rather than the interleaved "value+gap" column count.
    n_value_cols = max(1, len(multiplicities)) if span_cols is None else int(span_cols)
    pre = rf"\multicolumn{{{n_value_cols}}}{{c}}{{" + "\n" + r"$\begin{pNiceArray}{" + space.join(["c"] * n) + "}"
    post = r"\end{pNiceArray}$}"

    # Build an n x n string matrix
    zero = formatter(0)
    mat_raw: List[List[Any]] = [[0 for _ in range(n)] for __ in range(n)]
    mat_tex: List[List[str]] = [[zero for _ in range(n)] for __ in range(n)]
    for i, v in enumerate(diag):
        mat_raw[i][i] = v
        mat_tex[i][i] = formatter(v)

    # Edge spacing
    if extra_space:
        for i in range(n):
            mat_tex[i][0] = extra_space + mat_tex[i][0]
            mat_tex[i][n - 1] = mat_tex[i][n - 1] + extra_space

    if matrix_ids:
        mat_tex = _apply_matrix_decorators(mat_tex, mat_raw, decorators, matrix_ids, formatter, strict)

    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    rows = [" & ".join(row) for row in mat_tex]
    return pre + nl.join(rows) + r" \\ " + post


def _mk_sigma_matrix(
    values: Sequence[Any],
    multiplicities: Sequence[int],
    *,
    formatter: LatexFormatter,
    sz: Tuple[int, int],
    mm: int = 8,
    span_cols: Optional[int] = None,
    extra_space: str = "",
    add_height_mm: int = 0,
    decorators: Optional[Sequence[Any]] = None,
    matrix_ids: Optional[Sequence[str]] = None,
    strict: bool = False,
) -> str:
    diag: List[Any] = []
    for v, m in zip(values, multiplicities, strict=False):
        diag.extend([v] * int(m))
    n = len(diag)

    mrows, ncols = int(sz[0]), int(sz[1])
    if ncols <= 0 or mrows <= 0:
        raise ValueError("Invalid sz for sigma matrix")

    space = r"@{\hspace{" + str(mm) + r"mm}}"
    n_value_cols = max(1, len(multiplicities)) if span_cols is None else int(span_cols)
    pre = rf"\multicolumn{{{n_value_cols}}}{{c}}{{" + "\n" + r"$\begin{pNiceArray}{" + space.join(["c"] * ncols) + "}"
    post = r"\end{pNiceArray}$}"

    zero = formatter(0)
    mat_raw: List[List[Any]] = [[0 for _ in range(ncols)] for __ in range(mrows)]
    mat_tex: List[List[str]] = [[zero for _ in range(ncols)] for __ in range(mrows)]
    for i in range(min(n, mrows, ncols)):
        mat_raw[i][i] = diag[i]
        mat_tex[i][i] = formatter(diag[i])

    if extra_space:
        for i in range(mrows):
            mat_tex[i][0] = extra_space + mat_tex[i][0]
            mat_tex[i][ncols - 1] = mat_tex[i][ncols - 1] + extra_space

    if matrix_ids:
        mat_tex = _apply_matrix_decorators(mat_tex, mat_raw, decorators, matrix_ids, formatter, strict)

    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    rows = [" & ".join(row) for row in mat_tex]
    return pre + nl.join(rows) + r" \\ " + post


def _mk_vecs_matrix(
    vec_groups: Sequence[Sequence[Iterable[Any]]],
    *,
    formatter: LatexFormatter,
    sz: int,
    mm: int = 8,
    span_cols: int = 1,
    extra_space: str = "",
    add_height_mm: int = 0,
    decorators: Optional[Sequence[Any]] = None,
    matrix_ids: Optional[Sequence[str]] = None,
    strict: bool = False,
) -> Optional[str]:
    # Flatten vectors column-wise
    cols: List[List[str]] = []
    for group in vec_groups:
        for vec in group:
            entries = list(vec)
            cols.append(entries)

    if not cols:
        return None

    # All vectors must have length sz
    if any(len(c) != sz for c in cols):
        return None

    # Build square matrix sz x sz, filling columns left to right
    if len(cols) != sz:
        # Legacy code returned a raw matrix in this case; for layout code, None is clearer.
        return None

    mat_raw: List[List[Any]] = [[0 for _ in range(sz)] for __ in range(sz)]
    mat_tex: List[List[str]] = [[formatter(0) for _ in range(sz)] for __ in range(sz)]
    for j, col in enumerate(cols):
        for i, v in enumerate(col):
            mat_raw[i][j] = v
            mat_tex[i][j] = formatter(v)

    if extra_space:
        for i in range(sz):
            mat_tex[i][0] = extra_space + mat_tex[i][0]
            mat_tex[i][sz - 1] = mat_tex[i][sz - 1] + extra_space

    if matrix_ids:
        mat_tex = _apply_matrix_decorators(mat_tex, mat_raw, decorators, matrix_ids, formatter, strict)

    space = r"@{\hspace{" + str(mm) + r"mm}}"
    pre = rf"\multicolumn{{{int(span_cols)}}}{{c}}{{" + "\n" + r"$\begin{pNiceArray}{" + space.join(["r"] * sz) + "}"
    post = r"\end{pNiceArray}$}"

    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    rows = [" & ".join(row) for row in mat_tex]
    return pre + nl.join(rows) + r" \\ " + post


def render_eig_tex(
    eig: Mapping[str, Any],
    *,
    case: str = "S",
    formatter: LatexFormatter = latexify,
    color: str = "blue",
    mmLambda: int = 8,
    mmS: int = 4,
    fig_scale: Optional[Union[int, float]] = None,
    body_preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
    sz: Optional[Tuple[int, int]] = None,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
) -> str:
    """Render an eigen/QR/SVD table TeX document using the package template.

    Parameters
    ----------
    eig:
        Pre-computed eigen/SVD description dictionary (algorithmic package owns this).
        Expected keys (case-dependent):
          - always: 'lambda' (distinct values), 'ma' (multiplicities), 'evecs' (groups)
          - optional: 'sigma', 'qvecs', 'uvecs'
    case:
        'S' for eigenvectors S, 'Q' for orthonormal eigenvectors Q, 'SVD' for SVD.
    formatter:
        Converts scalar entries to LaTeX strings (e.g. sympy.latex).
    color:
        xcolor color name (e.g. 'blue', 'RoyalBlue', 'DarkGreen').
    mmLambda, mmS:
        Column spacing (mm) for diagonal/matrix blocks.
    fig_scale:
        If provided, wraps the content in ``\\scalebox{<fig_scale>}{% ... }``.
        This matches the template convention.
    body_preamble:
        TeX inserted after the scale wrapper and before the tabular. Use for
        ``\\NiceMatrixOptions`` etc.
    sz:
        Matrix size (M, N) for SVD tables. If omitted, defaults to (N, N) where
        N = sum(ma).
    decorators:
        Optional decorator specs for matrix blocks or vector rows.
    strict:
        If True, raise when a decorator selector matches zero entries.

    Examples
    --------
    Decorate a basis entry in the eigenbasis row::

        def box(tex): return rf"\\boxed{{{tex}}}"
        decorators = [{"target": "eigenbasis", "entries": [(0, 0, 1)], "decorator": box}]
        tex = render_eig_tex(spec, case="S", decorators=decorators)
    """
    if "lambda" not in eig or "ma" not in eig or "evecs" not in eig:
        missing = [k for k in ("lambda", "ma", "evecs") if k not in eig]
        raise KeyError(f"render_eig_tex missing required keys: {missing}")

    case = norm_str(case) or ""
    color = norm_str(color) or ""
    lambdas_distinct = list(eig["lambda"])
    multiplicities = list(eig["ma"])
    n = int(sum(multiplicities))
    # Algorithmic packages may attach the original matrix size for SVD tables.
    size = _coerce_matrix_size(sz if sz is not None else eig.get("sz"), default=(n, n))

    # Matrix blocks span only the *distinct* value columns.
    matrix_span_cols = max(1, len(lambdas_distinct))

    # Values rows
    sigmas_row = None
    if case.upper() == "SVD" and "sigma" in eig:
        sig_cells = _mk_values(list(eig["sigma"]), formatter=formatter, zero_blank=True)
        sigmas_row = " & ".join(sig_cells) + r" \\"
    lambdas_row = " & ".join(_mk_values(lambdas_distinct, formatter=formatter)) + r" \\"
    mas_row = " & ".join(_mk_values(multiplicities, formatter=formatter)) + r" \\"

    # Vector blocks
    evecs_row = _mk_vector_blocks(
        eig["evecs"],
        formatter=formatter,
        decorators=decorators,
        target_name="eigenbasis",
        strict=strict,
    ) + r" \\"

    orthonormal_row = None
    left_singular_matrix = None
    if case.upper() == "Q":
        if "qvecs" in eig:
            orthonormal_row = _mk_vector_blocks(
                eig["qvecs"],
                formatter=formatter,
                add_height_mm=1,
                decorators=decorators,
                target_name="orthonormal_basis",
                strict=strict,
            ) + r" \\"
    elif case.upper() == "SVD":
        if "qvecs" in eig:
            orthonormal_row = _mk_vector_blocks(
                eig["qvecs"],
                formatter=formatter,
                add_height_mm=1,
                decorators=decorators,
                target_name="orthonormal_basis",
                strict=strict,
            ) + r" \\"
        # Left singular vectors are shown as a matrix (U) below, if provided.
        if "uvecs" in eig:
            left_singular_matrix = _mk_vecs_matrix(
                eig["uvecs"],
                formatter=formatter,
                sz=size[0],
                mm=mmS,
                span_cols=matrix_span_cols,
                decorators=decorators,
                matrix_ids=["uvecs", "left_singular_matrix", "u"],
                strict=strict,
            )

    # Matrices (diagonal + eigen/singular vector matrix)
    if case.upper() == "SVD" and "sigma" in eig:
        diag_values = list(eig["sigma"])
        lambda_matrix = _mk_sigma_matrix(
            diag_values,
            multiplicities,
            formatter=formatter,
            sz=size,
            mm=mmLambda,
            span_cols=matrix_span_cols,
            decorators=decorators,
            matrix_ids=["sigma", "sigma_matrix", "lambda", "lambda_matrix"],
            strict=strict,
        )
    else:
        lambda_matrix = _mk_diag_matrix(
            lambdas_distinct,
            multiplicities,
            formatter=formatter,
            sz=size,
            mm=mmLambda,
            span_cols=matrix_span_cols,
            decorators=decorators,
            matrix_ids=["lambda", "lambda_matrix"],
            strict=strict,
        )

    if case.upper() == "S":
        evecs_matrix = _mk_vecs_matrix(
            eig["evecs"],
            formatter=formatter,
            sz=size[1],
            mm=mmS,
            span_cols=matrix_span_cols,
            decorators=decorators,
            matrix_ids=["evecs", "evecs_matrix", "s"],
            strict=strict,
        )
    else:
        qvecs = eig.get("qvecs")
        evecs_matrix = (
            _mk_vecs_matrix(
                qvecs,
                formatter=formatter,
                sz=size[1],
                mm=mmS,
                span_cols=matrix_span_cols,
                decorators=decorators,
                matrix_ids=["qvecs", "evecs", "evecs_matrix", "q", "v"],
                strict=strict,
            )
            if qvecs
            else None
        )

    # Matrix name labels
    if case.upper() == "S":
        matrix_names = [r"\Lambda", "S"]
    elif case.upper() == "Q":
        matrix_names = [r"\Lambda", "Q"]
    else:
        matrix_names = [r"\Sigma", "V", "U"]

    # Figure scaling wrapper string (table convention)
    fig_scale_cmd = None
    if fig_scale is not None:
        fig_scale_cmd = r"\scalebox{" + str(fig_scale) + r"}{%"

    context = {
        "body_preamble": body_preamble,
        "fig_scale": fig_scale_cmd,
        "matrix_names": matrix_names,
        "table_format": _mk_table_format(len(lambdas_distinct)),
        "rule_format": _mk_rule_format(len(lambdas_distinct)),
        "sigmas": sigmas_row,
        "lambdas": lambdas_row,
        "algebraic_multiplicities": mas_row,
        "eigenbasis": evecs_row,
        "orthonormal_basis": orthonormal_row,
        "color": "{" + color + "}",
        "lambda_matrix": lambda_matrix,
        "evecs_matrix": evecs_matrix,
        "left_singular_matrix": left_singular_matrix,
    }
    return render_template("eigproblem.tex.j2", context)


def render_eig_svg(
    eig: Mapping[str, Any],
    *,
    case: str = "S",
    formatter: LatexFormatter = latexify,
    color: str = "blue",
    mmLambda: int = 8,
    mmS: int = 4,
    fig_scale: Optional[Union[int, float]] = None,
    body_preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
    sz: Optional[Tuple[int, int]] = None,
    decorators: Optional[Sequence[Any]] = None,
    strict: bool = False,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
    frame: Any = None,
    exact_bbox: Optional[bool] = None,
    output_stem: Optional[str] = None,
    tmp_dir: Optional[Any] = None,
    output_dir: Optional[Any] = None,
    render_opts: Optional[Mapping[str, Any]] = None,
) -> str:
    """Render the eigen/QR/SVD table to SVG via the strict rendering boundary.

    ``tmp_dir`` is retained as a compatibility alias for ``output_dir``.
    Prefer ``output_dir`` for new code.
    """
    tex = render_eig_tex(
        eig,
        case=case,
        formatter=formatter,
        color=color,
        mmLambda=mmLambda,
        mmS=mmS,
        fig_scale=fig_scale,
        body_preamble=body_preamble,
        sz=sz,
        decorators=decorators,
        strict=strict,
    )
    opts = _resolve_render_svg_kwargs(
        render_opts,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
        tmp_dir=tmp_dir,
        output_stem=output_stem,
        exact_bbox=exact_bbox,
    )
    return render_svg(tex, **opts)
