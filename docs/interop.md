# Interop

matrixlayout accepts Julia-style inputs when called via PythonCall/PyCall.

- Julia Symbols may stringify as `:name` or `Symbol(:name)` and are normalized.
- Toolchain/crop options accept Julia Symbols (e.g. `:tight`).
- Julia arrays wrapped by PythonCall are handled in la_figures; matrixlayout expects Python lists or sympy matrices.

Interop focuses on option normalization; layout data should be converted to
Python-native lists before calling matrixlayout entry points.

## Recommendation

Perform matrix computations in the host language and pass concrete values to
matrixlayout; avoid passing symbolic wrappers when possible.
