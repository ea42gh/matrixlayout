# API

This is a lightweight index of primary entry points. All functions accept
spec dictionaries and return TeX or SVG strings.

See module docstrings for argument details and defaults.

## GE

- `matrixlayout.ge.grid_tex(matrices, **opts)`: emit TeX for a GE grid (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.grid_svg(matrices, **opts)`: render a GE grid to SVG (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.grid_bundle(matrices, **opts)`: return TeX plus submatrix span metadata.
- `matrixlayout.ge.grid_line_specs(**opts)`: build `submatrix_locs` entries for hlines/vlines.
- `matrixlayout.ge.grid_highlight_specs(**opts)`: build `codebefore` entries for block highlights.

Common options: `specs` (labels/callouts), `decorations` (hlines/vlines/boxes),
`output_dir`/`output_stem` (persist TeX/SVG). Label rows/cols are inserted only
when needed; existing blank rows/cols are reused.

Specs vs decorations:
use `specs` for labels/callouts and `decorations` for entry styling/lines.

## QR

- `matrixlayout.qr.qr_grid_tex(matrices, **opts)`: emit TeX for a QR grid (accepts `specs`).
- `matrixlayout.qr.qr_grid_svg(matrices, **opts)`: render a QR grid to SVG (accepts `specs`).
- `matrixlayout.qr.qr_grid_bundle(matrices, **opts)`: return TeX plus submatrix span metadata.

Common options: `specs` (labels/callouts), `output_dir`/`output_stem` (persist TeX/SVG).

## Eigen/SVD

- `matrixlayout.eigproblem.eigproblem_tex`: emit TeX for eigen/SVD tables.
- `matrixlayout.eigproblem.eigproblem_svg`: render eigen/SVD tables to SVG.

## Backsubstitution

- `matrixlayout.backsubst.backsubst_tex(**opts)`: emit TeX for system/cascade/solution blocks.
- `matrixlayout.backsubst.backsubst_svg(**opts)`: render the back-substitution document to SVG.
