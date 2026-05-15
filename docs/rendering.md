# Rendering

Rendering is delegated to `jupyter-tikz` under the hood.

Install the render extra when SVG output is needed:

```bash
python -m pip install "matrixlayout[render]"
```

The extra pins `jupyter-tikz` to the maintained `ea42gh/jupyter-tikz` revision
used in CI and Binder. Current PyPI releases do not provide the artifact-aware
renderer that matrixlayout uses for reliable diagnostics. If an incompatible
renderer is installed, matrixlayout raises an explicit version/capability error
before running LaTeX.

## Prerequisites

Rendering requires a LaTeX toolchain and a PDF/DVI-to-SVG converter
(e.g., `latexmk` with `dvisvgm`, `pdf2svg`, or `pdftocairo`) available on PATH.
The Python extra installs the Python renderer only; it does not install TeX Live,
Ghostscript, `latexmk`, `dvisvgm`, `pdf2svg`, or Poppler.

## SVG output

```python
from matrixlayout.ge import render_ge_svg
svg = render_ge_svg(matrices=[[None, [[1]]]])
```

`render_ge_svg` forwards its inputs to `render_ge_tex` before rendering. If you pass both
`spec`/`specs` and explicit kwargs, explicit kwargs take precedence.

## render_opts pass-through

All SVG renderers accept a `render_opts` mapping that is forwarded verbatim to
`jupyter-tikz`. Explicit keyword arguments (e.g., `crop`, `padding`,
`toolchain_name`) override any values supplied in `render_opts`.

```python
from matrixlayout.ge import render_ge_svg

svg = render_ge_svg(
    matrices=[[None, [[1, 2], [3, 4]]]],
    render_opts={
        "toolchain_name": "xelatex_dvisvgm",
        "crop": "tight",
        "padding": (4, 4, 4, 4),
        "frame": {"stroke": "#666", "stroke_width": 0.5},
        "exact_bbox": True,
    },
)
```

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
