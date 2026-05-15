import pytest

from matrixlayout.ge_decorator_map import build_ge_decorator_map, resolve_ge_decorator_grid
from matrixlayout.ge_grid import grid_block_padding


def _resolver(name, matrices, legacy):
    del matrices, legacy
    return {"A0": (0, 1), "A0x1": (0, 1), "A0x0": (0, 0)}.get(name)


def _grid_parts(matrices):
    grid, cell_cache, block_heights, block_widths, _pad_left, _pad_top = grid_block_padding(matrices)
    return grid, cell_cache, len(block_heights), len(block_widths)


def test_resolve_ge_decorator_grid_accepts_grid_and_name_aliases():
    matrices = [[None, [[1, 2], [3, 4]]]]

    assert resolve_ge_decorator_grid(
        {"grid": ["0", "1"]},
        matrices=matrices,
        n_block_cols=2,
        legacy_submatrix_names=False,
        resolve_grid_name=_resolver,
    ) == (0, 1)
    assert resolve_ge_decorator_grid(
        {"matrix_name": "A0"},
        matrices=matrices,
        n_block_cols=2,
        legacy_submatrix_names=False,
        resolve_grid_name=_resolver,
    ) == (0, 1)
    assert resolve_ge_decorator_grid(
        {"name": ["M", 2, 3]},
        matrices=matrices,
        n_block_cols=2,
        legacy_submatrix_names=False,
        resolve_grid_name=_resolver,
    ) == (2, 3)
    assert resolve_ge_decorator_grid(
        {"matrix": "E4"},
        matrices=matrices,
        n_block_cols=2,
        legacy_submatrix_names=False,
        resolve_grid_name=lambda *_: None,
    ) == (4, 0)
    assert resolve_ge_decorator_grid(
        {"matrix": "A4"},
        matrices=matrices,
        n_block_cols=2,
        legacy_submatrix_names=False,
        resolve_grid_name=lambda *_: None,
    ) == (4, 1)
    assert resolve_ge_decorator_grid(
        {"matrix": "M7x8"},
        matrices=matrices,
        n_block_cols=3,
        legacy_submatrix_names=False,
        resolve_grid_name=lambda *_: None,
    ) == (7, 8)


def test_resolve_ge_decorator_grid_returns_none_for_unresolved():
    assert resolve_ge_decorator_grid(
        {"matrix": "unknown"},
        matrices=[[[1]]],
        n_block_cols=1,
        legacy_submatrix_names=False,
        resolve_grid_name=lambda *_: None,
    ) is None


def test_build_ge_decorator_map_expands_selectors_and_uses_formatter():
    grid, cell_cache, n_block_rows, n_block_cols = _grid_parts([[None, [[1, 2], [3, 4]]]])

    def dec(value):
        return value

    formatter = lambda value: f"v{value}"
    result = build_ge_decorator_map(
        decorators=[{"matrix_name": "A0", "entries": [(0, 1)], "decorator": dec, "formatter": formatter}],
        matrices=grid,
        cell_cache=cell_cache,
        n_block_rows=n_block_rows,
        n_block_cols=n_block_cols,
        formatter=str,
        strict=True,
        legacy_submatrix_names=False,
        resolve_grid_name=_resolver,
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
            matrices=grid,
            cell_cache=cell_cache,
            n_block_rows=n_block_rows,
            n_block_cols=n_block_cols,
            formatter=str,
            strict=False,
            legacy_submatrix_names=False,
            resolve_grid_name=lambda *_: None,
        )
        == {}
    )


def test_build_ge_decorator_map_strict_and_validation_errors():
    grid, cell_cache, n_block_rows, n_block_cols = _grid_parts([[[1]]])

    common = {
        "matrices": grid,
        "cell_cache": cell_cache,
        "n_block_rows": n_block_rows,
        "n_block_cols": n_block_cols,
        "formatter": str,
        "legacy_submatrix_names": False,
        "resolve_grid_name": lambda *_: None,
    }

    with pytest.raises(ValueError, match="dict specs"):
        build_ge_decorator_map(decorators=["bad"], strict=True, **common)
    with pytest.raises(ValueError, match="resolvable name"):
        build_ge_decorator_map(decorators=[{"matrix": "missing", "decorator": lambda value: value}], strict=True, **common)
    with pytest.raises(ValueError, match="callable"):
        build_ge_decorator_map(decorators=[{"grid": (0, 0), "decorator": "not callable"}], strict=True, **common)
    with pytest.raises(ValueError, match="out of range"):
        build_ge_decorator_map(decorators=[{"grid": (9, 9), "decorator": lambda value: value}], strict=True, **common)
    with pytest.raises(ValueError, match="selector did not match"):
        build_ge_decorator_map(decorators=[{"grid": (0, 0), "entries": [(9, 9)], "decorator": lambda value: value}], strict=True, **common)
