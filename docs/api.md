# API

This is a lightweight index of primary entry points. All functions accept
spec dictionaries and return TeX or SVG strings.

See module docstrings for argument details and defaults.

## Public vs internal helpers

Public APIs are stable and documented below. Internal helpers are either
prefixed with `_` or live in modules that are not intended to be called
directly by users. If you need an internal helper, prefer a public wrapper.

Prefer descriptive renderer names such as `render_ge_tex` and `render_ge_svg`
over generic aliases. The package top level intentionally does not export
`tex` or `svg`; use `render_ge_tex`/`render_ge_svg` for supported GE rendering. The private `matrixlayout.ge._tex`/`matrixlayout.ge._svg` helpers are only for
working with the lower-level GE template interface.

## GE

- `matrixlayout.ge.render_ge_tex(matrices, **opts)`: emit TeX for a GE grid (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.render_ge_svg(matrices, **opts)`: render a GE grid to SVG (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.grid_bundle(matrices, **opts)`: return TeX plus submatrix span metadata.
- `matrixlayout.ge.grid_submatrix_spans(matrices, **opts)`: return delimiter spans for a GE grid.
- `matrixlayout.ge.grid_line_specs(**opts)`: compute `submatrix_locs` entries for hlines/vlines.
- `matrixlayout.ge.grid_highlight_specs(**opts)`: compute `codebefore` entries for block highlights.
- `matrixlayout.ge.render_ge_tex_specs(annotations)`: convert row/column label annotations into `label_rows`/`label_cols`.
- `matrixlayout.ge.resolve_ge_grid_name(name, **opts)`: resolve generated delimiter names to grid positions for diagnostics and low-level interop; prefer `grid=(block_row, block_col)` in new specs.
- `matrixlayout.ge.decorations_help()`: return help text for `decorations` spec syntax.

Common options: `annotations` (row/column labels), `callouts` (arrow labels attached
to submatrix delimiters), `decorations` (hlines/vlines/boxes/highlights),
`output_dir`/`output_stem` (persist TeX/SVG). Label rows/cols are inserted only
when needed; existing blank rows/cols are reused. Explicit kwargs override values
provided by a spec.

The package top level also exports `grid_bundle` and `GEGridBundle`, matching
the QR `qr_grid_bundle`/`QRGridBundle` API.

Spec roles:
use `annotations` or explicit `label_rows`/`label_cols` for row and column labels,
`callouts` for arrow labels attached to matrix blocks, `decorations` for high-level
highlights/lines/outline specs, and `decorators` for callable entry formatting.

## QR

- `matrixlayout.qr.render_qr_tex(matrices, **opts)`: emit TeX for a QR grid (accepts `annotations` and `callouts`).
- `matrixlayout.qr.render_qr_svg(matrices, **opts)`: render a QR grid to SVG (accepts `annotations` and `callouts`).
- `matrixlayout.qr.qr_grid_bundle(matrices, **opts)`: return a `QRGridBundle` (TeX plus submatrix span metadata).
- `matrixlayout.qr.resolve_qr_grid_name(name, **opts)`: resolve QR grid matrix names to positions.

Common options: `annotations` (row/column labels), `callouts` (arrow labels),
`output_dir`/`output_stem` (persist TeX/SVG).

## Eigen/SVD

- `matrixlayout.eigproblem.render_eig_tex`: emit TeX for eigen/SVD tables.
- `matrixlayout.eigproblem.render_eig_svg`: render eigen/SVD tables to SVG.

The eigen/SVD template uses `body_preamble` for body-local TeX setup such as
`\NiceMatrixOptions`.
Matrix-block column spacing is controlled with millimeter kwargs:
`mmLambda` for `\Lambda`, `mmSigma` for `\Sigma`, `mmS` for ordinary eigenvector
matrix `S`, `mmQ` for `Q`, `mmV` for `V`, and `mmU` for `U`. When omitted,
`mmSigma` defaults to `mmLambda`, while `mmQ`, `mmV`, and `mmU` default to
`mmS`.
Use `output_dir` to preserve rendered artifacts from `render_eig_svg`.
Prefer `output_dir` for new code.

## Backsubstitution

- `matrixlayout.backsubst.backsubst_tex(**opts)`: emit TeX for system/cascade/solution blocks.
- `matrixlayout.backsubst.backsubst_svg(**opts)`: render the back-substitution document to SVG.

The back-substitution template uses `body_preamble` for body-local TeX setup.
The back-substitution template requires `systeme.sty` from the TeX toolchain.
Use `output_dir` to preserve rendered artifacts from `backsubst_svg`.
Prefer `output_dir` for new code.

## Formatting and selectors

- `matrixlayout.formatting.latexify(x)`: default scalar formatter to TeX strings.
- `matrixlayout.formatting.norm_str(x)`: normalize Julia/Python symbols to strings.
- `matrixlayout.formatting.make_decorator(**opts)`: build an entry decorator from options.
- `matrixlayout.formatting.decorator_box()`: wrap entry in `\\boxed{}`.
- `matrixlayout.formatting.decorator_color(color)`: wrap entry in `\\color{}`.
- `matrixlayout.formatting.decorator_bg(color)`: wrap entry in `\\colorbox{}`.
- `matrixlayout.formatting.decorator_bf()`: wrap entry in `\\mathbf{}`.
- `matrixlayout.formatting.sel_entry/sel_box/sel_row/sel_col/sel_rows/sel_cols/sel_all`: entry selector helpers.
- `matrixlayout.formatting.sel_vec/sel_vec_range`: eigen/SVD vector selector helpers.
- `matrixlayout.formatting.decorate_tex_entries`: apply decorators to formatted entries.
- `matrixlayout.formatting.expand_entry_selectors`: expand selectors to explicit coordinates.
- `matrixlayout.formatting.apply_decorator`: apply a decorator to a single entry.

## Rendering and templates

- `matrixlayout.render.render_svg`: render TeX to SVG.
- `matrixlayout.render.render_svg_with_artifacts`: render TeX to SVG and keep TeX/PDF/SVG artifacts.
- `matrixlayout.nicematrix_decor.render_delim_callout(s)`: render delimiter callouts as TikZ.
- `matrixlayout.nicematrix_decor.validate_callouts`: validate callout descriptors (strict or non-strict).
- `matrixlayout.specs.validate_ge_spec`, `matrixlayout.specs.validate_qr_spec`: lightweight spec validation.
- `matrixlayout.nicematrix_decor.infer_ge_matrix_callouts`: infer matrix callouts from a GE grid.
- `matrixlayout.jinja_env.make_environment/get_environment`: create or fetch Jinja environments.
- `matrixlayout.jinja_env.render_template/render_string`: render templates/strings.
- `matrixlayout.shortcascade.normalize_backsub_trace`: normalize shortcascade traces.
- `matrixlayout.shortcascade.mk_shortcascade_lines`: build shortcascade LaTeX lines.


