"""Decorator-grid resolution helpers for GE rendering."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .formatting import expand_entry_selectors
from .ge_render_grid import DecoratorMap


GridResolver = Callable[[str, Sequence[Sequence[Any]], bool], Optional[Tuple[int, int]]]


def resolve_ge_decorator_grid(
    spec_item: Dict[str, Any],
    *,
    matrices: Sequence[Sequence[Any]],
    n_block_cols: int,
    legacy_submatrix_names: bool,
    resolve_grid_name: GridResolver,
) -> Optional[Tuple[int, int]]:
    """Resolve a decorator spec's grid target."""

    grid_pos = spec_item.get("grid")
    if isinstance(grid_pos, (list, tuple)) and len(grid_pos) == 2:
        return (int(grid_pos[0]), int(grid_pos[1]))

    name = spec_item.get("matrix_name") or spec_item.get("name") or spec_item.get("matrix")
    if isinstance(name, (list, tuple)) and len(name) == 3:
        return (int(name[1]), int(name[2]))

    if isinstance(name, str):
        resolved = resolve_grid_name(name, matrices, legacy_submatrix_names)
        if resolved is not None:
            return resolved
        match = re.match(r"([A-Za-z]+)(\d+)x(\d+)$", name)
        if match:
            return (int(match.group(2)), int(match.group(3)))
        match = re.match(r"([A-Za-z]+)(\d+)$", name)
        if match and n_block_cols == 2 and match.group(1) in ("E", "A"):
            block_col = 0 if match.group(1) == "E" else 1
            return (int(match.group(2)), block_col)

    return None


def build_ge_decorator_map(
    *,
    decorators: Optional[Sequence[Any]],
    matrices: Sequence[Sequence[Any]],
    cell_cache: Sequence[Sequence[Tuple[List[List[Any]], int, int]]],
    n_block_rows: int,
    n_block_cols: int,
    formatter: Callable[[Any], str],
    strict: bool,
    legacy_submatrix_names: bool,
    resolve_grid_name: GridResolver,
) -> DecoratorMap:
    """Build the flattened decorator map consumed by GE render assembly."""

    decorator_map: DecoratorMap = {}
    if not decorators:
        return decorator_map

    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")

        grid_pos = resolve_ge_decorator_grid(
            spec_item,
            matrices=matrices,
            n_block_cols=n_block_cols,
            legacy_submatrix_names=legacy_submatrix_names,
            resolve_grid_name=resolve_grid_name,
        )
        if grid_pos is None:
            if strict:
                raise ValueError("decorator grid must be a (row,col) pair or resolvable name")
            continue

        block_row, block_col = grid_pos
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
