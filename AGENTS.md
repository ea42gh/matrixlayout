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

## Interoperability Constraint

Maintain Python/Julia interoperability throughout the migration.

This is a first-class constraint, not an afterthought. Any API cleanup in
`matrixlayout` or `LAFigureSpecs` must preserve, or be migrated in lockstep
with, the Julia bridge used by `GenLAProblems` and `LATeachingSuite`.

Preserve or explicitly migrate:

1. Python module names and import paths used from Julia.
2. Keyword names and defaults used through PythonCall.
3. Return shapes for spec dictionaries, bundles, and extracted matrix helpers.
4. Display/render helper behavior that Julia wrappers depend on.
5. Interop-friendly argument conventions for nested lists, strings, and
   matrix-like inputs.

Capability areas that must be checked when touched:

- GE
- QR / Gram-Schmidt
- eigen / SVD
- rendering / display helpers
- bundle/spec extraction helpers

## Legacy `nM.*` Surface

The `nM.*` functions were the original top-level functions in early versions of
these packages.

Compatibility rule:

- `nM.*` entry points do **not** need to be preserved indefinitely.
- They may be removed or reduced once newer top-level functions with equivalent
  functionality exist and are documented.
- When replacing an `nM.*` path, prefer preserving capability rather than name.
- Keep bridge tests focused on current canonical entry points, not on retaining
  every historical `nM.*` alias.

## Additional Requirements

Apply these requirements across migration slices:

1. Preserve capability families, not just function names.
   GE, QR / Gram-Schmidt, eigen / SVD, backsub / system display, spec
   extraction, and rendering must continue to exist through supported top-level
   entry points.
2. Distinguish canonical APIs from compatibility APIs.
   New code should target the canonical entry points; compatibility wrappers may
   remain temporarily but should not drive new design.
3. Keep deterministic small-matrix examples.
   Use fixed seeds or fixed matrices for tests, docs, and Binder notebooks so
   teaching outputs remain stable.
4. Treat notebook output shape as a contract.
   Exact SVG bytes need not always match, but bundle keys, matrix extraction
   shapes, labels, and major callout structure should remain stable.
5. Keep informative no-toolchain / no-Python failure behavior covered by tests.
6. Update all relevant documentation files in the same slice as code changes.
   Do not update only code and tests while leaving README files, docs pages,
   Binder/demo material, or public examples stale.
7. Update all relevant unit tests in the same slice as code changes.
   Do not leave intended behavior changes or new canonical wrappers waiting for
   a later test-only cleanup pass.

## Package-Specific Requirements

### `matrixlayout`

- Remain layout-only; no algorithm creep from `LAFigureSpecs` or Julia
  workflow layers.
- Maintain typed-spec and dict-spec parity where both paths exist.
- Keep the SVG rendering boundary singular and explicit.
- Preserve TeX/spec functionality without requiring a TeX toolchain.

### `LAFigureSpecs`

- Remain the canonical Python facade for teaching-oriented figure generation.
- Preserve top-level reachability for current capability families even if
  internals are restructured.
- Keep bundle contracts stable: `spec`, `tex`, `svg`, `data`, `render_error`.
- Keep PythonCall-friendly argument conventions stable where they are relied on
  by Julia wrappers.

## Validation Standard

For each slice:

- Run `matrixlayout`: ruff, mypy, full pytest with coverage.
- Run `LAFigureSpecs`: full pytest and render smoke where available.
- Include at least one end-to-end `LAFigureSpecs -> matrixlayout` check for any
  touched feature area.
- Include at least one end-to-end Julia bridge path for any touched feature
  area:
  `GenLAProblems` or `LATeachingSuite` -> `LAFigureSpecs` -> `matrixlayout`.
- When changing any interop-facing API, verify both:
  - direct Python usage
  - Julia/PythonCall-mediated usage

## Test Expectations

### Add or maintain these `matrixlayout` tests

- Spec normalization equivalence tests for canonical fields vs temporary aliases.
- Failure-contract tests for invalid render opts, callouts, labels, and block
  targeting.
- Golden-lite structure tests that assert expected TeX fragments or layout
  markers rather than only full SVG snapshots.
- Cross-family consistency tests for shared options such as `fig_scale`,
  `decorators`, `output_dir`, and `render_opts`.

### Add or maintain these `LAFigureSpecs` tests

- Canonical family coverage for GE, QR, eigen, and SVD:
  `*_spec`, `*_tex`, `*_svg`, `*_bundle`.
- Bundle contract invariants:
  required keys, `render_error` behavior, and contents of `data`.
- Cross-path equivalence:
  spec-then-render vs direct convenience render helpers.
- Display/render helper tests for `show_svg`, `latex_svg`,
  `latex_document_svg`, and `lshow_svg`.
- PythonCall-oriented input tests for interop-friendly nested lists / scalar
  inputs.

## Binder / Demo Expectations

### `matrixlayout`

Keep or add Binder/demo examples for:

- minimal GE layout from a raw spec dict
- QR layout from a raw matrix stack
- eigen / SVD display from raw specs
- decorator / formatting showcase
- spec debugging / normalization examples

### `LAFigureSpecs`

Keep or add Binder/demo examples for:

- teaching workflow overview notebook covering GE, QR, eigen, and SVD
- spec-first / render-second notebook
- Julia interop notebook
- backsub / system display notebook
- decorator and recipe notebook

## Documentation Task

When a migration slice changes renderer behavior, spec shape, package naming,
or interop expectations, update all relevant documentation files in the same
change.

This includes, as applicable:

- package `README.md`
- docs pages and migration notes
- Binder/demo notebooks and launch instructions
- public code examples embedded in tests or comments

## Unit Test Task

When a migration slice changes renderer behavior, spec shape, package naming,
interop expectations, or compatibility wrappers, update the relevant unit tests
in the same change.

This includes, as applicable:

- updating existing tests for intentionally changed behavior
- adding characterization tests for behavior that must remain stable
- adding tests for new canonical entry points
- keeping interop-focused tests aligned with Julia/Python bridge usage
