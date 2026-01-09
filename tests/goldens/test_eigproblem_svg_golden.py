from pathlib import Path

import pytest

from jupyter_tikz.svg_normalize import normalize_svg
from matrixlayout.eigproblem import eigproblem_svg


@pytest.mark.render
def test_eigproblem_svg_golden():
    spec = {
        "lambda": [2],
        "ma": [1],
        "evecs": [[[1, 0]]],
        "qvecs": [[[1, 0]]],
        "sz": (2, 2),
    }
    svg = normalize_svg(eigproblem_svg(spec, case="Q", formatter=str))

    golden = Path(__file__).parent / "eigproblem_basic.svg"
    expected = normalize_svg(golden.read_text())
    assert svg == expected
