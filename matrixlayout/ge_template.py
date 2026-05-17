"""Template normalization helpers for GE nicematrix output."""

from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from .formatting import norm_str
from .specs import PivotBox, RowEchelonPath, SubMatrixLoc, TextAt


BODY_PREAMBLE_FORBIDDEN = (
    r"\\documentclass",
    r"\\usepackage",
    r"\\RequirePackage",
    r"\\geometry\s*\{",
)


def validate_body_preamble(preamble: str) -> None:
    """Reject LaTeX preamble directives in the GE body preamble hook."""
    if not preamble:
        return
    for pattern in BODY_PREAMBLE_FORBIDDEN:
        if re.search(pattern, preamble):
            raise ValueError(
                "The `body_preamble` parameter is injected into the document body. "
                "Do not include LaTeX preamble directives (e.g. \\usepackage, \\geometry). "
                "Use `document_preamble=` for true LaTeX preamble insertions."
            )


def append_nicematrix_option(nice_options: Optional[str], opt: str) -> str:
    opts = (nice_options or "").strip()
    if not opts:
        return opt
    if opt in opts:
        return opts
    return f"{opts}, {opt}"


def merge_list(explicit: Optional[Sequence[Any]], spec_val: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    """Merge list-like fields by concatenation, preserving explicit values first."""
    if explicit is None and spec_val is None:
        return None
    out: List[Any] = []
    if explicit is not None:
        out.extend(list(explicit))
    if spec_val is not None:
        out.extend(list(spec_val))
    return out


def merge_callouts(explicit: Optional[Any], spec_val: Optional[Any]) -> Optional[Any]:
    """Merge callouts while preserving boolean auto-callout flags."""
    if isinstance(explicit, bool) or isinstance(spec_val, bool):
        if explicit is None:
            return spec_val
        if spec_val is None:
            return explicit
        if explicit != spec_val:
            raise ValueError(f"Conflicting values for callouts: explicit={explicit!r} spec={spec_val!r}")
        return explicit
    return merge_list(explicit, spec_val)


def julia_str(value: Any) -> str:
    """Normalize Julia/PythonCall/PyCall string-like values to plain strings."""
    if value is None:
        return ""
    return str(norm_str(value))


def coord_token(value: Any) -> str:
    """Convert a coordinate into an ``i-j`` token."""
    if isinstance(value, (tuple, list)) and len(value) == 2:
        row, col = value
        return f"{int(row)}-{int(col)}"
    text = str(value).strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    return text


def coord_paren(value: Any) -> str:
    """Convert a coordinate into parenthesized ``(i-j)`` form."""
    token = coord_token(value)
    if token.startswith("(") and token.endswith(")"):
        return token
    return f"({token})"


def fit_target(value: Any) -> str:
    """Normalize a fit target into the TeX form ``(i-j)(k-l)``."""
    if isinstance(value, (tuple, list)) and len(value) == 2 and all(
        isinstance(item, (tuple, list, str, int)) for item in value
    ):
        first, last = value
        return f"{coord_paren(first)}{coord_paren(last)}"

    text = str(value).strip()
    if text.startswith("{") and "}{" in text and text.endswith("}"):
        parts = re.findall(r"\{\s*([^}]+?)\s*\}", text)
        if len(parts) == 2:
            return f"({coord_token(parts[0])})({coord_token(parts[1])})"
    return text


def fit_span(value: Any) -> str:
    """Convert a span-like input into a fit target ``(i-j)(k-l)``."""
    if isinstance(value, str):
        text = value.strip()
        if "(" in text and ")" in text and "{" not in text:
            return text
    if isinstance(value, (tuple, list)) and len(value) == 2:
        first, last = value
        return coord_paren(first) + coord_paren(last)
    text = str(value).strip()
    parts = re.findall(r"\{\s*([^}]+?)\s*\}", text)
    if len(parts) == 2:
        return f"({parts[0]})({parts[1]})"
    return text


def normalize_mat_format(mat_format: str) -> str:
    """Normalize a LaTeX array preamble, accepting ``"cc"`` or ``"{cc}"``."""
    text = (mat_format or "").strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    return text


def normalize_mat_rep(mat_rep: str) -> str:
    r"""Normalize a matrix body before inserting it into the GE template."""
    if mat_rep is None:
        return ""
    text = str(mat_rep)
    return re.sub(r"(?<!\\)\\(?!\\)(\s+)", r"\\\\\1", text)


def guess_shape_from_mat_rep(mat_rep: str) -> Tuple[int, int]:
    """Best-effort ``(nrows, ncols)`` inferred from a TeX matrix body."""
    body = normalize_mat_rep(mat_rep)
    rows = [row.strip() for row in body.split(r"\\") if row.strip()]
    nrows = len(rows) if rows else 0
    ncols = 0
    for row in rows:
        ncols = max(ncols, row.count("&") + 1)
    return nrows, ncols


def normalize_submatrix_locs(submatrix_locs: Optional[Sequence[Any]]) -> List[Tuple[str, ...]]:
    r"""Normalize submatrix descriptors to ``(options, span[, left, right])``."""
    if not submatrix_locs:
        return []
    out: List[Tuple[str, ...]] = []

    for item in submatrix_locs:
        if len(item) == 2:
            opts, loc = item
            opts = julia_str(opts)

            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(isinstance(part, (tuple, list)) for part in loc):
                first, last = loc
                span = f"{{{coord_token(first)}}}{{{coord_token(last)}}}"
                out.append((opts, span))
                continue

            loc_text = str(loc).strip()

            if "{" in loc_text and "}" in loc_text:
                parts = re.findall(r"\{\s*([^}]+?)\s*\}", loc_text)
                if len(parts) != 2:
                    raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]
            else:
                parts = re.findall(r"\(\s*([^)]+?)\s*\)", loc_text)
                if len(parts) != 2:
                    raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]

        elif len(item) == 3:
            opts, first, last = item
            opts = julia_str(opts)

            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = coord_token(first)
            else:
                first = str(first).strip()
                if first.startswith("(") and first.endswith(")"):
                    first = first[1:-1].strip()

            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = coord_token(last)
            else:
                last = str(last).strip()
                if last.startswith("(") and last.endswith(")"):
                    last = last[1:-1].strip()

        elif len(item) == 4:
            opts, loc, left_delim, right_delim = item
            opts = julia_str(opts)

            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(isinstance(part, (tuple, list)) for part in loc):
                first, last = loc
                span = f"{{{coord_token(first)}}}{{{coord_token(last)}}}"
            else:
                loc_text = str(loc).strip()
                if "{" in loc_text and "}" in loc_text:
                    parts = re.findall(r"\{\s*([^}]+?)\s*\}", loc_text)
                    if len(parts) != 2:
                        raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                    first, last = parts[0], parts[1]
                else:
                    parts = re.findall(r"\(\s*([^)]+?)\s*\)", loc_text)
                    if len(parts) != 2:
                        raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                    first, last = parts[0], parts[1]
                span = f"{{{first}}}{{{last}}}"

            out.append((opts, span, julia_str(left_delim), julia_str(right_delim)))
            continue

        elif len(item) == 5:
            opts, first, last, left_delim, right_delim = item
            opts = julia_str(opts)

            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = coord_token(first)
            else:
                first = str(first).strip()
                if first.startswith("(") and first.endswith(")"):
                    first = first[1:-1].strip()

            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = coord_token(last)
            else:
                last = str(last).strip()
                if last.startswith("(") and last.endswith(")"):
                    last = last[1:-1].strip()

            span = f"{{{first}}}{{{last}}}"
            out.append((opts, span, julia_str(left_delim), julia_str(right_delim)))
            continue
        else:
            raise ValueError(
                "submatrix_locs entry must be a 2-, 3-, 4-, or 5-tuple, got: "
                f"{item!r}"
            )

        span = f"{{{first}}}{{{last}}}"
        out.append((opts, span))

    return out


