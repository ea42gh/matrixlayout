"""Low-level grid and matrix formatting helpers for GE layouts."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence, Tuple


LatexFormatter = Callable[[Any], str]


def as_2d_list(matrix: Any) -> Tuple[List[List[Any]], int, int]:
    """Return ``(rows, nrows, ncols)`` from common matrix-like inputs."""
    if matrix is None:
        return [], 0, 0

    if hasattr(matrix, "tolist"):
        rows = matrix.tolist()
    elif isinstance(matrix, (list, tuple)):
        rows = list(matrix)
    else:
        try:
            rows = list(matrix)
        except Exception as exc:
            raise TypeError(f"Unsupported matrix-like object: {type(matrix)!r}") from exc

    rows2: List[List[Any]] = []
    for row in rows:
        if isinstance(row, (list, tuple)):
            rows2.append(list(row))
        else:
            rows2.append([row])

    nrows = len(rows2)
    ncols = max((len(row) for row in rows2), default=0)

    for row in rows2:
        if len(row) < ncols:
            row.extend([""] * (ncols - len(row)))

    return rows2, nrows, ncols


def normalize_grid_input(matrices: Any) -> List[List[Any]]:
    """Coerce common inputs into a grid-of-matrices list."""
    if matrices is None:
        return []
    if not isinstance(matrices, (list, tuple)):
        return [[matrices]]
    if not matrices:
        return []
    if not isinstance(matrices[0], (list, tuple)):
        return [list(matrices)]

    def _is_scalar_like(value: Any) -> bool:
        if isinstance(value, (list, tuple)):
            return False
        return not hasattr(value, "shape") and not hasattr(value, "tolist")

    def _is_matrix_like_list(value: Any) -> bool:
        if not isinstance(value, (list, tuple)) or not value:
            return False
        if not all(isinstance(row, (list, tuple)) for row in value):
            return False
        return all(all(_is_scalar_like(cell) for cell in row) for row in value)

    if len(matrices) == 1 and _is_matrix_like_list(matrices[0]):
        return [[matrices[0]]]

    if all(isinstance(row, (list, tuple)) for row in matrices):
        if all(all(_is_scalar_like(cell) for cell in row) for row in matrices):
            return [[matrices]]
    return [list(row) for row in matrices]


def block_pad_left(width: int, actual: int, block_align: Optional[str]) -> int:
    if actual <= 0 or width <= actual:
        return 0
    mode = (block_align or "auto").strip().lower()
    if mode in ("left", "l", "none"):
        return 0
    if mode in ("center", "centre", "c"):
        return (width - actual) // 2
    if mode in ("right", "r", "auto"):
        return width - actual
    raise ValueError(f"Invalid block_align: {block_align!r} (expected left/right/center/auto)")


def block_pad_top(height: int, actual: int, block_valign: Optional[str]) -> int:
    if actual <= 0 or height <= actual:
        return 0
    mode = (block_valign or "bottom").strip().lower()
    if mode in ("top", "t", "none"):
        return 0
    if mode in ("center", "centre", "c"):
        return (height - actual) // 2
    if mode in ("bottom", "b", "auto"):
        return height - actual
    raise ValueError(f"Invalid block_valign: {block_valign!r} (expected top/bottom/center/auto)")


def grid_block_padding(
    matrices: Sequence[Sequence[Any]],
    *,
    block_align: Optional[str] = None,
    block_valign: Optional[str] = None,
) -> Tuple[List[List[Any]], List[List[Tuple[List[List[Any]], int, int]]], List[int], List[int], List[List[int]], List[List[int]]]:
    grid: List[List[Any]] = normalize_grid_input(matrices)
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(row) for row in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    for row in range(n_block_rows):
        if len(grid[row]) < n_block_cols:
            grid[row].extend([None] * (n_block_cols - len(grid[row])))

    block_heights: List[int] = [0] * n_block_rows
    block_widths: List[int] = [0] * n_block_cols
    cell_cache: List[List[Tuple[List[List[Any]], int, int]]] = [
        [([], 0, 0) for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]

    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows, height, width = as_2d_list(grid[br][bc])
            cell_cache[br][bc] = (rows, height, width)
            block_heights[br] = max(block_heights[br], height)
            block_widths[bc] = max(block_widths[bc], width)

    max_height = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_height > 0:
            block_widths[bc] = max_height

    if any(width <= 0 for width in block_widths) or any(height <= 0 for height in block_heights):
        raise ValueError("Could not infer matrix block sizes from `matrices`.")

    pad_left: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    pad_top: List[List[int]] = [[0 for _ in range(n_block_cols)] for _ in range(n_block_rows)]
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, height, width = cell_cache[br][bc]
            if height == 0 or width == 0:
                continue
            pad_left[br][bc] = block_pad_left(block_widths[bc], width, block_align)
            pad_top[br][bc] = block_pad_top(block_heights[br], height, block_valign)

    return grid, cell_cache, block_heights, block_widths, pad_left, pad_top


def matrix_body_tex(matrix: Any, *, formatter: LatexFormatter) -> str:
    """Format a matrix-like object into a TeX body: ``a & b \\ c & d``."""
    rows, nrows, ncols = as_2d_list(matrix)
    if nrows == 0 or ncols == 0:
        return ""

    body_rows: List[str] = []
    for row in rows:
        cells = [formatter(value) for value in row]
        body_rows.append(" & ".join(cells) + r" \\")
    return "\n".join(body_rows)


def pnicearray_tex(
    matrix: Any,
    *,
    n_rhs: int = 0,
    formatter: LatexFormatter,
    align: str = "r",
) -> str:
    """Wrap a matrix body into a ``pNiceArray`` environment."""
    _rows, nrows, ncols = as_2d_list(matrix)
    if nrows == 0 or ncols == 0:
        return r"\NotEmpty"

    if n_rhs and 0 < n_rhs < ncols:
        left = ncols - n_rhs
        fmt = (align * left) + "|" + (align * n_rhs)
    else:
        fmt = align * ncols

    body = matrix_body_tex(matrix, formatter=formatter)
    return f"\\begin{{pNiceArray}}{{{fmt}}}%\n{body}\n\\end{{pNiceArray}}"
