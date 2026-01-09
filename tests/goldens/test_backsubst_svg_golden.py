from pathlib import Path

import pytest

from jupyter_tikz.svg_normalize import normalize_svg
from matrixlayout.backsubst import backsubst_svg


@pytest.mark.render
def test_backsubst_svg_golden():
    svg = normalize_svg(
        backsubst_svg(
            system_txt=r"$x_1 + x_2 = 3$",
            cascade_txt=[r"$x_2 = 1$", r"$x_1 = 2$"],
            solution_txt=r"$x = (2, 1)$",
        )
    )

    golden = Path(__file__).parent / "backsubst_basic.svg"
    expected = normalize_svg(golden.read_text())
    assert svg == expected
