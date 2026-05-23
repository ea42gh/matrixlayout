import re

import pytest
import sympy as sym

import matrixlayout
from matrixlayout.eigproblem import (
    _display_vector_factor,
    _display_matrix_factor,
    _format_vector_for_display,
    _coerce_matrix_size,
    _is_zero_like,
    _mk_diag_matrix,
    _mk_vector_blocks,
    _mk_sigma_matrix,
    _mk_values,
    _mk_vecs_matrix,
    _positive_rational_gcd,
)


def test_templates_load():
    env = matrixlayout.get_environment()
    env.get_template("backsubst.tex.j2")
    env.get_template("eigproblem.tex.j2")


def _sample_eig():
    # Two distinct eigenvalues with multiplicity 1 each.
    return {
        "lambda": [1, 2],
        "ma": [1, 1],
        "evecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "qvecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "sigma": [3, 0],
        "uvecs": [
            [[1, 0]],
            [[0, 1]],
        ],
    }


def test_render_eig_tex_case_S():
    tex = matrixlayout.render_eig_tex(_sample_eig(), case="S", formatter=str, fig_scale=None)
    assert r"\begin{tabular}" in tex
    assert r"\usepackage[margin=0cm,paperwidth=90in,paperheight=90in," in tex
    assert r"$\color" in tex
    assert r"\sigma" not in tex  # sigma row is SVD-only
    assert r"{\parbox{2cm}{\textcolor" in tex  # eigenbasis label
    # Should render eigenvector matrix row (S)
    assert re.search(r"\\color\{[^}]+\}\{\s*S\s*=\s*\}", tex) is not None


def test_render_eig_tex_case_Q_includes_orthonormal():
    tex = matrixlayout.render_eig_tex(_sample_eig(), case="Q", formatter=str, fig_scale=None)
    assert "orthonormal basis for $E_\\lambda$" in tex
    # In Q case, matrix label should be Q
    assert re.search(r"\\color\{[^}]+\}\{\s*Q\s*=\s*\}", tex) is not None


def test_render_eig_tex_case_SVD_includes_sigma_and_U():
    tex = matrixlayout.render_eig_tex(_sample_eig(), case="SVD", formatter=str, fig_scale=1.2, sz=(2, 2))
    assert r"\sigma" in tex
    assert re.search(r"\\color\{[^}]+\}\{\s*\\Sigma\s*=\s*\}", tex) is not None
    assert re.search(r"\\color\{[^}]+\}\{\s*U\s*=\s*\}", tex) is not None
    assert r"\begin{minipage}" not in tex


def test_render_eig_tex_svd_uses_spec_size_when_sz_missing():
    spec = {
        "lambda": [4],
        "ma": [1],
        "sigma": [2],
        "evecs": [[[1, 0]]],
        "qvecs": [[[1, 0]]],
        "uvecs": [[[1, 0, 0]]],
        "sz": (3, 2),
    }
    tex = matrixlayout.render_eig_tex(spec, case="SVD", formatter=str, fig_scale=None)
    assert r"\begin{pNiceArray}{c@{\hspace{8mm}}c}" in tex
    assert r"2 & 0 \\ 0 & 0 \\ 0 & 0 \\" in tex


def test_eig_matrix_size_helper_validates_two_item_size():
    assert _coerce_matrix_size(None, default=(2, 2)) == (2, 2)
    assert _coerce_matrix_size(["3", 2.0], default=(2, 2)) == (3, 2)

    with pytest.raises(ValueError, match="2-item"):
        _coerce_matrix_size([3], default=(2, 2))

    with pytest.raises(ValueError, match="2-item"):
        matrixlayout.render_eig_tex({**_sample_eig(), "sz": [3]}, case="SVD", formatter=str)


def test_eig_zero_like_and_values_helpers():
    class IsZero:
        is_zero = True

    class NotZero:
        is_zero = False

    class FloatBad:
        @property
        def is_zero(self):
            raise TypeError("unknown")

        def __float__(self):
            raise TypeError("not numeric")

    assert _is_zero_like(None) is False
    assert _is_zero_like(" 0 ") is True
    assert _is_zero_like("x") is False
    assert _is_zero_like(IsZero()) is True
    assert _is_zero_like(NotZero()) is False
    assert _is_zero_like(0.0) is True
    assert _is_zero_like(FloatBad()) is False
    assert _mk_values([3, 0, "0"], formatter=str, zero_blank=True) == ["$3$", "", "$$", "", "$$"]


