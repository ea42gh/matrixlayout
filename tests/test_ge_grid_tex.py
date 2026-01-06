import pathlib

import pytest


def _has_ge_template() -> bool:
    try:
        import matrixlayout
    except Exception:
        return False
    tpl = pathlib.Path(matrixlayout.__file__).resolve().parent / "templates" / "ge.tex.j2"
    return tpl.exists()


def test_ge_grid_tex_smoke_builds_tex():
    if not _has_ge_template():
        pytest.skip("matrixlayout GE template not available")

    from matrixlayout.ge import ge_grid_tex

    matrices = [
        [None, [[1, 2, 3], [4, 5, 6]]],
        [[[1, 0], [0, 1]], [[1, 0, 0], [0, 1, 0]]],
    ]

    tex = ge_grid_tex(matrices=matrices, Nrhs=1, preamble="")
    assert "\\begin{NiceArray}" in tex
    assert "\\SubMatrix" in tex
    # RHS partition should appear in the pNiceArray column spec.
    assert r"\begin{NiceArray}[vlines-in-sub-matrix = I]{rr@{\hspace{6mm}}rr|r}" in tex
