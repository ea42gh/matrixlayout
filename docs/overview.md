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

## Rendering boundary

Matrixlayout renders through `jupyter_tikz`. The rendering layer is external;
matrixlayout does not manage toolchain installation or environment setup.

## Data flow

Algorithmic code produces a spec → matrixlayout formats entries → optional
decorators are applied → TeX is emitted → SVG rendering is delegated.
