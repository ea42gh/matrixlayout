from pathlib import Path

import pytest

from matrixlayout.backsubst import backsubst_svg

pytest.importorskip("jupyter_tikz")
from svg_golden import assert_svg_matches_golden


@pytest.mark.render
def test_backsubst_svg_golden():
    svg = backsubst_svg(
        system_txt=r"$x_1 + x_2 = 3$",
        cascade_txt=[r"$x_2 = 1$", r"$x_1 = 2$"],
        solution_txt=r"$x = (2, 1)$",
    )

    golden = Path(__file__).parent / "backsubst_basic.svg"
    assert_svg_matches_golden(svg, golden)
