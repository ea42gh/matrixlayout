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
