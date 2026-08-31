import shutil

import pytest

from matrixlayout.ge import _tex, render_ge_tex


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
    tex_out = _tex(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        outer_delims=True,
        outer_delims_span=(2, 2),
        landscape=False,
    )
    assert r"\begin{NiceArray}" in tex_out
    assert r"\SubMatrix({1-1}{2-2})[name=A0x0]" in tex_out

@pytest.mark.parametrize("n_rhs", [-1, 3, [1, 2], [1, -1], [1, "b"], True])
def test_render_ge_tex_rejects_invalid_n_rhs(n_rhs):
    with pytest.raises(ValueError, match="n_rhs"):
        render_ge_tex(matrices=[[[1, 2]]], n_rhs=n_rhs)


def test_render_ge_tex_accepts_zero_and_full_width_n_rhs():
    render_ge_tex(matrices=[[[1, 2]]], n_rhs=0)
    render_ge_tex(matrices=[[[1, 2]]], n_rhs=2)
    render_ge_tex(matrices=[[[1, 2]]], n_rhs=[1, 1])


@pytest.mark.render
def test_ge_svg_smoke():
    pytest.importorskip("jupyter_tikz")

    from matrixlayout.ge import _svg

    svg_out = _svg(
        mat_rep="1 & 0 \\\\ 0 & 1",
        mat_format="cc",
        outer_delims=True,
        outer_delims_span=(2, 2),
        landscape=False,
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=(2, 2, 2, 2),
    )
    assert "<svg" in svg_out

