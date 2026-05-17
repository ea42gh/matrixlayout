import pathlib

import pytest


def _has_ge_template() -> bool:
    try:
        import matrixlayout
    except Exception:
        return False
    tpl = pathlib.Path(matrixlayout.__file__).resolve().parent / "templates" / "ge.tex.j2"
    return tpl.exists()


def test_render_ge_tex_smoke_builds_tex():
    if not _has_ge_template():
        pytest.skip("matrixlayout GE template not available")

    from matrixlayout.ge import render_ge_tex

    matrices = [
        [None, [[1, 2, 3], [4, 5, 6]]],
        [[[1, 0], [0, 1]], [[1, 0, 0], [0, 1, 0]]],
    ]

    tex = render_ge_tex(matrices=matrices, n_rhs=1, body_preamble="")
    assert "\\begin{NiceArray}" in tex
    assert "\\SubMatrix" in tex
    # RHS partition should appear in the pNiceArray column spec.
    assert r"\begin{NiceArray}[vlines-in-sub-matrix = I]{rr@{\hspace{6mm}}rr|r}" in tex


def test_render_ge_tex_accepts_legacy_nrhs_keyword():
    if not _has_ge_template():
        pytest.skip("matrixlayout GE template not available")

    from matrixlayout.ge import render_ge_tex

    matrices = [[None, [[1, 2, 3], [4, 5, 6]]]]
    tex = render_ge_tex(matrices=matrices, n_rhs=1, body_preamble="")
    assert r"\begin{NiceArray}[vlines-in-sub-matrix = I]{rr@{\hspace{6mm}}rr|r}" in tex


def test_render_ge_tex_callouts_enable_extra_nodes():
    if not _has_ge_template():
        pytest.skip("matrixlayout GE template not available")

    from matrixlayout.ge import render_ge_tex

    matrices = [[None, [[1]]], [[[1]], [[2]]]]
    tex = render_ge_tex(matrices=matrices, callouts=True, body_preamble="")
    line = next(line for line in tex.splitlines() if "NiceArray" in line and "begin" in line)
    assert "create-extra-nodes" in line


def test_render_ge_tex_rowechelon_paths_live_in_existing_tikzpicture():
    if not _has_ge_template():
        pytest.skip("matrixlayout GE template not available")

    from matrixlayout.ge import render_ge_tex

    path = r"\draw[blue] let \p1 = (A0.north west), \p2 = (A0.south east) in (\x1,\y1) -- (\x2,\y2);"
    tex = render_ge_tex(
        matrices=[[[1, 2], [3, 4]]],
        rowechelon_paths=[path],
        create_medium_nodes=True,
        body_preamble="",
    )

    assert path in tex
    assert r"\tikz \draw" not in tex
    assert tex.count(r"\begin{tikzpicture}") == 1
