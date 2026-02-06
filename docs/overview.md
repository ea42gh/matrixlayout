# Overview

Matrixlayout defines a grid-of-matrices model, eigenproblem/SVD summary tables,
and a TeX rendering boundary. Users provide matrices or a spec; matrixlayout
produces TeX and optional SVG.

Terms used here are summarized in `glossary.md`.

## Core model

- A grid is a 2D list of matrix blocks.
- A spec supplies layout options and annotations (pivots, callouts, paths).
- Decorators apply TeX transforms to formatted entries.

Specs are plain dictionaries; convenience helpers in `la_figures` construct them
from algorithmic traces.

### Precedence

When both a spec and explicit keyword arguments are provided, explicit arguments
take precedence. This lets you reuse a spec while overriding a few fields.

### Labels

Row/column labels are attached to a block and then placed into available blank
rows/cols (if adjacent blocks are empty). If there are no empty blocks, the
labels are inserted by adding padding rows/cols to the block.

## Rendering boundary

Matrixlayout renders through `jupyter_tikz`. The rendering layer is external;
matrixlayout does not manage toolchain installation or environment setup.

## Compatibility matrix

| Component | Minimum | Notes |
| --- | --- | --- |
| Python | 3.9 | Tested with 3.9–3.12. |
| jupyter_tikz | itikz_port | TeX toolchains + SVG. |
| TeX toolchain | TeX Live 2022+ | Needed for SVG rendering. |

## Data flow

Algorithmic code produces a spec → matrixlayout formats entries → optional
decorators are applied → TeX is emitted → SVG rendering is delegated.
