# Specs

This page describes the layout specs consumed by matrixlayout. Specs are plain
dictionaries passed to `*_tex` or `*_svg` helpers.

## Field summary (core)

| Spec | Field | Type | Notes |
| --- | --- | --- | --- |
| GE | `matrices` | list | Grid of matrices (rows of blocks). |
| GE | `Nrhs` | int | RHS column count for augmented matrices. |
| GE | `block_align` | str | Align narrower blocks within a column (`left/right/center/auto`). |
| GE | `block_valign` | str | Align shorter blocks within a row (`top/bottom/center/auto`). |
| GE | `block_vspace_mm` | int | Vertical spacing between block rows (mm). |
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

Defaults are applied when fields are omitted (e.g., `Nrhs=0`, `decorators=None`,
`formatter=latexify`). See `matrixlayout.formatting` for decorator helpers.

## Defaults (GE)

- `Nrhs=0`
- `outer_hspace_mm=6`
- `block_vspace_mm=1`
- `cell_align="r"`
- `block_align=None` (auto right-align within block columns)
- `block_valign=None` (auto bottom-align within block rows)
- `decorations=None`
- `grid` defaults to `(0,0)` when the input is a single matrix

## GE specs

- `matrices`: grid of matrices (list of rows).
- `Nrhs`: number of RHS columns for augmented matrices.
- `block_align`: align narrower blocks within a block column (`left`, `right`, `center`, `auto`).
- `block_valign`: align shorter blocks within a block row (`top`, `bottom`, `center`, `auto`).
- `block_vspace_mm`: vertical spacing between block rows (mm).
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
