# Getting Started

Minimal examples for common layouts and rendering. Each function accepts
Python lists or `sympy.Matrix` values.

Prerequisite: install `matrixlayout` (and `la_figures` for eigen/SVD specs).

## GE grid

```python
import sympy as sym
from matrixlayout.ge import render_ge_svg

matrices = [[None, sym.Matrix([[1, 2], [3, 4]])]]
svg = render_ge_svg(matrices=matrices)
```

You can also pass a single matrix directly (it is wrapped as `[[A]]`):

```python
svg = render_ge_svg(matrices=sym.Matrix([[1, 2], [3, 4]]))
```

To inspect the TeX instead of rendering SVG:

```python
from matrixlayout.ge import render_ge_tex

tex = render_ge_tex(matrices=matrices)
```

Quick decorations (one-line specs):

```python
decorations = [
    {"grid": (0, 1), "entries": [(0, 0)], "box": True},
    {"grid": (0, 1), "hlines": 1},
    {"grid": (0, 1), "label": r"\\mathbf{A}", "side": "right", "angle": -35, "length": 8},
]
svg = render_ge_svg(matrices=matrices, decorations=decorations, create_medium_nodes=True)
```

Labels and callouts (annotations):

```python
annotations = [
    {"grid": (0, 1), "side": "above", "labels": ["x_1", "x_2"]},
    {"grid": (0, 1), "side": "right", "label": r"\\mathbf{A}", "angle": -35, "length_mm": 8},
]
svg = render_ge_svg(matrices=matrices, annotations=annotations)
```

Notes:
- If both `spec`/`annotations` and explicit kwargs are provided, explicit kwargs win.
- Labels are attached to a block and placed into empty adjacent blocks when possible.
- `specs` is still accepted as a compatibility alias for `annotations`.

## QR grid

```python
import sympy as sym
from matrixlayout.qr import render_qr_svg

matrices = [[None, None, sym.Matrix([[1, 2], [3, 4]]), sym.eye(2)]]
svg = render_qr_svg(matrices=matrices)

You can also pass `annotations` to attach labels/callouts without manual label rows/cols.
```

QR labels with annotations:

```python
annotations = [{"grid": (0, 2), "side": "above", "labels": ["x_1", "x_2"]}]
svg = render_qr_svg(matrices=matrices, annotations=annotations)
```

## Eigen/SVD tables

```python
import sympy as sym
from la_figures import eig_tbl_spec
from matrixlayout import render_eig_svg

spec = eig_tbl_spec(sym.Matrix([[2, 0], [0, 3]]))
svg = render_eig_svg(spec, case="S")
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
For repeated workflows, prefer `render_ge_tex` and render explicitly.

## Output inspection

Use `output_dir` and `output_stem` when calling `*_svg` to retain TeX and SVG
files for inspection.

Debug workflow:

```python
from matrixlayout.ge import render_ge_tex, render_ge_svg

tex = render_ge_tex(matrices=matrices, annotations=annotations)
svg = render_ge_svg(matrices=matrices, annotations=annotations, output_dir="./_out", output_stem="debug")
```

### Smoke render helper

If you need a quick toolchain sanity check, run:

```
python render_smoke.py
```

Set `MATRIXLAYOUT_SMOKE_OUT` to control the output directory.

## Troubleshooting (minimal)

- If SVG rendering fails, switch to `*_tex` to inspect the emitted LaTeX.
- Try an alternate `toolchain_name` if a toolchain is unavailable.
- If labels are misplaced, verify `annotations` are attached to the correct grid cell.
