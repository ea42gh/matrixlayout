# Getting Started

Minimal examples for common layouts and rendering. Each function accepts
Python lists or `sympy.Matrix` values.

Prerequisite: install `matrixlayout` (and `la_figures` for eigen/SVD specs).

## GE grid

```python
import sympy as sym
from matrixlayout.ge import grid_svg

matrices = [[None, sym.Matrix([[1, 2], [3, 4]])]]
svg = grid_svg(matrices=matrices)
```

You can also pass a single matrix directly (it is wrapped as `[[A]]`):

```python
svg = grid_svg(matrices=sym.Matrix([[1, 2], [3, 4]]))
```

To inspect the TeX instead of rendering SVG:

```python
from matrixlayout.ge import grid_tex

tex = grid_tex(matrices=matrices)
```

Quick decorations (one-line specs):

```python
decorations = [
    {"grid": (0, 1), "entries": [(0, 0)], "box": True},
    {"grid": (0, 1), "hlines": 1},
    {"grid": (0, 1), "label": r"\\mathbf{A}", "side": "right", "angle": -35, "length": 8},
]
svg = grid_svg(matrices=matrices, decorations=decorations, create_medium_nodes=True)
```

Labels and callouts (specs):

```python
specs = [
    {"grid": (0, 1), "side": "above", "labels": ["x_1", "x_2"]},
    {"grid": (0, 1), "side": "right", "label": r"\\mathbf{A}", "angle": -35, "length_mm": 8},
]
svg = grid_svg(matrices=matrices, specs=specs)
```

## QR grid

```python
import sympy as sym
from matrixlayout.qr import qr_grid_svg

matrices = [[None, None, sym.Matrix([[1, 2], [3, 4]]), sym.eye(2)]]
svg = qr_grid_svg(matrices=matrices)

You can also pass `specs` to attach labels/callouts without manual label rows/cols.
```

QR labels with specs:

```python
specs = [{"grid": (0, 2), "side": "above", "labels": ["x_1", "x_2"]}]
svg = qr_grid_svg(matrices=matrices, specs=specs)
```

## Eigen/SVD tables

```python
import sympy as sym
from la_figures import eig_tbl_spec
from matrixlayout import eigproblem_svg

spec = eig_tbl_spec(sym.Matrix([[2, 0], [0, 3]]))
svg = eigproblem_svg(spec, case="S")
```

## Backsubstitution

```python
import sympy as sym
from la_figures import linear_system_tex, backsubstitution_tex, standard_solution_tex
from matrixlayout.backsubst import backsubst_svg

A = sym.Matrix([[1, 0, sym.pi], [0, 1, 1]])
b = sym.Matrix([1, 2])

svg = backsubst_svg(
    system_txt=linear_system_tex(A, b),
    cascade_txt=backsubstitution_tex(A, b),
    solution_txt=standard_solution_tex(A, b),
)
```

The rendering backend is `jupyter_tikz`; toolchain configuration lives there.
For repeated workflows, prefer `grid_tex` and render explicitly.

## Output inspection

Use `output_dir` and `output_stem` when calling `*_svg` to retain TeX and SVG
files for inspection.

Debug workflow:

```python
from matrixlayout.ge import grid_tex, grid_svg

tex = grid_tex(matrices=matrices, specs=specs)
svg = grid_svg(matrices=matrices, specs=specs, output_dir="./_out", output_stem="debug")
```

## Troubleshooting (minimal)

- If SVG rendering fails, switch to `*_tex` to inspect the emitted LaTeX.
- Try an alternate `toolchain_name` if a toolchain is unavailable.
- If labels are misplaced, verify `specs` are attached to the correct grid cell.
