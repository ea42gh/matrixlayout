# API

This is a lightweight index of primary entry points. All functions accept
spec dictionaries and return TeX or SVG strings.

See module docstrings for argument details and defaults.

## Public vs internal helpers

Public APIs are stable and documented below. Internal helpers are either
prefixed with `_` or live in modules that are not intended to be called
directly by users. If you need an internal helper, prefer a public wrapper.

## GE

- `matrixlayout.ge.render_ge_tex(matrices, **opts)`: emit TeX for a GE grid (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.render_ge_svg(matrices, **opts)`: render a GE grid to SVG (supports `block_align`/`block_valign` for narrower blocks).
- `matrixlayout.ge.grid_bundle(matrices, **opts)`: return TeX plus submatrix span metadata.
- `matrixlayout.ge.grid_submatrix_spans(matrices, **opts)`: return delimiter spans for a GE grid.
- `matrixlayout.ge.grid_line_specs(**opts)`: compute `submatrix_locs` entries for hlines/vlines.
- `matrixlayout.ge.grid_highlight_specs(**opts)`: compute `codebefore` entries for block highlights.
- `matrixlayout.ge.render_ge_tex_specs(specs)`: convert label/callout specs into `label_rows`/`label_cols`.
- `matrixlayout.ge.resolve_ge_grid_name(name, **opts)`: resolve matrix names (e.g., `A0`, `E1`) to grid positions.
- `matrixlayout.ge.decorations_help()`: return help text for `decorations` spec syntax.

Common options: `specs` (labels/callouts), `decorations` (hlines/vlines/boxes),
`output_dir`/`output_stem` (persist TeX/SVG). Label rows/cols are inserted only
when needed; existing blank rows/cols are reused. Explicit kwargs override values
provided by a spec.

Specs vs decorations:
use `specs` for labels/callouts and `decorations` for entry styling/lines.

## QR

- `matrixlayout.qr.render_qr_tex(matrices, **opts)`: emit TeX for a QR grid (accepts `specs`).
- `matrixlayout.qr.render_qr_svg(matrices, **opts)`: render a QR grid to SVG (accepts `specs`).
- `matrixlayout.qr.qr_grid_bundle(matrices, **opts)`: return TeX plus submatrix span metadata.
- `matrixlayout.qr.resolve_qr_grid_name(name, **opts)`: resolve QR grid matrix names to positions.

Common options: `specs` (labels/callouts), `output_dir`/`output_stem` (persist TeX/SVG).

## Eigen/SVD

- `matrixlayout.eigproblem.render_eig_tex`: emit TeX for eigen/SVD tables.
- `matrixlayout.eigproblem.render_eig_svg`: render eigen/SVD tables to SVG.

## Backsubstitution

- `matrixlayout.backsubst.backsubst_tex(**opts)`: emit TeX for system/cascade/solution blocks.
- `matrixlayout.backsubst.backsubst_svg(**opts)`: render the back-substitution document to SVG.

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
- `matrixlayout.nicematrix_decor.infer_ge_matrix_labels`: infer labels from a GE grid.
- `matrixlayout.nicematrix_decor.infer_ge_layer_callouts`: infer layer callouts from a GE grid.
- `matrixlayout.jinja_env.make_environment/get_environment`: create or fetch Jinja environments.
- `matrixlayout.jinja_env.render_template/render_string`: render templates/strings.
- `matrixlayout.shortcascade.normalize_backsub_trace`: normalize shortcascade traces.
- `matrixlayout.shortcascade.mk_shortcascade_lines`: build shortcascade LaTeX lines.
