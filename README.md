# matrixlayout

`matrixlayout` is a small, composable Python library for **matrix-based layout and presentation**. It builds **LaTeX/TikZ** that describes matrix and grid visuals (blocks, partitions, spacing, braces, arrows, highlights) and renders them to **SVG** via a single backend boundary.

This project is **layout-only** by design: it does not implement linear algebra algorithms or symbolic manipulation.

## Scope

### What `matrixlayout` *does*
- Construct matrix/grid layouts (rows, columns, blocks, partitions, spacing)
- Construct tables for eigenproblems and SVD
- Place annotations (arrows, braces, highlights, labels)
- Convert symbolic objects to LaTeX strings for display (e.g. `sympy.latex`)
- Generate LaTeX/TikZ that describes the layout
- Render to SVG by calling `jupyter_tikz.render_svg(tex: str) -> str`

### What `matrixlayout` *does not* do
- Compute matrix factorizations or decompositions (QR/LU/SVD/eigen, etc.)
- Perform Gaussian elimination / RREF / back-substitution or any solver logic
- Modify or simplify symbolic expressions
- Manage rendering toolchains, subprocesses, cropping, or SVG normalization
- Choose between rendering backends

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

`matrixlayout` depends on `jupyter_tikz` and **always** renders through:

```python
from jupyter_tikz import render_svg
```

## Documentation

MkDocs configuration lives in `matrixlayout/mkdocs.yml` with content under
`matrixlayout/docs/`.

Build the docs:

```bash
cd matrixlayout
mkdocs build
```
