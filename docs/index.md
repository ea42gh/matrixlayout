# Matrixlayout

Matrixlayout is a layout layer for matrix-based figures. It emits LaTeX/TikZ
for structured grids and tables (GE, QR, eigen/SVD) and delegates rendering to
`jupyter_tikz`. It does not implement linear algebra algorithms; those live in
`la_figures`.

## Design Principle

Layout concerns are separated from algorithmic concerns. Matrixlayout consumes
explicit matrices or layout specs and produces TeX; it does not compute those
matrices.

## Scope

- Constructs grid/table layouts from explicit matrices or specs.
- Formats entries to TeX and applies decorators/selectors.
- Emits TeX for `nicematrix` and auxiliary TikZ nodes.
- Renders SVG via `jupyter_tikz`.

## Reading Guide

- See `overview.md` for the core layout model and specs.
- See `getting-started.md` for minimal runnable examples.
- See `decorators.md` for selector and decorator usage.
- See `rendering.md` for toolchains, crop, and padding.
- See `notebooks/` for runnable JupyterLab examples:
  - `notebooks/01_ge_grids.ipynb`
  - `notebooks/02_qr_grids.ipynb`
  - `notebooks/03_eig_svd_tables.ipynb`
  - `notebooks/04_backsubstitution.ipynb`
  - `notebooks/05_formatting_selectors.ipynb`
  - `notebooks/06_rendering_templates.ipynb`
- See `glossary.md` for terminology.
