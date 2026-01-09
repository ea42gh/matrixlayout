# API

This is a lightweight index of primary entry points. All functions accept
spec dictionaries and return TeX or SVG strings.

See module docstrings for argument details and defaults.

## GE

- `matrixlayout.ge.ge_grid_tex`: emit TeX for a GE grid.
- `matrixlayout.ge.ge_grid_svg`: render a GE grid to SVG.
- `matrixlayout.ge.ge_grid_bundle`: return TeX plus submatrix span metadata.

## QR

- `matrixlayout.qr.qr_grid_tex`: emit TeX for a QR grid.
- `matrixlayout.qr.qr_grid_svg`: render a QR grid to SVG.
- `matrixlayout.qr.qr_grid_bundle`: return TeX plus submatrix span metadata.

## Eigen/SVD

- `matrixlayout.eigproblem.eigproblem_tex`: emit TeX for eigen/SVD tables.
- `matrixlayout.eigproblem.eigproblem_svg`: render eigen/SVD tables to SVG.
