# Rendering

Rendering uses `jupyter_tikz` under the hood.

## Prerequisites

Rendering requires a LaTeX toolchain and a PDF/DVI-to-SVG converter
(e.g., `latexmk` with `dvisvgm`, `pdf2svg`, or `pdftocairo`) available on PATH.

## SVG output

```python
from matrixlayout.ge import render_ge_svg
svg = render_ge_svg(matrices=[[None, [[1]]]])
```

`render_ge_svg` forwards its inputs to `render_ge_tex` before rendering. If you pass both
`spec`/`specs` and explicit kwargs, explicit kwargs take precedence.

## Keep artifacts for debugging

```python
from matrixlayout.ge import render_ge_svg

svg = render_ge_svg(
    matrices=[[None, [[1, 2], [3, 4]]]],
    output_dir="./_out",
    output_stem="ge_debug",
    crop="tight",
    padding=(2, 2, 2, 2),
)
```

Inspect `./_out/ge_debug.tex` when debugging layout issues.

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
