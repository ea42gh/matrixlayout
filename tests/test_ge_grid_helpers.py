import pytest

from matrixlayout.ge_grid import (
    as_2d_list,
    block_pad_left,
    block_pad_top,
    grid_block_padding,
    matrix_body_tex,
    normalize_grid_input,
    pnicearray_tex,
)


class ToListMatrix:
    def tolist(self):
        return [[1, 2], [3, 4]]


class Unsupported:
    pass


def test_as_2d_list_accepts_matrix_like_vectors_and_ragged_rows():
    assert as_2d_list(None) == ([], 0, 0)
    assert as_2d_list(ToListMatrix()) == ([[1, 2], [3, 4]], 2, 2)
    assert as_2d_list([1, 2]) == ([[1], [2]], 2, 1)
    assert as_2d_list([[1], [2, 3]]) == ([[1, ""], [2, 3]], 2, 2)


def test_as_2d_list_rejects_unsupported_objects():
    with pytest.raises(TypeError, match="Unsupported matrix-like object"):
        as_2d_list(Unsupported())


def test_normalize_grid_input_distinguishes_matrix_vector_and_grid():
    assert normalize_grid_input(None) == []
    assert normalize_grid_input("A") == [["A"]]
    assert normalize_grid_input([1, 2]) == [[1, 2]]
    assert normalize_grid_input([[1, 2], [3, 4]]) == [[[[1, 2], [3, 4]]]]
    assert normalize_grid_input([[[1, 2], [3, 4]]]) == [[[[1, 2], [3, 4]]]]
    assert normalize_grid_input([[None, [[1]]], [[[2]], [[3]]]]) == [[None, [[1]]], [[[2]], [[3]]]]


def test_block_padding_modes_and_errors():
    assert block_pad_left(4, 2, None) == 2
    assert block_pad_left(4, 2, "left") == 0
    assert block_pad_left(5, 2, "center") == 1
    assert block_pad_left(4, 2, "right") == 2
    assert block_pad_left(2, 2, "right") == 0

    assert block_pad_top(4, 2, None) == 2
    assert block_pad_top(4, 2, "top") == 0
    assert block_pad_top(5, 2, "center") == 1
    assert block_pad_top(4, 2, "bottom") == 2
    assert block_pad_top(2, 2, "bottom") == 0

    with pytest.raises(ValueError, match="Invalid block_align"):
        block_pad_left(4, 2, "diagonal")
    with pytest.raises(ValueError, match="Invalid block_valign"):
        block_pad_top(4, 2, "middle-ish")


def test_grid_block_padding_normalizes_ragged_grid_and_infers_missing_column_width():
    grid, cell_cache, heights, widths, pad_left, pad_top = grid_block_padding(
        [
            [None, [[1, 2], [3, 4]]],
            [[[5], [6]], [[7]]],
        ],
        block_align="right",
        block_valign="bottom",
    )

    assert grid == [[None, [[1, 2], [3, 4]]], [[[5], [6]], [[7]]]]
    assert cell_cache[0][0] == ([], 0, 0)
    assert heights == [2, 2]
    assert widths == [1, 2]
    assert pad_left == [[0, 0], [0, 1]]
    assert pad_top == [[0, 0], [0, 1]]


def test_grid_block_padding_rejects_empty_grid():
    with pytest.raises(ValueError, match="non-empty"):
        grid_block_padding([])


def test_matrix_body_tex_and_pnicearray_tex():
    assert matrix_body_tex([[1, 2], [3, 4]], formatter=str) == "1 & 2 \\\\\n3 & 4 \\\\"
    assert pnicearray_tex(None, formatter=str) == r"\NotEmpty"

    tex = pnicearray_tex([[1, 2, 3]], n_rhs=1, formatter=str, align="c")
    assert r"\begin{pNiceArray}{cc|c}%" in tex
    assert "1 & 2 & 3" in tex
    assert r"\end{pNiceArray}" in tex
