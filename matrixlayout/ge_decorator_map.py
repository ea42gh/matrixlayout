"""Decorator-grid resolution helpers for GE rendering."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence, Tuple

from .formatting import expand_entry_selectors
from .ge_render_grid import DecoratorMap


def build_ge_decorator_map(
    *,
    decorators: Optional[Sequence[Any]],
    cell_cache: Sequence[Sequence[Tuple[List[List[Any]], int, int]]],
    n_block_rows: int,
    n_block_cols: int,
    formatter: Callable[[Any], str],
    strict: bool,
) -> DecoratorMap:
    """Build the flattened decorator map consumed by GE render assembly."""

    decorator_map: DecoratorMap = {}
    if not decorators:
        return decorator_map

    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")

        grid = spec_item.get("grid")
        if isinstance(grid, (list, tuple)) and len(grid) == 2:
            grid_key = (int(grid[0]), int(grid[1]))
        else:
            grid_key = None
        if grid_key is None:
            if strict:
                raise ValueError("decorator grid must be a (row,col) pair")
            continue

        block_row, block_col = grid_key
        decorator = spec_item.get("decorator")
        if not callable(decorator):
            raise ValueError("decorator must be callable")

        entry_formatter = spec_item.get("formatter", formatter)
        entries = spec_item.get("entries")
        if block_row < 0 or block_col < 0 or block_row >= n_block_rows or block_col >= n_block_cols:
            raise ValueError("decorator grid position out of range")

        _rows, nrows, ncols = cell_cache[block_row][block_col]
        selected = expand_entry_selectors(entries, nrows, ncols, filter_bounds=True)
        if strict and not selected:
            raise ValueError("decorator selector did not match any entries")

        decorator_map.setdefault((block_row, block_col), []).append((decorator, selected, entry_formatter))

    return decorator_map
