# Common Pitfalls

A short list of issues that commonly appear when first using matrixlayout.

## Rendering failures

- Toolchain binaries may be missing from `PATH`.
- If `*_svg` fails, call `*_tex` and inspect the emitted LaTeX.
- Try a different `toolchain_name` to isolate toolchain-specific issues.
- Back-substitution rendering requires `systeme.sty`; install the TeX package set that provides it if the template fails with a missing-file error.

## Crop and padding

- `crop="tight"` uses the renderer's tight bounding box; this can hide
  annotations that sit outside the matrix.
- Increase `padding` when using long arrows or labels.

## Callouts and names

- Prefer grid-targeted callouts such as
  `{"grid": (block_row, block_col), "label": "...", "side": "right"}`.
- Name-targeted callouts attach to `\SubMatrix` delimiter names; ensure the
  target name is present if you use `"name": ...` directly.
- Prefer grid-targeted callouts over delimiter-name callouts. Legacy delimiter names such as `A0`, `A1`, or `E1` are renderer-compatibility details and should not appear in new specs.

## Label placement

- `grid` refers to block `(row, col)`, not entry coordinates.
- Labels may be placed into adjacent empty blocks; if no empty block exists,
  matrixlayout inserts padding rows/cols.

## Specs vs explicit kwargs

- If both are provided, explicit kwargs take precedence.
