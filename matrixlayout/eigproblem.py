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

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple, Union, List, Dict

from .jinja_env import render_template
from .render import render_svg
from .formatting import latexify, apply_decorator, expand_entry_selectors, norm_str


LatexFormatter = Callable[[Any], str]


def _is_zero_like(x: Any) -> bool:
    """Best-effort check for whether x represents numeric zero."""
    if x is None:
        return False
    if isinstance(x, str):
        return x.strip() == "0"
    # SymPy-ish: x.is_zero is True/False/None
    try:
        iz = getattr(x, "is_zero")
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
    dec_specs: List[Tuple[Callable[..., str], set[Tuple[int, int, int]]]] = []
    if decorators and target_name:
        target_key = target_name.lower()
        alias_map = {
            "eigenbasis": {"eigenbasis", "evecs_row", "basis"},
            "orthonormal_basis": {"orthonormal_basis", "qvecs_row", "orthobasis"},
        }
        targets = alias_map.get(target_key, {target_key})
        for spec_item in decorators:
            if not isinstance(spec_item, dict):
                raise ValueError("decorators must be dict specs")
            key = spec_item.get("target")
            if key is None or str(key).lower() not in targets:
                continue
            dec = spec_item.get("decorator")
            if not callable(dec):
                raise ValueError("decorator must be callable")
            entries = spec_item.get("entries")
            expanded: set[Tuple[int, int, int]] = set()
            if entries is None:
                for g_idx, group in enumerate(vec_groups):
                    for v_idx, vec in enumerate(group):
                        for i_idx, _ in enumerate(vec):
                            expanded.add((g_idx, v_idx, i_idx))
            else:
                for ent in entries:
                    if isinstance(ent, (list, tuple)) and len(ent) == 3:
                        expanded.add((int(ent[0]), int(ent[1]), int(ent[2])))
                        continue
                    if isinstance(ent, (list, tuple)) and len(ent) == 2:
                        a, b = ent
                        if (
                            isinstance(a, (list, tuple))
                            and isinstance(b, (list, tuple))
                            and len(a) == 3
                            and len(b) == 3
                            and int(a[0]) == int(b[0])
                            and int(a[1]) == int(b[1])
                        ):
                            g_idx, v_idx = int(a[0]), int(a[1])
                            i0, i1 = int(a[2]), int(b[2])
                            for i_idx in range(min(i0, i1), max(i0, i1) + 1):
                                expanded.add((g_idx, v_idx, i_idx))
            if expanded:
                dec_specs.append((dec, expanded))
    groups_out: List[str] = []
    applied_counts = [0 for _ in dec_specs]
    for g_idx, vecs in enumerate(vec_groups):
        vec_tex: List[str] = []
        for v_idx, vec in enumerate(vecs):
            entries: List[str] = []
            for i_idx, v in enumerate(vec):
                cell = formatter(v)
                if dec_specs:
                    for idx, (dec, expanded) in enumerate(dec_specs):
                        if (g_idx, v_idx, i_idx) in expanded:
                            cell = apply_decorator(dec, i_idx, v_idx, v, cell)
                            applied_counts[idx] += 1
                entries.append(cell)
            vec_tex.append(r"$\begin{pNiceArray}{r}" + nl.join(entries) + r" \end{pNiceArray}$")
        groups_out.append(", ".join(vec_tex))
    if strict and dec_specs:
        for count in applied_counts:
            if count == 0:
                raise ValueError("decorator selector did not match any entries")
    return " & & ".join(groups_out)


def _apply_matrix_decorators(
    mat_tex: List[List[str]],
    mat_raw: List[List[Any]],
    decorators: Optional[Sequence[Any]],
    matrix_ids: Sequence[str],
    formatter: LatexFormatter,
    strict: bool,
) -> List[List[str]]:
    if not decorators:
        return mat_tex
    id_set = {str(mid).lower() for mid in matrix_ids}
    nrows = len(mat_tex)
    ncols = len(mat_tex[0]) if nrows else 0
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("matrix", spec_item.get("target"))
        if key is None or str(key).lower() not in id_set:
            continue
        dec = spec_item.get("decorator")
        if not callable(dec):
            raise ValueError("decorator must be callable")
        fmt = spec_item.get("formatter", formatter)
        applied = 0
        for i, j in expand_entry_selectors(spec_item.get("entries"), nrows, ncols):
            if i < 0 or j < 0 or i >= nrows or j >= ncols:
                continue
            raw = mat_raw[i][j]
            base = mat_tex[i][j] or str(fmt(raw))
            mat_tex[i][j] = apply_decorator(dec, i, j, raw, base)
            applied += 1
        if strict and applied == 0:
            raise ValueError("decorator selector did not match any entries")
    return mat_tex


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
    for v, m in zip(values, multiplicities):
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
    for v, m in zip(values, multiplicities):
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
            entries = [v for v in vec]
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
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
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
    preamble:
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
    if sz is None and "sz" in eig:
        # Algorithmic packages may attach the original matrix size for SVD tables.
        try:
            sz = tuple(eig["sz"])  # type: ignore[arg-type]
        except Exception:
            sz = None
    sz = (n, n) if sz is None else tuple(sz)

    # Value rows use an interleaved "value, gap, value" scheme.
    value_cols = max(1, 2 * len(lambdas_distinct) - 1)
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
                sz=sz[0],
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
            sz=sz,
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
            sz=sz,
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
            sz=sz[1],
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
                sz=sz[1],
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
        "preamble": preamble,
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
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
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
    """Render the eigen/QR/SVD table to SVG via the strict rendering boundary."""
    tex = render_eig_tex(
        eig,
        case=case,
        formatter=formatter,
        color=color,
        mmLambda=mmLambda,
        mmS=mmS,
        fig_scale=fig_scale,
        preamble=preamble,
        sz=sz,
        decorators=decorators,
        strict=strict,
    )
    if output_dir is None:
        output_dir = tmp_dir
    opts: Dict[str, Any] = dict(render_opts or {})
    if toolchain_name is not None:
        opts["toolchain_name"] = toolchain_name
    if crop is not None:
        opts["crop"] = crop
    if padding is not None:
        opts["padding"] = padding
    if frame is not None:
        opts["frame"] = frame
    if output_dir is not None:
        opts["output_dir"] = output_dir
    if output_stem is not None:
        opts["output_stem"] = output_stem
    if exact_bbox is not None:
        opts["exact_bbox"] = exact_bbox
    return render_svg(tex, **opts)
