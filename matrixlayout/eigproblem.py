"""Eigen/SVD table layout template (EIGPROBLEM_TEMPLATE migration).

This module migrates the legacy ``EIGPROBLEM_TEMPLATE`` from ``itikz.nicematrix``
into a package template at ``matrixlayout/templates/eigproblem.tex.j2``.

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
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple, Union, List

from .jinja_env import render_template
from .render import render_svg


LatexFormatter = Callable[[Any], str]


def _default_formater(x: Any) -> str:
    """Default scalar formatter for TeX.

    Behavior:
    - If ``x`` is already a string, it is assumed to be TeX-ready and returned unchanged.
    - Otherwise, if SymPy is available, uses ``sympy.latex(x)``.
    - Falls back to ``str(x)``.
    """
    if isinstance(x, str):
        return x
    try:
        import sympy as sym  # type: ignore
        return sym.latex(x)
    except Exception:
        return str(x)


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


def _mk_values(values: Sequence[Any], *, formater: LatexFormatter, zero_blank: bool = False) -> List[str]:
    """Return interleaved value cells matching the legacy tabular column scheme."""
    l: List[str] = []
    for v in values:
        if zero_blank and _is_zero_like(v):
            s = ""
        else:
            s = formater(v)
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
    formater: LatexFormatter,
    add_height_mm: int = 0,
) -> str:
    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    groups_out: List[str] = []
    for vecs in vec_groups:
        vec_tex: List[str] = []
        for vec in vecs:
            entries = [formater(v) for v in vec]
            vec_tex.append(r"$\begin{pNiceArray}{r}" + nl.join(entries) + r" \end{pNiceArray}$")
        groups_out.append(", ".join(vec_tex))
    return " & & ".join(groups_out)


def _mk_diag_matrix(
    values: Sequence[Any],
    multiplicities: Sequence[int],
    *,
    formater: LatexFormatter,
    sz: Tuple[int, int],
    mm: int = 8,
    extra_space: str = "",
    add_height_mm: int = 0,
) -> str:
    # Expand distinct values by multiplicity to length N (diagonal entries)
    diag: List[Any] = []
    for v, m in zip(values, multiplicities):
        diag.extend([v] * int(m))
    n = len(diag)

    space = r"@{\hspace{" + str(mm) + r"mm}}"
    pre = rf"\multicolumn{{{len(multiplicities)}}}{{c}}{{" + "\n" + r"$\begin{pNiceArray}{" + space.join(["c"] * n) + "}"
    post = r"\end{pNiceArray}$}"

    # Build an n x n string matrix
    zero = formater(0)
    mat: List[List[str]] = [[zero for _ in range(n)] for __ in range(n)]
    for i, v in enumerate(diag):
        mat[i][i] = formater(v)

    # Edge spacing
    if extra_space:
        for i in range(n):
            mat[i][0] = extra_space + mat[i][0]
            mat[i][n - 1] = mat[i][n - 1] + extra_space

    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    rows = [" & ".join(row) for row in mat]
    return pre + nl.join(rows) + r" \\ " + post


def _mk_vecs_matrix(
    vec_groups: Sequence[Sequence[Iterable[Any]]],
    *,
    formater: LatexFormatter,
    sz: int,
    mm: int = 8,
    extra_space: str = "",
    add_height_mm: int = 0,
) -> Optional[str]:
    # Flatten vectors column-wise
    cols: List[List[str]] = []
    for group in vec_groups:
        for vec in group:
            entries = [formater(v) for v in vec]
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

    mat: List[List[str]] = [[formater(0) for _ in range(sz)] for __ in range(sz)]
    for j, col in enumerate(cols):
        for i, v in enumerate(col):
            mat[i][j] = v

    if extra_space:
        for i in range(sz):
            mat[i][0] = extra_space + mat[i][0]
            mat[i][sz - 1] = mat[i][sz - 1] + extra_space

    space = r"@{\hspace{" + str(mm) + r"mm}}"
    pre = rf"\multicolumn{{{len(vec_groups)}}}{{c}}{{" + "\n" + r"$\begin{pNiceArray}{" + space.join(["r"] * sz) + "}"
    post = r"\end{pNiceArray}$}"

    nl = r" \\ " if add_height_mm == 0 else rf" \\[{add_height_mm}mm] "
    rows = [" & ".join(row) for row in mat]
    return pre + nl.join(rows) + r" \\ " + post


def eigproblem_tex(
    eig: Mapping[str, Any],
    *,
    case: str = "S",
    formater: LatexFormatter = _default_formater,
    color: str = "blue",
    mmLambda: int = 8,
    mmS: int = 4,
    fig_scale: Optional[Union[int, float]] = None,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
    sz: Optional[Tuple[int, int]] = None,
) -> str:
    """Render an eigen/QR/SVD table TeX document using the migrated template.

    Parameters
    ----------
    eig:
        Pre-computed eigen/SVD description dictionary (algorithmic package owns this).
        Expected keys (case-dependent):
          - always: 'lambda' (distinct values), 'ma' (multiplicities), 'evecs' (groups)
          - optional: 'sigma', 'qvecs', 'uvecs'
    case:
        'S' for eigenvectors S, 'Q' for orthonormal eigenvectors Q, 'SVD' for SVD.
    formater:
        Converts scalar entries to LaTeX strings (e.g. sympy.latex).
    color:
        xcolor color name (e.g. 'blue', 'RoyalBlue', 'DarkGreen').
    mmLambda, mmS:
        Column spacing (mm) for diagonal/matrix blocks.
    fig_scale:
        If provided, wraps the content in ``\\scalebox{<fig_scale>}{% ... }``.
        This matches the legacy template convention.
    preamble:
        TeX inserted after the scale wrapper and before the tabular. Use for
        ``\\NiceMatrixOptions`` etc.
    sz:
        Matrix size (M, N) for SVD tables. If omitted, defaults to (N, N) where
        N = sum(ma).
    """
    if "lambda" not in eig or "ma" not in eig or "evecs" not in eig:
        missing = [k for k in ("lambda", "ma", "evecs") if k not in eig]
        raise KeyError(f"eigproblem_tex missing required keys: {missing}")

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

    # Values rows
    sigmas_row = None
    if case.upper() == "SVD" and "sigma" in eig:
        sig_cells = _mk_values(list(eig["sigma"]), formater=formater, zero_blank=True)
        sigmas_row = " & ".join(sig_cells) + r" \\"
    lambdas_row = " & ".join(_mk_values(lambdas_distinct, formater=formater)) + r" \\"
    mas_row = " & ".join(_mk_values(multiplicities, formater=formater)) + r" \\"

    # Vector blocks
    evecs_row = _mk_vector_blocks(eig["evecs"], formater=formater) + r" \\"

    orthonormal_row = None
    left_singular_matrix = None
    if case.upper() == "Q":
        if "qvecs" in eig:
            orthonormal_row = _mk_vector_blocks(eig["qvecs"], formater=formater, add_height_mm=1) + r" \\"
    elif case.upper() == "SVD":
        if "qvecs" in eig:
            orthonormal_row = _mk_vector_blocks(eig["qvecs"], formater=formater, add_height_mm=1) + r" \\"
        # Left singular vectors are shown as a matrix (U) below, if provided.
        if "uvecs" in eig:
            left_singular_matrix = _mk_vecs_matrix(
                eig["uvecs"], formater=formater, sz=sz[0], mm=mmS
            )

    # Matrices (diagonal + eigen/singular vector matrix)
    if case.upper() == "SVD" and "sigma" in eig:
        diag_values = list(eig["sigma"])
        lambda_matrix = _mk_diag_matrix(diag_values, multiplicities, formater=formater, sz=sz, mm=mmLambda)
    else:
        lambda_matrix = _mk_diag_matrix(lambdas_distinct, multiplicities, formater=formater, sz=sz, mm=mmLambda)

    if case.upper() == "S":
        evecs_matrix = _mk_vecs_matrix(eig["evecs"], formater=formater, sz=sz[1], mm=mmS)
    else:
        qvecs = eig.get("qvecs")
        evecs_matrix = _mk_vecs_matrix(qvecs, formater=formater, sz=sz[1], mm=mmS) if qvecs else None

    # Matrix name labels
    if case.upper() == "S":
        matrix_names = [r"\Lambda", "S"]
    elif case.upper() == "Q":
        matrix_names = [r"\Lambda", "Q"]
    else:
        matrix_names = [r"\Sigma", "V", "U"]

    # Figure scaling wrapper string (legacy convention)
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


def eigproblem_svg(
    eig: Mapping[str, Any],
    *,
    case: str = "S",
    formater: LatexFormatter = _default_formater,
    color: str = "blue",
    mmLambda: int = 8,
    mmS: int = 4,
    fig_scale: Optional[Union[int, float]] = None,
    preamble: str = r" \NiceMatrixOptions{cell-space-limits = 1pt}" + "\n",
    sz: Optional[Tuple[int, int]] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
) -> str:
    """Render the eigen/QR/SVD table to SVG via the strict rendering boundary."""
    tex = eigproblem_tex(
        eig,
        case=case,
        formater=formater,
        color=color,
        mmLambda=mmLambda,
        mmS=mmS,
        fig_scale=fig_scale,
        preamble=preamble,
        sz=sz,
    )
    return render_svg(tex, toolchain_name=toolchain_name, crop=crop, padding=padding)
