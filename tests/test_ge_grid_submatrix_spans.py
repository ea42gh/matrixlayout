from matrixlayout.ge import ge_grid_submatrix_spans


def test_ge_grid_submatrix_spans_default_names_and_coords():
    # Legacy 2-column GE layout: [[E?, A?], ...]
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[5, 6], [7, 8]]],
    ]

    spans = ge_grid_submatrix_spans(matrices)
    names = [s.name for s in spans]

    # Row 0 has only an A-block; row 1 has E and A blocks.
    assert names == ["A0", "E1", "A1"]

    # A0 spans rows 1..2 and cols 3..4 (E column inferred as width=2).
    a0 = spans[0]
    assert (a0.row_start, a0.col_start, a0.row_end, a0.col_end) == (1, 3, 2, 4)

    # E1 spans rows 3..4 and cols 1..2.
    e1 = spans[1]
    assert (e1.row_start, e1.col_start, e1.row_end, e1.col_end) == (3, 1, 4, 2)

    # A1 spans rows 3..4 and cols 3..4.
    a1 = spans[2]
    assert (a1.row_start, a1.col_start, a1.row_end, a1.col_end) == (3, 3, 4, 4)


def test_ge_grid_submatrix_spans_delimiter_node_names():
    matrices = [[[1]], [[2]]]

    # Single-column grid => names are M0r (block-col based).
    spans = ge_grid_submatrix_spans(matrices)

    assert [s.name for s in spans] == ["M00", "M01"]
    assert spans[0].left_delim_node == "M00-left"
    assert spans[0].right_delim_node == "M00-right"
