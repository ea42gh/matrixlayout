# matrixlayout

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ea42gh/matrixlayout/HEAD?labpath=matrixlayout_demo.ipynb)

`matrixlayout` is a small, composable Python library for **matrix-based layout and presentation**. It builds **LaTeX/TikZ** that describes matrix and grid visuals (blocks, partitions, spacing, braces, arrows, highlights) and renders them to **SVG** via a single backend boundary.

This project is **layout-only** by design: it does not implement linear algebra algorithms or symbolic manipulation; packages such as `la_figures` compute linear algebra examples and pass layout descriptions to `matrixlayout`.

## Scope

### What `matrixlayout` *does*
- Construct matrix/grid layouts (rows, columns, blocks, partitions, spacing)
- Construct tables for eigenproblems and SVD
- Place annotations (arrows, braces, highlights, labels)
- Convert symbolic objects to LaTeX strings for display (e.g. `sympy.latex`)
- Generate LaTeX/TikZ that describes the layout
- Render to SVG by delegating to `jupyter_tikz`

### What `matrixlayout` *does not* do
- Compute matrix factorizations or decompositions (QR/LU/SVD/eigen, etc.)
- Perform Gaussian elimination / RREF / back-substitution or any solver logic
- Modify or simplify symbolic expressions
- Install or manage rendering toolchains
- Implement rendering backends itself

Algorithmic work lives in a separate package (`la_figures`) that produces **layout descriptions** consumed by `matrixlayout`.

## Decorators & selectors

Decorator specs let you style specific entries after formatting. Helpers in
`matrixlayout.formatting` make selectors concise:

```python
from matrixlayout.formatting import decorator_box, sel_entry

decorators = [
    {"grid": (0, 1), "entries": [sel_entry(0, 0)], "decorator": decorator_box()},
]
```

For eigenproblem vector rows, selectors use `(group, vector, entry)` tuples.

## Rendering boundary

`matrixlayout` delegates SVG rendering to `jupyter_tikz`:

```python
from matrixlayout.ge import render_ge_svg
```

Use `pip install "matrixlayout[render]"` for rendering. The render extra pins
the patched `ea42gh/jupyter-tikz` renderer because the PyPI `jupyter-tikz`
package does not provide the `render_svg_with_artifacts` API that matrixlayout
requires.

## Documentation

MkDocs configuration lives in `mkdocs.yml` with content under `docs/`.

Build the docs:

```bash
cd matrixlayout
mkdocs build
```
