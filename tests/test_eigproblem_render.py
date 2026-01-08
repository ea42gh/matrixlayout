import shutil

import pytest


def _pick_toolchain_name_or_skip() -> str:
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


@pytest.mark.render
def test_eigproblem_svg_svd_smoke():
    pytest.importorskip("jupyter_tikz")

    from matrixlayout import eigproblem_svg

    spec = {
        "lambda": [4, 1],
        "ma": [1, 1],
        "sigma": [2, 1],
        "evecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "qvecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "uvecs": [
            [[1, 0, 0]],
            [[0, 1, 0]],
            [[0, 0, 1]],
        ],
        "sz": (3, 2),
    }

    svg = eigproblem_svg(
        spec,
        case="SVD",
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=(2, 2, 2, 2),
    )
    assert isinstance(svg, str)
    assert "<svg" in svg


@pytest.mark.render
def test_eigproblem_svg_svd_smoke_wide():
    pytest.importorskip("jupyter_tikz")

    from matrixlayout import eigproblem_svg

    spec = {
        "lambda": [9, 4],
        "ma": [1, 1],
        "sigma": [3, 2],
        "evecs": [
            [[1, 0, 0]],
            [[0, 1, 0]],
        ],
        "qvecs": [
            [[1, 0, 0]],
            [[0, 1, 0]],
        ],
        "uvecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "sz": (2, 3),
    }

    svg = eigproblem_svg(
        spec,
        case="SVD",
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=(2, 2, 2, 2),
    )
    assert isinstance(svg, str)
    assert "<svg" in svg
