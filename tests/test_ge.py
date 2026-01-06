import os
import pytest

from matrixlayout.ge import ge_tex


def test_ge_tex_contains_SubMatrix_when_requested():
    tex = ge_tex(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        outer_delims=True,
        outer_delims_span=(2, 2),
        landscape=False,
    )
    assert r"\begin{NiceArray}" in tex
    assert r"\SubMatrix({1-1}{2-2})[name=A0x0]" in tex


@pytest.mark.render
def test_ge_svg_smoke():
    if os.environ.get("MATRIXLAYOUT_RUN_RENDER_TESTS") != "1":
        pytest.skip("opt-in render test")
    from matrixlayout.ge import ge_svg

    svg = ge_svg(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        outer_delims=True,
        outer_delims_span=(2, 2),
        landscape=False,
    )
    assert "<svg" in svg
