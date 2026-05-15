import re

import pytest

import matrixlayout
from matrixlayout.eigproblem import (
    _coerce_matrix_size,
    _is_zero_like,
    _mk_diag_matrix,
    _mk_sigma_matrix,
    _mk_values,
    _mk_vecs_matrix,
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
