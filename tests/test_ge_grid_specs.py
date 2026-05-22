import pytest

from matrixlayout.ge import grid_highlight_specs, grid_line_specs, grid_submatrix_spans
from matrixlayout.ge_grid_specs import normalize_range


def test_grid_line_specs_filters_targets_and_deduplicates_valid_lines():
    matrices = [
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[10, 11], [12, 13]]],
    ]

    specs = grid_line_specs(
        matrices,
        targets=[(0, 0), (9, 9)],
        hlines=[2, 1, 1, 99, 0],
        vlines={2, 1, -1, 99},
    )

    assert specs == [("delimiters/color=.,hlines={1,2},vlines={1,2}", "1-1", "3-3")]


def test_grid_line_specs_omits_empty_or_out_of_range_lines():
    matrices = [[[[1, 2], [3, 4]]]]

    assert grid_line_specs(matrices, targets=[(0, 0)], hlines=9, vlines=-1) == []
    assert grid_line_specs(matrices, targets=[(9, 9)], hlines=1, vlines=1) == []


def test_normalize_range_edge_cases():
    assert normalize_range(None, 3) == (0, 2)
    assert normalize_range(slice(1, 3), 4) == (1, 2)
    assert normalize_range("2:0", 4) == (0, 2)
    assert normalize_range(":1", 4) == (0, 1)
    assert normalize_range("2:", 4) == (2, 3)
    assert normalize_range((3, 1), 5) == (1, 3)
    assert normalize_range([2, 0, 2], 3) == (0, 2)
    assert normalize_range([], 3) == (0, -1)
    assert normalize_range(None, 0) == (0, -1)

    with pytest.raises(ValueError, match="rows/cols"):
        normalize_range(object(), 3)


def test_grid_highlight_specs_dict_tuple_empty_missing_and_invalid_forms():
    matrices = [
        [[[1, 2], [3, 4]], [[5], [6]]],
    ]

    specs = grid_highlight_specs(
        matrices,
        blocks=[
            {"grid": (0, 0), "rows": "0:0", "cols": "1:1", "color": "red", "padding_pt": 2},
            ((0, 1), None, None, "blue"),
            {"grid": (9, 9), "rows": None, "cols": None},
            {"grid": (0, 0), "rows": [], "cols": []},
        ],
        color="yellow",
    )

    assert specs == [
        r"\tikz \node [fill=red, inner sep=2.0pt, fit=(1-2-medium) (1-2-medium)] {};",
        r"\tikz \node [fill=blue, inner sep=1.0pt, fit=(1-3-medium) (2-3-medium)] {};",
    ]

    with pytest.raises(ValueError, match="grid=\\(row,col\\)"):
        grid_highlight_specs(matrices, blocks=[{"grid": (0,)}])
    with pytest.raises(ValueError, match="block highlight"):
        grid_highlight_specs(matrices, blocks=[object()])


def test_grid_submatrix_spans_label_offsets_and_legacy_names():
    matrices = [[None, [[1, 2], [3, 4]]]]

    spans = grid_submatrix_spans(
        matrices,
        label_rows=[{"grid": (0, 1), "side": "above", "labels": [["x", "y"]]}],
        label_cols=[{"grid": (0, 1), "side": "left", "labels": [["r1"], ["r2"]]}],
        legacy_submatrix_names=True,
    )

    assert [(span.name, span.row_start, span.col_start, span.row_end, span.col_end) for span in spans] == [
        ("A0x1", 2, 4, 3, 5)
    ]
