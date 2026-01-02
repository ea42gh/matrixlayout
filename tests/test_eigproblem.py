import re

import matrixlayout


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


def test_eigproblem_tex_case_S():
    tex = matrixlayout.eigproblem_tex(_sample_eig(), case="S", formater=str, fig_scale=None)
    assert r"\begin{tabular}" in tex
    assert r"$\color" in tex
    assert r"\sigma" not in tex  # sigma row is SVD-only
    assert r"{\parbox{2cm}{\textcolor" in tex  # eigenbasis label
    # Should render eigenvector matrix row (S)
    assert re.search(r"\\color\{[^}]+\}\{\s*S\s*=\s*\}", tex) is not None


def test_eigproblem_tex_case_Q_includes_orthonormal():
    tex = matrixlayout.eigproblem_tex(_sample_eig(), case="Q", formater=str, fig_scale=None)
    assert "orthonormal basis for $E_\\lambda$" in tex
    # In Q case, matrix label should be Q
    assert re.search(r"\\color\{[^}]+\}\{\s*Q\s*=\s*\}", tex) is not None


def test_eigproblem_tex_case_SVD_includes_sigma_and_U():
    tex = matrixlayout.eigproblem_tex(_sample_eig(), case="SVD", formater=str, fig_scale=1.2, sz=(2, 2))
    assert r"\sigma" in tex
    assert re.search(r"\\color\{[^}]+\}\{\s*\\Sigma\s*=\s*\}", tex) is not None
    assert re.search(r"\\color\{[^}]+\}\{\s*U\s*=\s*\}", tex) is not None
