"""Helper functions for back-substitution layouts."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Union

from .formatting import apply_decorator, expand_entry_selectors


def as_lines(value: Union[str, Sequence[str], None]) -> list[str]:
    """Normalize a string or sequence of strings to a list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def as_scale(value: Optional[Union[str, float, int]]) -> Optional[str]:
    """Normalize a scale value to the string used by the TeX template."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return format(value, "g")


def apply_line_decorators(
    lines: List[str],
    decorators: Optional[Sequence[Any]],
    block: str,
    *,
    strict: bool,
) -> List[str]:
    """Apply decorator specs to one textual back-substitution block."""
    if not decorators:
        return lines
    if not lines:
        if strict:
            _raise_if_targeted_empty_block(decorators, block)
        return lines

    nrows, ncols = len(lines), 1
    block_key = block.lower()
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("block", spec_item.get("target"))
        if key is None or str(key).lower() not in {block_key, f"{block_key}_txt"}:
            continue
        dec = spec_item.get("decorator")
        if not callable(dec):
            raise ValueError("decorator must be callable")
        applied = 0
        for i, j in expand_entry_selectors(spec_item.get("entries"), nrows, ncols, allow_int=True):
            if i < 0 or i >= nrows or j != 0:
                continue
            base = lines[i]
            lines[i] = apply_decorator(dec, i, j, base, base)
            applied += 1
        if strict and applied == 0:
            raise ValueError("decorator selector did not match any entries")
    return lines


def _raise_if_targeted_empty_block(decorators: Sequence[Any], block: str) -> None:
    block_key = block.lower()
    for spec_item in decorators:
        if not isinstance(spec_item, dict):
            raise ValueError("decorators must be dict specs")
        key = spec_item.get("block", spec_item.get("target"))
        if key is None or str(key).lower() not in {block_key, f"{block_key}_txt"}:
            continue
        if not callable(spec_item.get("decorator")):
            raise ValueError("decorator must be callable")
        raise ValueError("decorator selector did not match any entries")
