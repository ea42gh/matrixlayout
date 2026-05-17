import pytest

from matrixlayout.ge_decorator_map import build_ge_decorator_map
from matrixlayout.ge_grid import grid_block_padding


def _grid_parts(matrices):
    grid, cell_cache, block_heights, block_widths, _pad_left, _pad_top = grid_block_padding(matrices)
    return grid, cell_cache, len(block_heights), len(block_widths)


def test_build_ge_decorator_map_expands_selectors_and_uses_formatter():
    grid, cell_cache, n_block_rows, n_block_cols = _grid_parts([[None, [[1, 2], [3, 4]]]])

    def dec(value):
        return value

    formatter = lambda value: f"v{value}"
    result = build_ge_decorator_map(
        decorators=[{"grid": (0, 1), "entries": [(0, 1)], "decorator": dec, "formatter": formatter}],
        cell_cache=cell_cache,
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        formatter=str,
        strict=True,
    )

    assert set(result) == {(0, 1)}
    decorator, selected, entry_formatter = result[(0, 1)][0]
    assert decorator is dec
    assert selected == {(0, 1)}
    assert entry_formatter(2) == "v2"


def test_build_ge_decorator_map_ignores_unresolved_when_not_strict():
    grid, cell_cache, n_block_rows, n_block_cols = _grid_parts([[[1]]])
    assert (
        build_ge_decorator_map(
            decorators=[{"matrix": "missing", "decorator": lambda value: value}],
            cell_cache=cell_cache,
            n_block_rows=n_block_rows,
            n_block_cols=n_block_cols,
            formatter=str,
            strict=False,
        )
        == {}
    )


def test_build_ge_decorator_map_strict_and_validation_errors():
    grid, cell_cache, n_block_rows, n_block_cols = _grid_parts([[[1]]])

    common = {
        "cell_cache": cell_cache,
        "n_block_rows": n_block_rows,
        "n_block_cols": n_block_cols,
        "formatter": str,
    }

    with pytest.raises(ValueError, match="dict specs"):
        build_ge_decorator_map(decorators=["bad"], strict=True, **common)
    with pytest.raises(ValueError, match="row,col"):
        build_ge_decorator_map(decorators=[{"matrix": "missing", "decorator": lambda value: value}], strict=True, **common)
    with pytest.raises(ValueError, match="callable"):
        build_ge_decorator_map(decorators=[{"grid": (0, 0), "decorator": "not callable"}], strict=True, **common)
    with pytest.raises(ValueError, match="out of range"):
        build_ge_decorator_map(decorators=[{"grid": (9, 9), "decorator": lambda value: value}], strict=True, **common)
    with pytest.raises(ValueError, match="selector did not match"):
        build_ge_decorator_map(decorators=[{"grid": (0, 0), "entries": [(9, 9)], "decorator": lambda value: value}], strict=True, **common)
