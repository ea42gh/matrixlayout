# Cross-Repository Plan

This repository is coupled to the sibling `LAFigureSpecs` project:

- `matrixlayout`: layout-only TeX/SVG rendering primitives.
- `LAFigureSpecs`: linear-algebra algorithms and spec builders that call `matrixlayout`.

`matrixlayout` is not treated as an independently stable public API for this work.
When a breaking cleanup improves the renderer API, migrate the corresponding
`LAFigureSpecs` call sites, specs, tests, docs, and notebooks in the same slice.

## Pre-Migration Cleanup

Before changing the API shape, clean both repositories without changing behavior:

1. Keep all current tests passing in both repositories.
2. Remove or isolate stale compatibility code only when no `LAFigureSpecs` caller uses it.
3. Improve local names and helper boundaries around existing behavior.
4. Add characterization tests for any behavior that is awkward but still relied on.
5. Update docs that describe existing behavior incorrectly.

Note:
- This repo does not currently have a Julia package root (`Project.toml`), so
  do not add a `CompatHelper.yml` workflow here unless that changes.

## API Cleanup Plan

Execute one item at a time, with tests and docs in the same change:

1. Rename GE RHS partition fields from `Nrhs` to `n_rhs`.
   Update `matrixlayout` specs/renderers and every `LAFigureSpecs` spec/call site.
2. Standardize block targeting on `grid=(block_row, block_col)`.
   Replace `grid_pos` and `block_row`/`block_col` in callout/spec inputs.
3. Clarify spec roles.
   Use canonical names for labels/annotations, high-level decorations, and
   callable entry decorators; remove ambiguous overlap where possible.
4. Normalize callout option names.
   Keep `angle_deg` and `length_mm`; remove `angle` and `length` aliases after
   migrating `LAFigureSpecs`.
5. Normalize label schema.
   Prefer one label payload spelling and one row/column targeting convention.
6. Rename TeX hooks.
   Replace ambiguous `preamble`/`extension` with names that distinguish document
   body setup from true LaTeX preamble insertion.
7. Refresh docs and notebooks after code migration.
   The `LAFigureSpecs` documentation should present algorithm-facing APIs; the
   `matrixlayout` documentation should present renderer/spec internals.

## Validation Standard

For each slice:

- Run `matrixlayout`: ruff, mypy, full pytest with coverage.
- Run `LAFigureSpecs`: full pytest and render smoke where available.
- Include at least one end-to-end `LAFigureSpecs -> matrixlayout` check for any
  touched feature area.
