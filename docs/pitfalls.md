# Common Pitfalls

A short list of issues that commonly appear when first using matrixlayout.

## Rendering failures

- Toolchain binaries may be missing from `PATH`.
- If `*_svg` fails, call `*_tex` and inspect the emitted LaTeX.
- Try a different `toolchain_name` to isolate toolchain-specific issues.

## Crop and padding

- `crop="tight"` uses the renderer's tight bounding box; this can hide
  annotations that sit outside the matrix.
- Increase `padding` when using long arrows or labels.

## Callouts and names

- Callouts attach to submatrix names; ensure names are present.
- When using legacy submatrix naming, enable `legacy_submatrix_names=True`.
