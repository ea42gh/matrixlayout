# Rendering

Rendering uses `jupyter_tikz` under the hood.

## SVG output

```python
from matrixlayout.ge import ge_grid_svg
svg = ge_grid_svg(matrices=[[None, [[1]]]])
```

## Toolchains

Pass `toolchain_name` to select a specific LaTeX toolchain.

## Crop and padding

Use `crop` and `padding` to control bounding box behavior.
