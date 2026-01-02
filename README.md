matrixlayout (prototype)
=======================

This snapshot contains the shared Jinja2 template environment used during migration
from nicematrix.py templates.

Included template
-----------------

The first migrated template is **BACKSUBST_TEMPLATE** (back-substitution / cascade)
as a package template: `matrixlayout/templates/backsubst.tex.j2`.

Public entry points:

- `matrixlayout.backsubst_tex(...) -> str` produces TeX source.
- `matrixlayout.backsubst_svg(...) -> str` compiles TeX and returns SVG text via
  `jupyter_tikz.render_svg` (opt-in smoke test only).

Back-substitution cascade formatting
-----------------------------------

To keep matrixlayout layout-only, the back-substitution *equations* should be
computed by an algorithmic package and passed in as a **trace**.

`backsubst_tex` / `backsubst_svg` accept `cascade_trace=...` (Option A), and
matrixlayout will format it into nested `\\ShortCascade` lines using:

- `matrixlayout.mk_shortcascade_lines(trace) -> list[str]`

The trace format is intentionally Julia-friendly: a mapping with `base` and
`steps`, where each step is a `(raw, substituted)` pair or a dict with keys
`raw`/`substituted`.

Run tests
---------

From this directory:

  python -m pytest

Optional: run end-to-end TeX→SVG smoke tests
--------------------------------------------

Rendering tests are skipped by default (to avoid requiring a TeX toolchain on
every machine). To enable them:

  MATRIXLAYOUT_RUN_RENDER_TESTS=1 python -m pytest

