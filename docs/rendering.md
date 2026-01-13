# Rendering

Rendering uses `jupyter_tikz` under the hood.

## Prerequisites

Rendering requires a LaTeX toolchain and a PDF/DVI-to-SVG converter
(e.g., `latexmk` with `dvisvgm`, `pdf2svg`, or `pdftocairo`) available on PATH.

## SVG output

```python
from matrixlayout.ge import grid_svg
svg = grid_svg(matrices=[[None, [[1]]]])
```

## Toolchains

Pass `toolchain_name` to select a specific LaTeX toolchain.

Toolchain options:

- `pdftex_pdftocairo`
- `pdftex_pdf2svg`
- `pdftex_dvisvgm`
- `xelatex_pdftocairo`
- `xelatex_pdf2svg`
- `xelatex_dvisvgm`

Default selection is delegated to `jupyter_tikz`: it uses an explicit argument
if provided, then a programmatic override, then `JUPYTER_TIKZ_DEFAULT_TOOLCHAIN`,
then the first available toolchain in its candidate list.

Default resolution is runtime-dependent on tool availability.

## Crop and padding

Use `crop` and `padding` to control bounding box behavior. `crop="tight"`
uses the renderer’s tight bounding box; `padding` accepts a 4-tuple.

## Frame and output_dir

Use `frame=True` to visualize the computed bounding box. Pass `output_dir`
to persist TeX/SVG artifacts for inspection.

`output_stem` controls the file prefix when writing artifacts.

## Troubleshooting

If rendering fails:

- Inspect the TeX by calling `*_tex` instead of `*_svg`.
- Set `output_dir` and re-run to capture artifacts for inspection.
- Try a different `toolchain_name` to isolate toolchain-specific issues.
