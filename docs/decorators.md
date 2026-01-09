# Decorators

Decorators apply TeX styling to selected entries after formatting.

## Basics

```python
from matrixlayout.formatting import decorator_box, sel_entry

decorators = [
    {"grid": (0, 1), "entries": [sel_entry(0, 0)], "decorator": decorator_box()},
]
```

## Selectors

- `sel_entry(i, j)`
- `sel_row(i)`, `sel_col(j)`
- `sel_box((i0, j0), (i1, j1))`
