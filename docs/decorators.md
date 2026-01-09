# Decorators

Decorators apply TeX styling to selected entries after formatting. Selection is
index-based; coordinates are 0-based within each matrix block.

TeX node coordinates and submatrix spans are 1-based; selectors remain 0-based.

## Basics

```python
from matrixlayout.formatting import decorator_box, sel_entry

decorators = [
    {"grid": (0, 1), "entries": [sel_entry(0, 0)], "decorator": decorator_box()},
]
```

## Unified decorations (recommended)

For one-line specs without nicematrix details, use `decorations` instead of
`decorators`. Each item is a dict keyed by `grid=(row,col)`.

Row/col selectors accept ranges, lists, slices, or `None`:

- `(0, 2)` inclusive
- `"0:2"` inclusive
- `slice(0, 3)` (stop exclusive)
- `[0, 2]`
- `None` (all)

The same `rows`/`cols`/`submatrix` selectors work for both entry styling
(`box`, `color`, `bold`) and block highlights (`background`). Use `entries`
to override selectors with explicit coordinates.

Background highlight:

```python
{"grid": (1, 0), "submatrix": ("0:1", "2:3"), "background": "yellow!25"}
```

Separator lines:

```python
{"grid": (0, 1), "hlines": 2}
{"grid": (0, 1), "vlines": [1, 3]}
```

Entry emphasis:

```python
{"grid": (2, 1), "entries": [(0, 0)], "box": True}
{"grid": (2, 1), "entries": [(0, 0)], "color": "red"}
{"grid": (2, 1), "entries": [(0, 0)], "bold": True}
```

Callout labels:

```python
{"grid": (1, 0), "label": r"\\mathbf{B}", "side": "left", "angle": -35, "length": 8}
```

All-in-one list:

```python
decorations = [
    {"grid": (0, 1), "submatrix": (None, "2:3"), "background": "yellow!25"},
    {"grid": (2, 1), "entries": [(0, 0)], "box": True},
    {"grid": (1, 0), "hlines": 2},
    {"grid": (0, 1), "vlines": 2},
    {"grid": (0, 1), "label": r"\\mathbf{C}", "side": "right", "angle": -35, "length": 8},
]
svg = ge_grid_svg(matrices=matrices, decorations=decorations, create_medium_nodes=True)
```

## Selectors

- `sel_entry(i, j)`
- `sel_row(i)`, `sel_col(j)`
- `sel_box((i0, j0), (i1, j1))`
- `sel_rows([...])`, `sel_cols([...])`
- `sel_all()`
- `sel_vec(group, vec, entry)`, `sel_vec_range(start, end)`

Example with a row selector:

```python
from matrixlayout.formatting import decorator_bf, sel_row

decorators = [
    {"grid": (0, 1), "entries": [sel_row(0)], "decorator": decorator_bf()},
]
```

Example with a box selector:

```python
from matrixlayout.formatting import decorator_bg, sel_box

decorators = [
    {"grid": (0, 1), "entries": [sel_box((0, 0), (1, 1))], "decorator": decorator_bg("yellow")},
]
```

Eigen/SVD vector selectors:

```python
from matrixlayout.formatting import decorator_color, sel_vec, sel_vec_range

decorators = [
    {"block": "evecs", "entries": [sel_vec(0, 0, 0)], "decorator": decorator_color("red")},
    {"block": "qvecs", "entries": [sel_vec_range((0, 0, 0), (0, 0, 2))], "decorator": decorator_color("blue")},
]
```

When `strict=True` is passed to a renderer, selectors that match no entries
raise a `ValueError`.
