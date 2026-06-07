import shutil
from pathlib import Path

import pytest

from matrixlayout.ge import render_ge_svg

jupyter_tikz = pytest.importorskip("jupyter_tikz")
from svg_golden import assert_svg_matches_golden


@pytest.mark.render
def test_render_ge_svg_golden():
    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not installed")
    if shutil.which("pdftocairo") is None:
        pytest.skip("pdftocairo not installed")

    matrices = [[None, [[1, 2], [3, 4]]]]
    svg = render_ge_svg(matrices=matrices)

    golden = Path(__file__).parent / "ge_basic.svg"
    assert_svg_matches_golden(svg, golden)


@pytest.mark.render
def test_render_ge_decorations_callout_golden():
    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not installed")
    if shutil.which("pdftocairo") is None:
        pytest.skip("pdftocairo not installed")

    svg = render_ge_svg(
        matrices=[[[1, 0], [0, 1]]],
        decorations=[
            {"grid": (0, 0), "entries": [(0, 0), (1, 1)], "background": "yellow!25"},
        ],
        callouts=[
            {
                "grid": (0, 0),
                "label": "R",
                "side": "right",
                "angle_deg": -35,
                "length_mm": 8,
            },
        ],
        create_medium_nodes=True,
    )

    golden = Path(__file__).parent / "ge_decorations_callout.svg"
    assert_svg_matches_golden(svg, golden)
