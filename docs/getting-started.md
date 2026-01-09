# Getting Started

Minimal examples for common layouts and rendering. Each function accepts
Python lists or `sympy.Matrix` values.

Prerequisite: install `matrixlayout` (and `la_figures` for eigen/SVD specs).

## GE grid

```python
import sympy as sym
from matrixlayout.ge import ge_grid_svg

matrices = [[None, sym.Matrix([[1, 2], [3, 4]])]]
svg = ge_grid_svg(matrices=matrices)
```

To inspect the TeX instead of rendering SVG:

```python
from matrixlayout.ge import ge_grid_tex

tex = ge_grid_tex(matrices=matrices)
```

## QR grid

```python
import sympy as sym
from matrixlayout.qr import qr_grid_svg

matrices = [[None, None, sym.Matrix([[1, 2], [3, 4]]), sym.eye(2)]]
svg = qr_grid_svg(matrices=matrices)
```

## Eigen/SVD tables

```python
import sympy as sym
from la_figures import eig_tbl_spec
from matrixlayout import eigproblem_svg

spec = eig_tbl_spec(sym.Matrix([[2, 0], [0, 3]]))
svg = eigproblem_svg(spec, case="S")
```

The rendering backend is `jupyter_tikz`; toolchain configuration lives there.
For repeated workflows, prefer `ge_grid_tex` and render explicitly.

## Output inspection

Use `output_dir` and `output_stem` when calling `*_svg` to retain TeX and SVG
files for inspection.

## Troubleshooting (minimal)

- If SVG rendering fails, switch to `*_tex` to inspect the emitted LaTeX.
- Try an alternate `toolchain_name` if a toolchain is unavailable.
