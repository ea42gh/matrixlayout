import shutil
from pathlib import Path

import pytest

from jupyter_tikz.svg_normalize import normalize_svg
from matrixlayout.ge import render_ge_svg


@pytest.mark.render
def test_render_ge_svg_golden():
    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not installed")
    if shutil.which("pdftocairo") is None:
        pytest.skip("pdftocairo not installed")

    matrices = [[None, [[1, 2], [3, 4]]]]
    svg = normalize_svg(render_ge_svg(matrices=matrices))

    golden = Path(__file__).parent / "ge_basic.svg"
    expected = normalize_svg(golden.read_text())
    assert svg == expected
