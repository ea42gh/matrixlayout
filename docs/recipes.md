# Spec Recipes

Compact examples for common layouts.

## GE with callouts and pivots

```python
from matrixlayout.ge import grid_svg

spec = {
    "matrices": [[None, [[1, 2], [3, 4]]]],
    "pivot_locs": ["(1-1)(1-1)", "(2-2)(2-2)"],
    "callouts": [
        {"name": "A0", "label": r"$A$", "anchor": "right", "angle_deg": -35, "length_mm": 8},
    ],
}
svg = grid_svg(**spec)
```

## QR with array names

```python
from matrixlayout.qr import qr_grid_svg

spec = {
    "matrices": [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]]],
    "array_names": True,
}
svg = qr_grid_svg(**spec)

# Optional: pass label/callout specs via `specs`.
```

## Eigen/SVD with decorators

```python
from matrixlayout import eigproblem_svg
from matrixlayout.formatting import decorator_color, sel_vec

spec = {
    "lambda": [2, 3],
    "ma": [1, 1],
    "evecs": [[[1, 0]], [[0, 1]]],
    "decorators": [
        {"block": "evecs", "entries": [sel_vec(0, 0, 0)], "decorator": decorator_color("red")},
    ],
}
svg = eigproblem_svg(spec, case="S")
```
