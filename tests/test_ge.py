import os

import pytest

from matrixlayout.ge import ge_tex


def test_ge_tex_includes_core_sections():
    tex = ge_tex(
        mat_rep="1 & 2 \\ 3 & 4",
        mat_format="cc",
        mat_options="",
        preamble="\\def\\Foo{bar}",
        extension="",
        codebefore=["% codebefore hook"],
        submatrix_locs=[("name=SM", "(1-1)(2-2)")],
        submatrix_names=["% submatrix label hook"],
        pivot_locs=[(" (1-1) ", "red")],
        txt_with_locs=[("(0,0)", "hello", "black")],
        rowechelon_paths=["% path hook"],
        fig_scale=None,
    )
    assert "\\begin{NiceArray}" in tex
    assert "1 & 2" in tex
    assert "\\SubMatrix" in tex
    assert "txt_with_locs" not in tex  # ensure rendered, not literal variable name
    assert "hello" in tex
    assert "\\node [draw" in tex


@pytest.mark.render
def test_ge_svg_smoke():
    if os.environ.get("MATRIXLAYOUT_RUN_RENDER_TESTS") != "1":
        pytest.skip("opt-in render test")
    from matrixlayout.ge import ge_svg

    svg = ge_svg(
        mat_rep="1 & 0 \\ 0 & 1",
        mat_format="cc",
    )
    assert "<svg" in svg