def test_eig_matrix_helpers_cover_spacing_and_invalid_shapes():
    diag = _mk_diag_matrix([2], [2], formatter=str, sz=(2, 2), extra_space=r"\quad ")
    assert r"\quad 2" in diag
    assert r"0\quad" in diag

    sigma = _mk_sigma_matrix([3], [1], formatter=str, sz=(2, 3), extra_space=r"\quad ")
    assert r"\begin{pNiceArray}{c@{\hspace{8mm}}c@{\hspace{8mm}}c}" in sigma
    assert r"\quad 3" in sigma

    try:
        _mk_sigma_matrix([1], [1], formatter=str, sz=(0, 2))
    except ValueError as exc:
        assert "Invalid sz" in str(exc)
    else:
        raise AssertionError("expected invalid sigma shape to raise")


def test_eig_vecs_matrix_returns_none_for_unusable_vector_sets():
    assert _mk_vecs_matrix([], formatter=str, sz=2) is None
    assert _mk_vecs_matrix([[[1, 2, 3]]], formatter=str, sz=2) is None
    assert _mk_vecs_matrix([[[1, 0]]], formatter=str, sz=2) is None


def test_positive_rational_gcd_and_display_vector_factor_helpers():
    assert _positive_rational_gcd([0, sym.Rational(2, 3), sym.Rational(4, 9)]) == sym.Rational(2, 9)
    assert _positive_rational_gcd([sym.sqrt(2)]) == 1
    assert _display_vector_factor([0, 0]) == (1, None)

    factor, reduced = _display_vector_factor(
        [
            sym.sqrt(2) * (-69 + sym.sqrt(5017)) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017))),
            8 * sym.sqrt(2) / sym.sqrt(5017 - 69 * sym.sqrt(5017)),
        ]
    )
    assert factor == sym.sqrt(2) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017)))
    assert reduced == [-69 + sym.sqrt(5017), 16]

    matrix_factor, matrix_reduced = _display_matrix_factor(
        [
            [sym.Rational(1, 2), sym.Rational(3, 4)],
            [0, sym.Rational(5, 6)],
        ]
    )
    assert matrix_factor == 12
    assert matrix_reduced == [[6, 9], [0, 10]]


def test_format_vector_for_display_covers_factored_and_plain_paths():
    seen = []

    def _decorate(i, value, cell):
        seen.append((i, value, cell))
        return f"[{cell}]"

    plain = _format_vector_for_display([1, 2], formatter=str, nl=r" \\ ", factor_common=False)
    assert plain == r"$\begin{pNiceArray}{r}1 \\ 2 \end{pNiceArray}$"

    factored = _format_vector_for_display(
        [
            sym.sqrt(2) * (-69 + sym.sqrt(5017)) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017))),
            8 * sym.sqrt(2) / sym.sqrt(5017 - 69 * sym.sqrt(5017)),
        ],
        formatter=matrixlayout.formatting.latexify,
        nl=r" \\[1mm] ",
        factor_common=True,
        decorators_apply=_decorate,
    )
    assert r"\frac{\sqrt{2}}{2 \sqrt{5017 - 69 \sqrt{5017}}}\," in factored
    assert r"\begin{pNiceArray}{r}[-69 + \sqrt{5017}] \\[1mm] [16] \end{pNiceArray}" in factored
    assert seen[0][0] == 0
    assert seen[1][0] == 1


