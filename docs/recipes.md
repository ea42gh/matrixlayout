# Spec Recipes

Compact examples for common layouts.

## GE with callouts and pivots

```python
from matrixlayout.ge import render_ge_svg

spec = {
    "matrices": [[None, [[1, 2], [3, 4]]]],
    "pivot_locs": ["(1-1)(1-1)", "(2-2)(2-2)"],
    "callouts": [
        {"name": "A0", "label": r"$A$", "anchor": "right", "angle_deg": -35, "length_mm": 8},
    ],
}
svg = render_ge_svg(**spec)
```

## GE with explicit labels overriding specs

```python
specs = [{"grid": (0, 1), "side": "above", "labels": ["spec"]}]
svg = render_ge_svg(
    matrices=[[None, [[1, 2], [3, 4]]]],
    specs=specs,
    label_rows=[{"grid": (0, 1), "side": "above", "rows": [["explicit"]]}],
)
```

## QR with array names

```python
from matrixlayout.qr import render_qr_svg

spec = {
    "matrices": [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]]],
    "array_names": True,
}
svg = render_qr_svg(**spec)

# Optional: pass label/callout specs via `specs`.
```

## Eigen/SVD with decorators

```python
from matrixlayout import render_eig_svg
from matrixlayout.formatting import decorator_color, sel_vec

spec = {
    "lambda": [2, 3],
    "ma": [1, 1],
    "evecs": [[[1, 0]], [[0, 1]]],
    "decorators": [
        {"block": "evecs", "entries": [sel_vec(0, 0, 0)], "decorator": decorator_color("red")},
    ],
}
svg = render_eig_svg(spec, case="S")
```
