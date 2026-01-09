# End-to-End Example

A compact example that emits TeX, renders SVG, and retains artifacts.

```python
import sympy as sym
from matrixlayout.ge import ge_grid_tex, ge_grid_svg

matrices = [[None, sym.Matrix([[1, 2], [3, 4]])]]
tex = ge_grid_tex(matrices=matrices)

svg = ge_grid_svg(
    matrices=matrices,
    output_dir="./_out",
    output_stem="ge_min",
    crop="tight",
    padding=(2, 2, 2, 2),
)
```

Inspect `./_out/ge_min.tex` and `./_out/ge_min.svg` after rendering.
