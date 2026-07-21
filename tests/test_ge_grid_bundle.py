from __future__ import annotations

import pytest

from matrixlayout.ge import grid_bundle, grid_submatrix_spans, render_ge_tex


def test_ge_grid_bundle_returns_tex_and_spans_consistently():
    # One-layer stack 2-column layout: [[None, A0]]
    matrices = [[None, [[1, 2], [3, 4]]]]

    b = grid_bundle(matrices=matrices, n_rhs=0)

    # TeX should match render_ge_tex for the same inputs.
    assert b.tex == render_ge_tex(matrices=matrices, n_rhs=0)

    # Spans should match the dedicated helper.
    assert b.submatrix_spans == grid_submatrix_spans(matrices, n_rhs=0)

    # Basic sanity: A0 is the only non-empty block and must be named.
    assert any(s.name == "A0" for s in b.submatrix_spans)
    assert "name=A0" in b.tex


def test_ge_grid_bundle_requires_matrices():
    with pytest.raises(ValueError, match="requires `matrices`"):
        grid_bundle()
