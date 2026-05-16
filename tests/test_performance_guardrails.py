from time import perf_counter

import pytest

from matrixlayout.ge import render_ge_tex


@pytest.mark.performance
def test_large_ge_grid_tex_assembly_stays_within_runtime_guardrail():
    """Catch accidental large regressions in pure-Python GE grid assembly."""

    block = [[i + j for j in range(10)] for i in range(10)]
    matrices = [[None, block]] + [[block, block] for _ in range(8)]

    start = perf_counter()
    tex = render_ge_tex(
        matrices=matrices,
        n_rhs=2,
        decorations=[
            {"grid": (1, 1), "entries": [(0, 0)], "background": "yellow!25"},
            {"grid": (8, 1), "submatrix": ("0:9", "0:0"), "outline": True},
        ],
        label_rows=[{"grid": (0, 1), "side": "above", "rows": [[f"x{j}" for j in range(10)]]}],
        label_cols=[{"grid": (8, 0), "side": "left", "cols": [[f"r{i}"] for i in range(10)]}],
    )
    elapsed = perf_counter() - start

    assert elapsed < 5.0
    assert tex.count(r"\SubMatrix") == 19
    assert "fill=yellow!25" in tex
