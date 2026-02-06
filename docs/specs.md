# Specs

Quick reference:

- `grid`: `(block_row, block_col)` index for the target submatrix.
- `entries`: list of `(i, j)` entry coordinates to decorate.
- `labels`: list of strings (or list-of-lists) for row/col labels.
- `label`: single string label for a callout or title.
- `side`: `left`, `right`, `above`, `below`, `top`, `bottom`.
- `hlines`/`vlines`: draw block separators.
- `box`: draw a box around entries or blocks.
- `angle`/`length_mm`: callout arrow direction/length.

Example:

```python
specs = [
    {"grid": (0, 0), "entries": [(0, 0)], "box": True},
    {"grid": (0, 0), "side": "right", "label": r"\\mathbf{A}", "angle": -35, "length_mm": 8},
]
```

This page describes the layout specs consumed by matrixlayout. Specs are plain
dictionaries passed to `*_tex` or `*_svg` helpers.

## Labels and callouts

Row/column labels (labels are placed in blank rows/cols when available):

```python
specs = [
    {"grid": (0, 0), "side": "above", "labels": ["x_1", "x_2", "x_3"]},
    {"grid": (0, 0), "side": "left", "labels": ["r_1", "r_2"]},
]
```

Callouts (arrow labels pointing at a block):

```python
specs = [
    {"grid": (0, 0), "label": r"\\mathbf{A}", "side": "right", "angle": -35, "length_mm": 8},
    {"grid": (0, 0), "label": r"\\mathbf{B}", "side": "below", "angle": 35, "length_mm": 8},
]
```

## Precedence and merging

- When a spec and explicit kwargs are both provided, explicit kwargs win.
- `specs` (label/callout targets) are merged into `label_rows`/`label_cols`.
- `variable_labels` are appended to `label_rows` with `side="below"`.
- When `strict=False`, extra/unknown fields in a spec dict are ignored instead of erroring.

If labels are attached to a block that has adjacent empty blocks, the labels are
placed in those blank rows/cols; otherwise extra padding rows/cols are inserted.

## Field summary (core)

| Spec | Field | Type | Notes |
| --- | --- | --- | --- |
| GE | `matrices` | list | Grid of matrices (rows of blocks). |
| GE | `Nrhs` | int | RHS column count for augmented matrices. |
| GE | `block_align` | str | Align narrower blocks within a column (`left/right/center/auto`). |
| GE | `block_valign` | str | Align shorter blocks within a row (`top/bottom/center/auto`). |
| GE | `block_vspace_mm` | int | Vertical spacing between block rows (mm). |
| GE | `label_rows` | list | Extra label rows attached to blocks. |
| GE | `label_cols` | list | Extra label columns attached to blocks. |
| GE | `label_gap_mm` | float | Gap between labels and blocks (mm). |
| GE | `variable_labels` | list | Shorthand for multiline annotations below a block. |
| GE | `format_nrhs` | bool | Whether to draw RHS separators in the column format. |
| GE | `decorations` | list | One-line decoration dicts (backgrounds, lines, callouts, entry styles). |
| GE | `pivot_locs` | list | TeX spans `(i-j)(k-l)` with optional styles. |
| GE | `callouts` | list | Labels attached to submatrix names. |
| QR | `matrices` | list | Grid of matrices (rows of blocks). |
| QR | `array_names` | bool | Enable default matrix labels. |
| QR | `decorators` | list | Entry decorators after formatting. |
| EIG/SVD | `lambda` | list | Eigenvalues. |
| EIG/SVD | `ma` | list | Multiplicities. |
| EIG/SVD | `evecs` | list | Eigenvector groups. |
| EIG/SVD | `sigma` | list | Singular values. |
| EIG/SVD | `sz` | tuple | SVD matrix size. |

## Spec schema (informal)

GE grid spec (core fields):

```text
{
  "matrices": list[list[matrix|None]],
  "Nrhs": int | list[int],
  "outer_hspace_mm": int,
  "block_vspace_mm": int,
  "cell_align": str,
  "block_align": str | None,
  "block_valign": str | None,
  "label_rows": list[LabelSpec],
  "label_cols": list[LabelSpec],
  "label_gap_mm": float,
  "variable_labels": list[LabelSpec],
  "decorations": list[DecorationSpec],
  "decorators": list[DecoratorSpec],
  "callouts": list[CalloutSpec],
  "pivot_locs": list,
  "rowechelon_paths": list,
}
```

LabelSpec (row/column labels):

```text
{
  "grid": (block_row, block_col),
  "side": "above" | "below" | "left" | "right",
  "rows": list[list[str]]  # for row labels
  "cols": list[list[str]]  # for column labels
}
```

DecorationSpec (one-line shorthand):

```text
{
  "grid": (block_row, block_col),
  "entries": [(i,j), ...] | None,
  "rows": range | None,
  "cols": range | None,
  "submatrix": (rows, cols) | None,
  "background": "color" | None,
  "hlines": int | list | "all" | "bounds" | "submatrix" | None,
  "vlines": int | list | "all" | "bounds" | "submatrix" | None,
  "label": "text" | None,
}
```

DecoratorSpec:

```text
{
  "grid": (block_row, block_col),
  "entries": [(i,j), ...],
  "decorator": callable,
}
```

