from pathlib import Path

import pytest

from matrixlayout.eigproblem import render_eig_svg

pytest.importorskip("jupyter_tikz")
from svg_golden import assert_svg_matches_golden


@pytest.mark.render
def test_render_eig_svg_golden():
    spec = {
        "lambda": [2],
        "ma": [1],
        "evecs": [[[1, 0]]],
        "qvecs": [[[1, 0]]],
        "sz": (2, 2),
    }
    svg = render_eig_svg(spec, case="Q", formatter=str)

    golden = Path(__file__).parent / "eigproblem_basic.svg"
    assert_svg_matches_golden(svg, golden)