def normalize_pivot_locs(pivot_locs: Optional[Sequence[Tuple[Any, Any]]]) -> List[Tuple[str, str]]:
    """Normalize pivot box descriptors for TikZ ``fit``."""
    if not pivot_locs:
        return []
    return [(fit_target(target), julia_str(style)) for target, style in pivot_locs]


def normalize_txt_with_locs(txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]]) -> List[Tuple[str, str, str]]:
    """Normalize text-at-coordinate descriptors."""
    if not txt_with_locs:
        return []
    return [(coord_paren(coord), str(text), julia_str(style)) for coord, text, style in txt_with_locs]


def coerce_submatrix_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for item in items:
        if isinstance(item, SubMatrixLoc):
            out.append(item.to_tuple())
        elif isinstance(item, dict):
            out.append(
                SubMatrixLoc(
                    opts=str(item.get("opts", "")),
                    start=str(item.get("start", "")),
                    end=str(item.get("end", "")),
                    left_delim=item.get("left_delim"),
                    right_delim=item.get("right_delim"),
                ).to_tuple()
            )
        else:
            out.append(item)
    return out


def coerce_pivot_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for item in items:
        if isinstance(item, PivotBox):
            out.append(item.to_tuple())
        elif isinstance(item, dict):
            out.append(
                PivotBox(
                    fit_target=str(item.get("fit_target", "")),
                    style=str(item.get("style", "")),
                ).to_tuple()
            )
        else:
            out.append(item)
    return out


def coerce_txt_with_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for item in items:
        if isinstance(item, TextAt):
            out.append(item.to_tuple())
        elif isinstance(item, dict):
            out.append(
                TextAt(
                    coord=str(item.get("coord", "")),
                    text=str(item.get("text", "")),
                    style=str(item.get("style", "")),
                ).to_tuple()
            )
        else:
            out.append(item)
    return out


def coerce_rowechelon_paths(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for item in items:
        if isinstance(item, RowEchelonPath):
            out.append(item.to_str())
        elif isinstance(item, dict):
            out.append(str(item.get("tikz", "")))
        else:
            out.append(str(item))
    return out
