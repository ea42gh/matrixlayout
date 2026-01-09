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

Use `decorations` for one-line specs. Each dict must include `grid=(row,col)`.

### Selector keys (shared)

| Key | Meaning | Forms |
| --- | --- | --- |
| `entries` | explicit entries | `[(r,c), ...]` |
| `rows` | row selection | `(r0,r1)`, `"r0:r1"`, `slice(r0,r1+1)`, `[r...]`, `None` |
| `cols` | col selection | same as `rows` |
| `submatrix` | rows+cols | `((rows),(cols))` |

`entries` overrides `rows`/`cols`/`submatrix`. The same selectors work for
entry styles and backgrounds.

### Action keys (choose one)

| Action | Key(s) | Notes |
| --- | --- | --- |
| Background | `background` | Uses selectors; emits `codebefore`. |
| Lines | `hlines`, `vlines` | Integer/list; `True`/`"submatrix"` uses selection end; `"bounds"` uses start+end; `"all"` uses every interior line. |
| Entry style | `box`, `color`, `bold` | Uses selectors; `box=True` or color string. |
| Callout | `label` | Optional `side`, `angle`, `length`, `anchor`. |

Selection keys apply to `background`, `box`, `color`, and `bold`. Line and label
specs ignore `rows`/`cols`/`submatrix`.

### One-liners

```python
{"grid": (1, 0), "submatrix": ("0:1", "2:3"), "background": "yellow!25"}
{"grid": (0, 1), "hlines": 2}
{"grid": (0, 1), "vlines": [1, 3]}
{"grid": (0, 1), "submatrix": ("0:0", None), "hlines": "submatrix"}
{"grid": (0, 1), "submatrix": (None, "0:2"), "vlines": True}
{"grid": (0, 1), "submatrix": ("0:2", None), "hlines": "bounds"}
{"grid": (0, 1), "submatrix": (None, "0:1"), "vlines": "bounds"}
{"grid": (0, 1), "submatrix": ("0:2", None), "hlines": "all"}
{"grid": (0, 1), "submatrix": (None, "0:2"), "vlines": "all"}
{"grid": (2, 1), "entries": [(0, 0)], "box": True}
{"grid": (2, 1), "rows": "0:1", "cols": "1:1", "color": "red"}
{"grid": (2, 1), "entries": [(0, 0)], "color": "red", "bold": True}
{"grid": (1, 0), "label": r"\\mathbf{B}", "side": "left", "angle": -35, "length": 8}
```

### Minimal list

```python
decorations = [
    {"grid": (0, 1), "submatrix": (None, "2:3"), "background": "yellow!25"},
    {"grid": (1, 0), "hlines": 2},
    {"grid": (0, 1), "vlines": 2},
    {"grid": (2, 1), "entries": [(0, 0)], "box": True},
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