CalloutSpec:

```text
{
  "name": "A0" | "E1" | ...,
  "label": "text",
  "side": "left" | "right",
  "angle_deg": float,
  "length_mm": float,
}
```

Defaults are applied when fields are omitted (e.g., `Nrhs=0`, `decorators=None`,
`formatter=latexify`). See `matrixlayout.formatting` for decorator helpers.

## Defaults (GE)

- `Nrhs=0`
- `outer_hspace_mm=6`
- `block_vspace_mm=1`
- `cell_align="r"`
- `block_align=None` (auto right-align within block columns)
- `block_valign=None` (auto bottom-align within block rows)
- `format_nrhs=True`
- `decorations=None`
- `grid` defaults to `(0,0)` when the input is a single matrix

## GE specs

- `matrices`: grid of matrices (list of rows).
- `Nrhs`: number of RHS columns for augmented matrices.
- `block_align`: align narrower blocks within a block column (`left`, `right`, `center`, `auto`).
- `block_valign`: align shorter blocks within a block row (`top`, `bottom`, `center`, `auto`).
- `block_vspace_mm`: vertical spacing between block rows (mm).
- `label_rows`: add label rows above/below a block.
- `label_cols`: add label columns left/right of a block.
- `label_gap_mm`: gap between label rows/cols and blocks (mm).
- `variable_labels`: convenience alias for `label_rows` with `side="below"`.
- `format_nrhs`: control whether RHS separators are emitted via the column format.
- `decorations`: high-level decoration specs (backgrounds, lines, callouts, entry styles).

The `decorations` list accepts one-line dicts. Each dict must include `grid=(row,col)`
unless the grid has a single matrix, in which case `grid` defaults to `(0,0)`,
and one of: `background`, `hlines`/`vlines`, `label`, or entry styling (`box`, `color`, `bold`).
Row/col selection supports ranges, lists, or slices via `rows`/`cols` or `submatrix`.

Quick reference:

| Key | Purpose |
| --- | --- |
| `grid` | Target block `(row,col)` |
| `submatrix` | Row/col range for highlights or entry styles |
| `rows`, `cols` | Alternative row/col selectors |
| `entries` | Explicit entry list |
| `background` | Block highlight color |
| `hlines`, `vlines` | Separator lines |
| `box`, `color`, `bold` | Entry styling |
| `label` | Callout label |

See `decorators.md` for full syntax and examples.
- `preamble`, `extension`, `nice_options`: LaTeX preamble and nicematrix options.
- `pivot_locs`: pivot box locations (`(i-j)(k-l)` spans).
- `rowechelon_paths`: polyline specs for row echelon outlines.
- `callouts`: name/label callouts attached to submatrix delimiters.

Minimal example:

```python
spec = {
    "matrices": [[None, [[1, 2], [3, 4]]]],
    "Nrhs": 0,
    "pivot_locs": [("(1-1)(1-1)", "draw=red")],
}
```

Block alignment example (right-align a narrower block within its column):

```python
spec = {
    "matrices": [[None, [[1, 2, 3]]], [[[4, 5]], [[6, 7, 8]]]],
    "block_align": "right",
}
```

Callouts and row-echelon paths:

```python
spec = {
    "matrices": [[None, [[1, 2], [3, 4]]]],
    "callouts": [
        {"name": "A0", "label": r"$A$", "anchor": "right", "angle_deg": -35, "length_mm": 8},
    ],
    "rowechelon_paths": [
        r"\draw[blue,line width=0.4mm] (1-1) -- (2-1) -- (2-2);",
    ],
}
```

## Common patterns

- Use `pivot_locs` for explicit pivot boxes rather than manual TikZ rectangles.
- Keep `callouts` attached to submatrix names when labeling matrices.

## Common mistakes

- Wrong `grid` index: `grid` is `(block_row, block_col)`, not entry coordinates.
- Mixing `label` and `labels`: use `labels` for row/col lists, `label` for callouts.
- Forgetting `side`: labels/callouts require a `side` (`left/right/above/below`).
- Misusing `decorations` when `specs` are intended for labels/callouts.

## Specs vs decorations

Use `specs` for labels/callouts and layout-adjacent annotations. Use
`decorations` for entry styling, highlights, and lines. Both can coexist.

## QR specs

- `matrices`: grid of matrices (list of rows).
- `array_names`: optional matrix name labels.
- `decorators`: entry-level decorators applied after formatting.

Minimal example:

```python
spec = {
    "matrices": [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]]],
    "array_names": True,
}
```

QR spec with labels:

```python
specs = [
    {"grid": (0, 2), "side": "above", "labels": ["x_1", "x_2"]},
    {"grid": (0, 3), "side": "above", "labels": ["w_1", "w_2"]},
]
```

## Eigen/SVD specs

- `lambda`: eigenvalues.
- `ma`: algebraic multiplicities.
- `evecs`, `qvecs`, `uvecs`: eigenvector groups.
- `sigma`: singular values (SVD).
- `sz`: matrix size for SVD layout.

Minimal example:

```python
spec = {
    "lambda": [2, 3],
    "ma": [1, 1],
    "evecs": [[[1, 0]], [[0, 1]]],
}
```