def test_mk_vector_blocks_covers_factored_latexify_and_strict_decorators():
    vec_groups = [
        [
            [
                sym.sqrt(2) * (-69 + sym.sqrt(5017)) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017))),
                8 * sym.sqrt(2) / sym.sqrt(5017 - 69 * sym.sqrt(5017)),
            ]
        ]
    ]

    block = _mk_vector_blocks(vec_groups, formatter=matrixlayout.formatting.latexify, add_height_mm=1)
    assert r"\frac{\sqrt{2}}{2 \sqrt{5017 - 69 \sqrt{5017}}}\," in block
    assert r"-69 + \sqrt{5017}" in block

    with pytest.raises(ValueError, match="decorator selector did not match any entries"):
        _mk_vector_blocks(
            [[[1, 0]]],
            formatter=str,
            decorators=[{"target": "eigenbasis", "entries": [(9, 9, 9)], "decorator": lambda tex: tex}],
            target_name="eigenbasis",
            strict=True,
        )


def test_svd_matrix_rows_stay_entrywise_while_vector_rows_factor():
    tex = matrixlayout.render_eig_tex(
        {
            "lambda": [5017, 1],
            "ma": [1, 1],
            "sigma": [1, 0],
            "evecs": [
                [[
                    sym.sqrt(2) * (-69 + sym.sqrt(5017)) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017))),
                    8 * sym.sqrt(2) / sym.sqrt(5017 - 69 * sym.sqrt(5017)),
                ]],
                [[0, 1]],
            ],
            "qvecs": [
                [[
                    sym.sqrt(2) * (-69 + sym.sqrt(5017)) / (2 * sym.sqrt(5017 - 69 * sym.sqrt(5017))),
                    8 * sym.sqrt(2) / sym.sqrt(5017 - 69 * sym.sqrt(5017)),
                ]],
                [[0, 1]],
            ],
            "uvecs": [
                [[1, 0]],
                [[0, 1]],
            ],
            "sz": (2, 2),
        },
        case="SVD",
        formatter=matrixlayout.formatting.latexify,
        fig_scale=None,
    )

    assert r"\frac{\sqrt{2}}{2 \sqrt{5017 - 69 \sqrt{5017}}}\,\begin{pNiceArray}{r}-69 + \sqrt{5017}" in tex
    assert r"\frac{\sqrt{2} \left(-69 + \sqrt{5017}\right)}{2 \sqrt{5017 - 69 \sqrt{5017}}}" in tex
    assert r"\frac{\sqrt{2}}{2 \sqrt{5017 - 69 \sqrt{5017}}}\,\begin{pNiceArray}{r}\frac{\sqrt{2} \left(-69 + \sqrt{5017}\right)}" not in tex


def test_matrix_factor_out_can_target_selected_svd_blocks():
    tex = matrixlayout.render_eig_tex(
        {
            "lambda": [1, 2],
            "ma": [1, 1],
            "sigma": [sym.Rational(1, 2), sym.Rational(1, 3)],
            "evecs": [
                [[sym.Rational(1, 2), 0]],
                [[0, sym.Rational(1, 3)]],
            ],
            "qvecs": [
                [[sym.Rational(1, 2), 0]],
                [[0, sym.Rational(1, 3)]],
            ],
            "uvecs": [
                [[sym.Rational(1, 4), 0]],
                [[0, sym.Rational(1, 5)]],
            ],
            "sz": (2, 2),
        },
        case="SVD",
        formatter=str,
        fig_scale=None,
        matrix_factor_out={"sigma_matrix": True, "u": True},
    )

    assert r"\begin{pNiceArray}{c@{\hspace{8mm}}c}6\,3 & 0 \\ 0 & 2" in tex
    assert r"\begin{pNiceArray}{r@{\hspace{4mm}}r}20\,5 & 0 \\ 0 & 4" in tex
    assert r"\begin{pNiceArray}{r@{\hspace{4mm}}r}1/2 & 0 \\ 0 & 1/3" in tex


def test_render_eig_tex_missing_keys_and_q_case_without_qvecs():
    with pytest.raises(KeyError, match="missing required keys"):
        matrixlayout.render_eig_tex({"lambda": [1], "ma": [1]}, case="S", formatter=str)

    tex = matrixlayout.render_eig_tex(
        {"lambda": [1], "ma": [1], "evecs": [[[1]]]},
        case="Q",
        formatter=str,
        fig_scale=None,
    )
    assert "orthonormal basis for $E_\\lambda$" not in tex
    assert re.search(r"\\color\{[^}]+\}\{\s*Q\s*=\s*\}", tex) is None
