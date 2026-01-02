import os
import pytest

from matrixlayout.ge import ge_tex


def test_ge_tex_contains_env_and_format():
    tex = ge_tex(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        landscape=False,
    )
    assert r"\begin{pNiceArray}" in tex  # default delimiter environment
    assert r"{cc}" in tex
    assert "1 & 0" in tex


def test_ge_tex_submatrix_emits_SubMatrix():
    tex = ge_tex(
        mat_rep="1 & 2 \\\\ 3 & 4",
        mat_format="cc",
        submatrix_locs=[("name=SM", "(1-1)(2-2)")],
        submatrix_names=[r"\node at (SM-center) {A};"],
        landscape=False,
    )
    assert r"\SubMatrix[name=SM](1-1)(2-2)" in tex
    assert r"\node at (SM-center) {A};" in tex


@pytest.mark.render
def test_ge_svg_smoke():
    if os.environ.get("MATRIXLAYOUT_RUN_RENDER_TESTS") != "1":
        pytest.skip("opt-in render test")
    from matrixlayout.ge import ge_svg

    svg = ge_svg(
        mat_rep="1 & 2 \\\\ 3 & 4",
        mat_format="cc",
        submatrix_locs=[("name=SM", "(1-1)(2-2)")],
        submatrix_names=[r"\node at (SM-center) {A};"],
        landscape=False,
    )
    assert "<svg" in svg
