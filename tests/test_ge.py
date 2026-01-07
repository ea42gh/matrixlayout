import shutil

import pytest

from matrixlayout.ge import ge_tex


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
    from matrixlayout.ge import ge_svg

    svg = ge_svg(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        outer_delims=True,
        outer_delims_span=(2, 2),
        landscape=False,
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=(2, 2, 2, 2),
    )
    assert "<svg" in svg
