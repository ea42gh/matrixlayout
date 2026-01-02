import os

import pytest

from matrixlayout.backsubst import backsubst_tex


def test_backsubst_tex_sections_toggle():
    tex = backsubst_tex(
        preamble="%P",
        system_txt="SYS",
        cascade_txt=["C1", "C2"],
        solution_txt="SOL",
        show_system=True,
        show_cascade=False,
        show_solution=True,
    )

    assert "%P" in tex
    assert "SYS" in tex
    assert "SOL" in tex
    assert "C1" not in tex
    assert "C2" not in tex


def test_backsubst_tex_includes_cascade_lines_in_order():
    tex = backsubst_tex(
        cascade_txt=("C1", "C2", "C3"),
        show_system=False,
        show_cascade=True,
        show_solution=False,
    )

    assert tex.index("C1") < tex.index("C2") < tex.index("C3")


def test_backsubst_tex_scalebox_when_fig_scale_set():
    tex = backsubst_tex(system_txt="SYS", show_cascade=False, show_solution=False, fig_scale=0.8)
    assert "\\scalebox" in tex
    assert "{ 0.8 }" in tex
    # Regression guard: display math cannot live directly in \scalebox's LR box.
    # Ensure the template nests a minipage inside the \scalebox argument.
    assert tex.index("\\scalebox") < tex.index("\\begin{minipage}")


@pytest.mark.render
def test_backsubst_svg_smoke():
    """Optional end-to-end test.

    Disabled by default to avoid hard dependency on a working TeX toolchain in
    every development environment.
    """

    if os.environ.get("MATRIXLAYOUT_RUN_RENDER_TESTS") != "1":
        pytest.skip("Set MATRIXLAYOUT_RUN_RENDER_TESTS=1 to enable render tests")

    jupyter_tikz = pytest.importorskip("jupyter_tikz")

    from matrixlayout.backsubst import backsubst_svg

    svg = backsubst_svg(system_txt=r"$x=1$", show_cascade=False, show_solution=False)
    assert isinstance(svg, str)
    assert "<svg" in svg
