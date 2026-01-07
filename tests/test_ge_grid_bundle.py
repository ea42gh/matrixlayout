from __future__ import annotations

from matrixlayout.ge import ge_grid_bundle, ge_grid_submatrix_spans, ge_grid_tex


def test_ge_grid_bundle_returns_tex_and_spans_consistently():
    # One-layer legacy 2-column layout: [[None, A0]]
    matrices = [[None, [[1, 2], [3, 4]]]]

    b = ge_grid_bundle(matrices=matrices, Nrhs=0)

    # TeX should match ge_grid_tex for the same inputs.
    assert b.tex == ge_grid_tex(matrices=matrices, Nrhs=0)

    # Spans should match the dedicated helper.
    assert b.submatrix_spans == ge_grid_submatrix_spans(matrices, Nrhs=0)

    # Basic sanity: A0 is the only non-empty block and must be named.
    assert any(s.name == "A0" for s in b.submatrix_spans)
    assert "name=A0" in b.tex
