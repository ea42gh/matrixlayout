import shutil

import pytest

from matrixlayout.backsubst import backsubst_tex


def _pick_toolchain_name_or_skip() -> str:
    """Pick a working SVG toolchain.

    Render tests are enabled by default. They are skipped only when the
    external TeX/converter binaries are unavailable (or if the user opts out via
    --skip-render-tests / ITIKZ_SKIP_RENDER_TESTS=1, handled in repo conftest).
    """

    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not found")

    if shutil.which("dvisvgm") is not None:
        return "pdftex_dvisvgm"
    if shutil.which("pdftocairo") is not None:
        return "pdftex_pdftocairo"
    if shutil.which("pdf2svg") is not None:
        return "pdftex_pdf2svg"

    pytest.skip("no SVG converter found (need dvisvgm, pdftocairo, or pdf2svg)")
    raise AssertionError("unreachable")


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
    """End-to-end smoke test: TeX -> SVG."""

    pytest.importorskip("jupyter_tikz")

    from matrixlayout.backsubst import backsubst_svg

    svg = backsubst_svg(
        system_txt=r"$x=1$",
        show_cascade=False,
        show_solution=False,
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=(2, 2, 2, 2),
    )
    assert isinstance(svg, str)
    assert "<svg" in svg
