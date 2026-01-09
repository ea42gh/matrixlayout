# Getting Started

This page shows minimal examples for common layouts and rendering.

## GE (Gaussian Elimination) grid

```python
import sympy as sym
from matrixlayout.ge import ge_grid_svg

matrices = [[None, sym.Matrix([[1, 2], [3, 4]])]]
svg = ge_grid_svg(matrices=matrices)
```

## QR grid

```python
import sympy as sym
from matrixlayout.qr import qr_grid_svg

matrices = [[None, None, sym.Matrix([[1, 2], [3, 4]]), sym.eye(2)]]
svg = qr_grid_svg(matrices=matrices)
```

## Eigen/SVD table

```python
import sympy as sym
from matrixlayout import eigproblem_svg
from la_figures import eig_tbl_spec

spec = eig_tbl_spec(sym.Matrix([[2, 0], [0, 3]]))
svg = eigproblem_svg(spec, case="S")
```
