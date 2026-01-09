# Interop

matrixlayout accepts Julia-style inputs when called via PythonCall/PyCall.

- Julia Symbols may stringify as `:name` or `Symbol(:name)` and are normalized.
- Julia arrays wrapped by PythonCall are handled in la_figures; matrixlayout expects Python lists or sympy matrices.
