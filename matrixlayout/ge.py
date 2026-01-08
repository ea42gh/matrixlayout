r"""
GE (Gaussian Elimination) template helpers.

This module generates TeX for the GE "matrix-of-matrices" layout. In this layout,
outer delimiters (and block delimiters) are drawn with `nicematrix`'s `\SubMatrix`
inside `\CodeAfter`.

Target: current `nicematrix`
----------------------------
The `\SubMatrix` command syntax (as of current nicematrix releases) uses a single
mandatory argument of the form `({i-j}{k-l})` followed by an *optional* key-value
list *after* the argument: `\SubMatrix({1-1}{3-3})[name=...]`.

Therefore, this module normalizes submatrix locations into `(options, span)` where
`span` is a string like `"{1-1}{2-2}"`, and the template emits:
    `\SubMatrix({span})[options]`
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union, Any, Dict
import os
import re

from .jinja_env import render_template
from .render import render_svg as _render_svg
from .formatting import latexify
from .specs import (
    GEGridBundle,
    GEGridSpec,
    GELayoutSpec,
    PivotBox,
    RowEchelonPath,
    SubMatrixLoc,
    SubMatrixSpan,
    TextAt,
)


def _julia_str(x: Any) -> str:
    """Normalize Julia/PythonCall/PyCall "string-like" values to plain strings.

    Julia Symbols frequently stringify to ``":name"`` (e.g. ``:tight``).
    For interop, strip a single leading colon.
    """
    if x is None:
        return ""
    s = str(x).strip()
    if s.startswith(":"):
        s = s[1:]
    return s


def _coord_token(x: Any) -> str:
    """Convert a coordinate into an ``i-j`` token (1-based indices).

    Accepted forms:
    - ``"(i-j)"`` or ``"i-j"``
    - ``(i, j)`` / ``[i, j]``
    """
    if isinstance(x, (tuple, list)) and len(x) == 2:
        i, j = x
        return f"{int(i)}-{int(j)}"
    s = str(x).strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    return s


def _coord_paren(x: Any) -> str:
    """Convert a coordinate into a parenthesized form ``(i-j)``."""
    tok = _coord_token(x)
    if tok.startswith("(") and tok.endswith(")"):
        return tok
    return f"({tok})"


def _fit_target(x: Any) -> str:
    """Normalize a fit target into the TeX form ``(i-j)(k-l)``.

    Accepted forms:
    - ``"(i-j)(k-l)"``
    - ``"{i-j}{k-l}"``
    - ``((i, j), (k, l))`` or ``[(i, j), (k, l)]``
    """
    if isinstance(x, (tuple, list)) and len(x) == 2 and all(isinstance(t, (tuple, list, str, int)) for t in x):
        first, last = x
        return f"{_coord_paren(first)}{_coord_paren(last)}"

    s = str(x).strip()
    if s.startswith("{") and "}{" in s and s.endswith("}"):
        # "{i-j}{k-l}" -> "(i-j)(k-l)"
        import re
        parts = re.findall(r"\{\s*([^}]+?)\s*\}", s)
        if len(parts) == 2:
            return f"({_coord_token(parts[0])})({_coord_token(parts[1])})"
    return s


def _fit_span(x: Any) -> str:
    """Convert a span-like input into a fit target ``(i-j)(k-l)``."""
    if isinstance(x, str):
        s = x.strip()
        # Already the desired form
        if "(" in s and ")" in s and "{" not in s:
            return s
    if isinstance(x, (tuple, list)) and len(x) == 2:
        a, b = x
        return _coord_paren(a) + _coord_paren(b)
    # Fallback: try to parse braces ``{i-j}{k-l}``
    s = str(x).strip()
    import re
    parts = re.findall(r"\{\s*([^}]+?)\s*\}", s)
    if len(parts) == 2:
        return f"({parts[0]})({parts[1]})"
    return s


def _normalize_mat_format(mat_format: str) -> str:
    """Normalize a LaTeX array preamble (accepts ``"cc"`` or ``"{cc}"``)."""
    s = (mat_format or "").strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    return s


def _normalize_mat_rep(mat_rep: str) -> str:
    r"""Normalize the matrix body.

    If a user accidentally writes a single backslash followed by whitespace
    instead of TeX's row separator ``\\``, convert it to ``\\``.
    """
    if mat_rep is None:
        return ""
    s = str(mat_rep)
    import re
    return re.sub(r"(?<!\\)\\(?!\\)(\s+)", r"\\\\\1", s)


def _guess_shape_from_mat_rep(mat_rep: str) -> Tuple[int, int]:
    """Best-effort (nrows, ncols) inferred from a TeX body like ``a & b \\\\ c & d``."""
    body = _normalize_mat_rep(mat_rep)
    rows = [r.strip() for r in body.split(r"\\") if r.strip()]
    nrows = len(rows) if rows else 0
    ncols = 0
    for r in rows:
        ncols = max(ncols, r.count("&") + 1)
    return nrows, ncols


def _normalize_submatrix_locs(
    submatrix_locs: Optional[
        Sequence[Union[Tuple[str, str], Tuple[str, str, str]]]
    ]
) -> List[Tuple[str, str]]:
    r"""Normalize submatrix descriptors to ``(options, span)``.

    Accepted input forms:
    - ``(opts, "{1-1}{2-2}")`` (legacy span encoding)
    - ``(opts, "(1-1)(2-2)")`` (two parenthesized tokens)
    - ``(opts, "(1-1)", "(2-2)")`` (explicit first/last, with parentheses)
    - ``(opts, "1-1", "2-2")`` (explicit first/last)

    Output span is always ``"{first}{last}"`` (including braces) and is meant to be
    used inside ``\SubMatrix({span})``.
    """
    if not submatrix_locs:
        return []
    # Each normalized entry is either (opts, span) or (opts, span, left, right)
    # where left/right are optional delimiters passed as _{...}^{...} to \SubMatrix.
    out: List[Tuple[str, ...]] = []
    import re

    for item in submatrix_locs:
        if len(item) == 2:
            opts, loc = item
            left_delim = right_delim = None
            opts = _julia_str(opts)

            # Accept a coord-pair span: ((i,j),(k,l))
            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(isinstance(t, (tuple, list)) for t in loc):
                first, last = loc
                first_tok = _coord_token(first)
                last_tok = _coord_token(last)
                span = f"{{{first_tok}}}{{{last_tok}}}"
                out.append((opts, span))
                continue

            loc_s = str(loc).strip()

            if "{" in loc_s and "}" in loc_s:
                # legacy "{r1-c1}{r2-c2}"
                parts = re.findall(r"\{\s*([^}]+?)\s*\}", loc_s)
                if len(parts) != 2:
                    raise ValueError(f"Bad legacy span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]
            else:
                # "(r1-c1)(r2-c2)"
                parts = re.findall(r"\(\s*([^)]+?)\s*\)", loc_s)
                if len(parts) != 2:
                    raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                first, last = parts[0], parts[1]

        elif len(item) == 3:
            opts, first, last = item
            left_delim = right_delim = None
            opts = _julia_str(opts)

            # Coordinates may be tuples/lists.
            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = _coord_token(first)
            else:
                first = str(first).strip()
                if first.startswith("(") and first.endswith(")"):
                    first = first[1:-1].strip()

            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = _coord_token(last)
            else:
                last = str(last).strip()
                if last.startswith("(") and last.endswith(")"):
                    last = last[1:-1].strip()
        elif len(item) == 4:
            # (opts, span, left, right)
            opts, loc, left_delim, right_delim = item
            opts = _julia_str(opts)

            # Re-use the same span parsing logic as the 2-tuple case.
            if isinstance(loc, (tuple, list)) and len(loc) == 2 and all(isinstance(t, (tuple, list)) for t in loc):
                first, last = loc
                first_tok = _coord_token(first)
                last_tok = _coord_token(last)
                span = f"{{{first_tok}}}{{{last_tok}}}"
            else:
                loc_s = str(loc).strip()
                if "{" in loc_s and "}" in loc_s:
                    parts = re.findall(r"\{\s*([^}]+?)\s*\}", loc_s)
                    if len(parts) != 2:
                        raise ValueError(f"Bad legacy span for submatrix_locs: {item!r}")
                    first, last = parts[0], parts[1]
                else:
                    parts = re.findall(r"\(\s*([^)]+?)\s*\)", loc_s)
                    if len(parts) != 2:
                        raise ValueError(f"Bad span for submatrix_locs: {item!r}")
                    first, last = parts[0], parts[1]
                span = f"{{{first}}}{{{last}}}"

            left = _julia_str(left_delim)
            right = _julia_str(right_delim)
            out.append((opts, span, left, right))
            continue

        elif len(item) == 5:
            # (opts, start, end, left, right)
            opts, first, last, left_delim, right_delim = item
            opts = _julia_str(opts)

            if isinstance(first, (tuple, list)) and len(first) == 2:
                first = _coord_token(first)
            else:
                first = str(first).strip()
                if first.startswith("(") and first.endswith(")"):
                    first = first[1:-1].strip()

            if isinstance(last, (tuple, list)) and len(last) == 2:
                last = _coord_token(last)
            else:
                last = str(last).strip()
                if last.startswith("(") and last.endswith(")"):
                    last = last[1:-1].strip()

            span = f"{{{first}}}{{{last}}}"
            left = _julia_str(left_delim)
            right = _julia_str(right_delim)
            out.append((opts, span, left, right))
            continue
        else:
            raise ValueError(
                "submatrix_locs entry must be a 2-, 3-, 4-, or 5-tuple, got: "
                f"{item!r}"
            )

        span = f"{{{first}}}{{{last}}}"
        out.append((opts, span))

    return out


def _normalize_pivot_locs(pivot_locs: Optional[Sequence[Tuple[Any, Any]]]) -> List[Tuple[str, str]]:
    """Normalize pivot box descriptors for tikz ``fit``.

    Accepts entries of the form:
    - ``(fit_target, style)`` where ``fit_target`` is either a string
      like ``"(1-1)(1-1)"`` or a pair ``((i,j),(k,l))``.
    """
    if not pivot_locs:
        return []
    out: List[Tuple[str, str]] = []
    for fit_target, style in pivot_locs:
        out.append((_fit_target(fit_target), _julia_str(style)))
    return out


def _normalize_txt_with_locs(txt_with_locs: Optional[Sequence[Tuple[Any, Any, Any]]]) -> List[Tuple[str, str, str]]:
    """Normalize label descriptors (coord, text, style)."""
    if not txt_with_locs:
        return []
    out: List[Tuple[str, str, str]] = []
    for coord, txt, style in txt_with_locs:
        out.append((_coord_paren(coord), str(txt), _julia_str(style)))
    return out


def _coerce_submatrix_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for it in items:
        if isinstance(it, SubMatrixLoc):
            out.append(it.to_tuple())
        elif isinstance(it, dict):
            out.append(
                SubMatrixLoc(
                    opts=str(it.get("opts", "")),
                    start=str(it.get("start", "")),
                    end=str(it.get("end", "")),
                    left_delim=it.get("left_delim"),
                    right_delim=it.get("right_delim"),
                ).to_tuple()
            )
        else:
            out.append(it)
    return out


def _coerce_pivot_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for it in items:
        if isinstance(it, PivotBox):
            out.append(it.to_tuple())
        elif isinstance(it, dict):
            out.append(
                PivotBox(
                    fit_target=str(it.get("fit_target", "")),
                    style=str(it.get("style", "")),
                ).to_tuple()
            )
        else:
            out.append(it)
    return out


def _coerce_txt_with_locs(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for it in items:
        if isinstance(it, TextAt):
            out.append(it.to_tuple())
        elif isinstance(it, dict):
            out.append(
                TextAt(
                    coord=str(it.get("coord", "")),
                    text=str(it.get("text", "")),
                    style=str(it.get("style", "")),
                ).to_tuple()
            )
        else:
            out.append(it)
    return out


def _coerce_rowechelon_paths(items: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    if items is None:
        return None
    out: List[Any] = []
    for it in items:
        if isinstance(it, RowEchelonPath):
            out.append(it.to_str())
        elif isinstance(it, dict):
            out.append(str(it.get("tikz", "")))
        else:
            out.append(str(it))
    return out



def _coerce_layout_spec(layout: Any) -> Optional[GELayoutSpec]:
    """Coerce ``layout`` into a :class:`GELayoutSpec` (or None)."""
    if layout is None:
        return None
    if isinstance(layout, GELayoutSpec):
        return layout
    if isinstance(layout, dict):
        return GELayoutSpec.from_dict(layout)
    raise TypeError(f"layout must be a GELayoutSpec or dict, not {type(layout).__name__}")


def _coerce_grid_spec(spec: Any) -> Optional[GEGridSpec]:
    if spec is None:
        return None
    if isinstance(spec, GEGridSpec):
        return spec
    if isinstance(spec, dict):
        return GEGridSpec.from_dict(spec)
    raise TypeError(f"spec must be a GEGridSpec or dict, not {type(spec).__name__}")


_BODY_PREAMBLE_FORBIDDEN = (
    r"\\documentclass",
    r"\\usepackage",
    r"\\RequirePackage",
    # Note: use regex whitespace (\s), not a literal backslash-s.
    r"\\geometry\s*\{",
)


def _validate_body_preamble(preamble: str) -> None:
    """Guardrail for the GE template's ``preamble`` hook.

    The GE template injects ``preamble`` into the document *body* (after
    ``\\begin{document}``). Users must not place LaTeX preamble directives here.
    Use ``extension=...`` for true preamble insertions.
    """
    if not preamble:
        return
    for pat in _BODY_PREAMBLE_FORBIDDEN:
        if re.search(pat, preamble):
            raise ValueError(
                "The `preamble` parameter is injected into the document body. "
                "Do not include LaTeX preamble directives (e.g. \\usepackage, \\geometry). "
                "Use `extension=` for preamble insertions."
            )


def _append_nicematrix_option(nice_options: Optional[str], opt: str) -> str:
    opts = (nice_options or "").strip()
    if not opts:
        return opt
    if opt in opts:
        return opts
    return f"{opts}, {opt}"


def _merge_scalar(field: str, explicit: Any, spec_val: Any) -> Any:
    """Merge a scalar field from explicit kwargs and layout spec."""
    if spec_val is None:
        return explicit
    if explicit is None:
        return spec_val
    if explicit != spec_val:
        raise ValueError(f"Conflicting values for {field}: explicit={explicit!r} spec={spec_val!r}")
    return explicit


def _merge_list(explicit: Optional[Sequence[Any]], spec_val: Optional[Sequence[Any]]) -> Optional[List[Any]]:
    """Merge list-like fields by concatenation (explicit first)."""
    if explicit is None and spec_val is None:
        return None
    out: List[Any] = []
    if explicit is not None:
        out.extend(list(explicit))
    if spec_val is not None:
        out.extend(list(spec_val))
    return out


def _merge_callouts(explicit: Optional[Any], spec_val: Optional[Any]) -> Optional[Any]:
    """Merge callouts, preserving boolean auto-callout flags."""
    if isinstance(explicit, bool) or isinstance(spec_val, bool):
        if explicit is None:
            return spec_val
        if spec_val is None:
            return explicit
        if explicit != spec_val:
            raise ValueError(f"Conflicting values for callouts: explicit={explicit!r} spec={spec_val!r}")
        return explicit
    return _merge_list(explicit, spec_val)

def ge_tex(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    txt_with_locs: Optional[Sequence[Any]] = None,
    rowechelon_paths: Optional[Sequence[Any]] = None,
    callouts: Optional[Sequence[Any]] = None,
    matrix_labels: Optional[Sequence[Any]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = None,
    create_extra_nodes: Optional[bool] = None,
    create_medium_nodes: Optional[bool] = None,
    outer_delims: Optional[bool] = None,
    outer_delims_name: Optional[str] = None,
    outer_delims_span: Optional[Tuple[int, int]] = None,
    callout_name_map: Optional[Mapping[Tuple[int, int], str]] = None,
) -> str:
    r"""Populate the GE template and return TeX."""
    mat_format_norm = _normalize_mat_format(mat_format)
    mat_rep_norm = _normalize_mat_rep(mat_rep)

    spec = _coerce_layout_spec(layout)
    # Merge string hooks from layout spec *before* validation, so guardrails
    # apply consistently regardless of whether the user supplies values via
    # explicit kwargs or the layout object.
    if spec is not None:
        if getattr(spec, "extension", None):
            # Layout spec is treated as the "base" template configuration.
            # Explicit kwargs are appended so users can override definitions.
            extension = (spec.extension or "") + ("\n" if (spec.extension and extension) else "") + (extension or "")
        if getattr(spec, "preamble", None):
            preamble = (spec.preamble or "") + ("\n" if (spec.preamble and preamble) else "") + (preamble or "")

    _validate_body_preamble(preamble or "")

    # Merge remaining layout fields.
    if spec is not None:
        nice_options = _merge_scalar("nice_options", nice_options, spec.nice_options)
        landscape = _merge_scalar("landscape", landscape, spec.landscape)
        create_cell_nodes = _merge_scalar("create_cell_nodes", create_cell_nodes, spec.create_cell_nodes)
        create_extra_nodes = _merge_scalar("create_extra_nodes", create_extra_nodes, spec.create_extra_nodes)
        create_medium_nodes = _merge_scalar("create_medium_nodes", create_medium_nodes, spec.create_medium_nodes)
        outer_delims = _merge_scalar("outer_delims", outer_delims, spec.outer_delims)
        outer_delims_name = _merge_scalar("outer_delims_name", outer_delims_name, spec.outer_delims_name)
        outer_delims_span = _merge_scalar("outer_delims_span", outer_delims_span, spec.outer_delims_span)

        codebefore = _merge_list(codebefore, spec.codebefore)
        submatrix_locs = _merge_list(submatrix_locs, spec.submatrix_locs)
        submatrix_names = _merge_list(submatrix_names, spec.submatrix_names)
        pivot_locs = _merge_list(pivot_locs, spec.pivot_locs)
        txt_with_locs = _merge_list(txt_with_locs, spec.txt_with_locs)
        rowechelon_paths = _merge_list(rowechelon_paths, spec.rowechelon_paths)
        callouts = _merge_callouts(callouts, spec.callouts)
        callouts = _merge_callouts(callouts, spec.matrix_labels)

    submatrix_locs = _coerce_submatrix_locs(submatrix_locs)
    pivot_locs = _coerce_pivot_locs(pivot_locs)
    txt_with_locs = _coerce_txt_with_locs(txt_with_locs)
    rowechelon_paths = _coerce_rowechelon_paths(rowechelon_paths)

    # Apply historical defaults after layout merging.
    if nice_options is None:
        nice_options = "vlines-in-sub-matrix = I"
    if landscape is None:
        landscape = False
    if create_cell_nodes is None:
        create_cell_nodes = True
    if create_extra_nodes is None:
        create_extra_nodes = False
    if create_medium_nodes is None:
        create_medium_nodes = False
    if outer_delims is None:
        outer_delims = False
    if outer_delims_name is None:
        outer_delims_name = "A0x0"

    if create_extra_nodes:
        nice_options = _append_nicematrix_option(nice_options, "create-extra-nodes")
    if create_medium_nodes:
        nice_options = _append_nicematrix_option(nice_options, "create-medium-nodes")

    # figure scale: the GE template currently supports TeX wrappers in the template itself
    fig_scale_open = fig_scale_close = ""
    if fig_scale is not None:
        if isinstance(fig_scale, (int, float)) and float(fig_scale) != 1.0:
            fig_scale_open = rf"\scalebox{{{fig_scale}}}{{%"
            fig_scale_close = "}"
        elif isinstance(fig_scale, str) and fig_scale.strip():
            fig_scale_open = fig_scale
            fig_scale_close = ""

    sub_spans = _normalize_submatrix_locs(submatrix_locs)

    if outer_delims and not sub_spans:
        if outer_delims_span is None:
            outer_delims_span = _guess_shape_from_mat_rep(mat_rep_norm)
        nrows, ncols = outer_delims_span
        if nrows <= 0 or ncols <= 0:
            raise ValueError("Could not infer outer_delims_span; pass outer_delims_span=(nrows,ncols).")
        sub_spans.append((f"name={outer_delims_name}", f"{{1-1}}{{{nrows}-{ncols}}}"))

    # Descriptor-based callouts (rendered to TikZ draw commands).
    # We validate against the set of SubMatrix names declared in sub_spans.
    rendered_callouts: List[str] = []
    if matrix_labels is not None:
        callouts = _merge_callouts(callouts, matrix_labels)
    if callouts:
        try:
            import re

            def _extract_names(spans: Sequence[Tuple[Any, ...]]) -> List[str]:
                """Extract declared SubMatrix names from normalized spans.

                ``_normalize_submatrix_locs`` can return tuples of length 2
                ``(opts, span)`` or length 4 ``(opts, span, left, right)``.
                We only care about the ``opts`` field.
                """
                names: List[str] = []
                for item in spans:
                    if not item:
                        continue
                    opts = item[0]
                    if not opts:
                        continue
                    m = re.search(r"(?:^|,)\s*name\s*=\s*([A-Za-z0-9_]+)", str(opts))
                    if m:
                        names.append(m.group(1))
                return names

            from .nicematrix_decor import render_delim_callouts

            rendered_callouts = render_delim_callouts(
                callouts,
                available_names=_extract_names(sub_spans),
                name_map=callout_name_map,
                strict=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to render callouts: {e}") from e

    ctx = dict(
        extension=extension or "",
        preamble=preamble or "",
        fig_scale_open=fig_scale_open,
        fig_scale_close=fig_scale_close,
        landscape=bool(landscape),
        nice_options=(nice_options or "").strip(),
        mat_format=mat_format_norm,
        create_cell_nodes=bool(create_cell_nodes),
        create_extra_nodes=bool(create_extra_nodes),
        create_medium_nodes=bool(create_medium_nodes),
        codebefore=list(codebefore or []),
        mat_rep=mat_rep_norm,
        submatrix_spans=sub_spans,   # list[(opts, "{i-j}{k-l}")]
        submatrix_names=list(submatrix_names or []),
        pivot_locs=_normalize_pivot_locs(pivot_locs),
        txt_with_locs=_normalize_txt_with_locs(txt_with_locs),
        rowechelon_paths=list(rowechelon_paths or []) + rendered_callouts,
    )
    return render_template("ge.tex.j2", ctx)


def ge_svg(
    *,
    mat_rep: str,
    mat_format: str,
    preamble: str = "",
    extension: str = "",
    nice_options: Optional[str] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    codebefore: Optional[Sequence[str]] = None,
    submatrix_locs: Optional[Sequence[Any]] = None,
    submatrix_names: Optional[Sequence[str]] = None,
    pivot_locs: Optional[Sequence[Any]] = None,
    txt_with_locs: Optional[Sequence[Any]] = None,
    rowechelon_paths: Optional[Sequence[Any]] = None,
    callouts: Optional[Sequence[Any]] = None,
    matrix_labels: Optional[Sequence[Any]] = None,
    fig_scale: Optional[Union[float, int, str]] = None,
    landscape: Optional[bool] = None,
    create_cell_nodes: Optional[bool] = None,
    create_extra_nodes: Optional[bool] = None,
    create_medium_nodes: Optional[bool] = None,
    outer_delims: Optional[bool] = None,
    outer_delims_name: Optional[str] = None,
    outer_delims_span: Optional[Tuple[int, int]] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
    output_dir: Optional[Union[str, "os.PathLike[str]"]] = None,
    output_stem: str = "output",
) -> str:
    """Render the GE template to SVG (strict rendering boundary)."""
    tex = ge_tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        preamble=preamble,
        extension=extension,
        nice_options=nice_options,
        layout=layout,
        codebefore=codebefore,
        submatrix_locs=submatrix_locs,
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
        rowechelon_paths=rowechelon_paths,
        callouts=callouts,
        matrix_labels=matrix_labels,
        fig_scale=fig_scale,
        landscape=landscape,
        create_cell_nodes=create_cell_nodes,
        create_extra_nodes=create_extra_nodes,
        create_medium_nodes=create_medium_nodes,
        outer_delims=outer_delims,
        outer_delims_name=outer_delims_name,
        outer_delims_span=outer_delims_span,
    )
    if toolchain_name:
        return _render_svg(
            tex,
            toolchain_name=toolchain_name,
            crop=crop,
            padding=padding,
            output_dir=output_dir,
            output_stem=output_stem,
        )
    return _render_svg(tex, crop=crop, padding=padding, output_dir=output_dir, output_stem=output_stem)


# -----------------------------------------------------------------------------
# Grid helpers: build GE mat_rep/mat_format from a "matrix-of-matrices" stack.
# -----------------------------------------------------------------------------


def _as_2d_list(M: Any) -> Tuple[List[List[Any]], int, int]:
    """Return (rows, nrows, ncols) from common matrix-like inputs."""
    if M is None:
        return [], 0, 0

    # SymPy / numpy / etc.
    if hasattr(M, 'tolist'):
        rows = M.tolist()
    elif isinstance(M, (list, tuple)):
        rows = list(M)
    else:
        try:
            rows = list(M)
        except Exception as e:
            raise TypeError(f"Unsupported matrix-like object: {type(M)!r}") from e

    rows2: List[List[Any]] = []
    for r in rows:
        if isinstance(r, (list, tuple)):
            rows2.append(list(r))
        else:
            # 1D vector treated as a column
            rows2.append([r])

    nrows = len(rows2)
    ncols = max((len(r) for r in rows2), default=0)

    # Pad ragged rows with blanks.
    for r in rows2:
        if len(r) < ncols:
            r.extend([""] * (ncols - len(r)))

    return rows2, nrows, ncols


def _matrix_body_tex(M: Any, *, formater: LatexFormatter) -> str:
    """Format a matrix-like object into a TeX body: ``a & b \\ c & d``."""
    rows, nrows, ncols = _as_2d_list(M)
    if nrows == 0 or ncols == 0:
        return ""

    body_rows: List[str] = []
    for r in rows:
        cells = [formater(v) for v in r]
        body_rows.append(" & ".join(cells) + r" \\")
    return "\n".join(body_rows)


def _pnicearray_tex(
    M: Any,
    *,
    Nrhs: int = 0,
    formater: LatexFormatter,
    align: str = "r",
) -> str:
    """Wrap a matrix body into a ``pNiceArray`` environment."""
    rows, nrows, ncols = _as_2d_list(M)
    if nrows == 0 or ncols == 0:
        # Use nicematrix's semantic marker for "this cell is not empty" so that
        # `create-cell-nodes` reliably creates nodes without introducing spacing.
        return r"\NotEmpty"

    # Column format, optionally with an augmented separator.
    if Nrhs and 0 < Nrhs < ncols:
        left = ncols - Nrhs
        fmt = (align * left) + "|" + (align * Nrhs)
    else:
        fmt = align * ncols

    body = _matrix_body_tex(rows, formater=formater)
    # IMPORTANT: emit real newlines, not a literal "\\n" TeX control sequence.
    return f"\\begin{{pNiceArray}}{{{fmt}}}%\n{body}\n\\end{{pNiceArray}}"


def ge_grid_tex(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    Nrhs: Any = 0,
    formater: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    extension: str = "",
    fig_scale: Optional[Union[float, int, str]] = None,
    *,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    **kwargs: Any,
) -> str:
    r"""Populate the GE template from a matrix stack.

    IMPORTANT
    ---------
    ``nicematrix`` environments cannot be nested. Therefore this helper must
    *not* place ``pNiceArray`` environments inside an outer ``NiceArray``.
    Instead, this routine *flattens* a "grid of matrices" into a single
    scalar ``NiceArray`` and then uses ``\SubMatrix`` to draw per-block
    delimiters (parentheses) around each matrix block.

    Parameters
    ----------
    matrices:
        A nested list representing the "matrix-of-matrices" layout, typically
        ``[[None, A0], [E1, A1], [E2, A2], ...]``.
    Nrhs:
        Number of RHS columns in the *A-block* matrices, or a list of RHS block
        widths (legacy partition style). This is used to insert an
        augmented-matrix partition bar in the last block-column's preamble.
    formater:
        Scalar formatter for TeX.
    outer_hspace_mm:
        Horizontal spacing between adjacent matrix blocks.

    Returns
    -------
    str
        TeX document (via :func:`ge_tex`).
    """
    grid_spec = _coerce_grid_spec(spec)
    if grid_spec is not None:
        if matrices is None:
            matrices = grid_spec.matrices
        else:
            matrices = grid_spec.matrices
        Nrhs = grid_spec.Nrhs
        if grid_spec.formater is not None:
            formater = grid_spec.formater
        outer_hspace_mm = int(grid_spec.outer_hspace_mm)
        cell_align = str(grid_spec.cell_align)
        extension = str(grid_spec.extension or extension)
        fig_scale = grid_spec.fig_scale if grid_spec.fig_scale is not None else fig_scale
        if grid_spec.layout is not None:
            kwargs["layout"] = grid_spec.layout
        kwargs["legacy_submatrix_names"] = bool(grid_spec.legacy_submatrix_names)
        kwargs["legacy_format"] = bool(grid_spec.legacy_format)

    grid: List[List[Any]] = [list(r) for r in (matrices or [])]
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    # Normalize ragged outer rows.
    for r in range(n_block_rows):
        if len(grid[r]) < n_block_cols:
            grid[r].extend([None] * (n_block_cols - len(grid[r])))

    # Determine per-block-row height and per-block-column width.
    block_heights: List[int] = [0] * n_block_rows
    block_widths: List[int] = [0] * n_block_cols
    cell_cache: List[List[Tuple[List[List[Any]], int, int]]] = [
        [([], 0, 0) for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]

    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows, h, w = _as_2d_list(grid[br][bc])
            cell_cache[br][bc] = (rows, h, w)
            block_heights[br] = max(block_heights[br], h)
            block_widths[bc] = max(block_widths[bc], w)

    # Heuristic: if a whole block-column is "missing" (e.g. the E-block is None
    # in the first layer), infer a square size from the tallest block-row.
    max_h = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_h > 0:
            block_widths[bc] = max_h

    if any(w <= 0 for w in block_widths) or any(h <= 0 for h in block_heights):
        raise ValueError("Could not infer matrix block sizes from `matrices`.")

    legacy_format = bool(kwargs.pop("legacy_format", False))

    # Build a single NiceArray format string.
    fmt_parts: List[str] = []
    spacer = rf"@{{\hspace{{{int(outer_hspace_mm)}mm}}}}"
    if legacy_format:
        fmt_parts.append(spacer)

    sep = "I" if legacy_format else "|"
    for bc, w in enumerate(block_widths):
        if bc > 0:
            fmt_parts.append(spacer)

        # Apply Nrhs only to the last block-column (A-block in the legacy layout).
        if Nrhs and bc == n_block_cols - 1:
            if isinstance(Nrhs, (list, tuple)):
                rhs = [int(x) for x in Nrhs]
                left = w - sum(rhs)
                cuts: List[int] = [left]
                for cut in rhs[:-1]:
                    cuts.append(cuts[-1] + cut)
                cur = 0
                fmt = ""
                for cut in cuts:
                    fmt += (cell_align * (cut - cur)) + sep
                    cur = cut
                if cur < w:
                    fmt += cell_align * (w - cur)
                fmt_parts.append(fmt)
            elif 0 < int(Nrhs) < w:
                left = w - int(Nrhs)
                fmt_parts.append((cell_align * left) + sep + (cell_align * int(Nrhs)))
            else:
                fmt_parts.append(cell_align * w)
        else:
            fmt_parts.append(cell_align * w)

    mat_format = "".join(fmt_parts)

    # Use nicematrix's semantic marker for "this cell is not empty" so that
    # `create-cell-nodes` reliably creates nodes without introducing spacing.
    blank = r"\NotEmpty"

    def _fmt(v: Any) -> str:
        if v is None:
            return blank
        s = formater(v)
        return s if (isinstance(s, str) and s.strip()) else blank

    # Flatten all blocks into one scalar matrix representation.
    lines: List[str] = []
    for br in range(n_block_rows):
        H = block_heights[br]
        for i in range(H):
            row_cells: List[str] = []
            for bc in range(n_block_cols):
                W = block_widths[bc]
                rows, h, w = cell_cache[br][bc]
                if h == 0 or w == 0:
                    row_cells.extend([blank] * W)
                    continue

                # Pad to the inferred block dimensions.
                if i < len(rows):
                    src = list(rows[i])
                else:
                    src = []
                if len(src) < W:
                    src.extend([None] * (W - len(src)))
                row_cells.extend([_fmt(v) for v in src[:W]])
            lines.append(" & ".join(row_cells) + r" \\")

    mat_rep = "\n".join(lines)

    # Emit \SubMatrix spans for each non-empty block to draw parentheses.
    # Merge with any user-provided spans passed via **kwargs.
    user_sub = kwargs.pop("submatrix_locs", None)
    submatrix_locs: List[Tuple[str, str, str]] = []
    use_legacy_names = bool(kwargs.pop("legacy_submatrix_names", False))

    # Precompute offsets (1-based nicematrix coordinates).
    row_starts: List[int] = []
    acc = 1
    for H in block_heights:
        row_starts.append(acc)
        acc += H
    col_starts: List[int] = []
    acc = 1
    for W in block_widths:
        col_starts.append(acc)
        acc += W

    name_map: Dict[Tuple[int, int], str] = {}
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, h, w = cell_cache[br][bc]
            if h == 0 or w == 0:
                continue
            r0 = row_starts[br]
            c0 = col_starts[bc]
            r1 = r0 + block_heights[br] - 1
            c1 = c0 + block_widths[bc] - 1
            # Name matrices by their column role when in the legacy 2-column layout.
            if use_legacy_names:
                base = "A"
                name = f"{base}{br}x{bc}"
            else:
                if n_block_cols == 2:
                    base = ("E" if bc == 0 else "A")
                else:
                    base = f"M{bc}"
                name = f"{base}{br}"
            # Use \SubMatrix to draw the per-block delimiters.
            # IMPORTANT: do *not* force explicit delimiter overrides via
            # _{(}^{)} here. Nicematrix already draws parentheses for SubMatrix
            # blocks by default, and adding explicit overrides re-introduces the
            # "spurious extra delimiters" artifact (and breaks tests that
            # assert the canonical \SubMatrix(...) [name=...] syntax).
            opts = f"name={name}"
            submatrix_locs.append((opts, f"{r0}-{c0}", f"{r1}-{c1}"))
            name_map[(br, bc)] = name

    if user_sub:
        submatrix_locs.extend(list(user_sub))

    return ge_tex(
        mat_rep=mat_rep,
        mat_format=mat_format,
        extension=extension,
        fig_scale=fig_scale,
        submatrix_locs=submatrix_locs,
        callouts=kwargs.pop("callouts", None),
        matrix_labels=kwargs.pop("matrix_labels", None),
        callout_name_map=name_map,
        **kwargs,
    )


def ge_grid_submatrix_spans(
    matrices: Sequence[Sequence[Any]],
    *,
    Nrhs: int = 0,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    legacy_submatrix_names: bool = False,
) -> List[SubMatrixSpan]:
    """Return the resolved ``\\SubMatrix`` spans for a GE matrix grid.

    This helper exposes the same naming and inferred-block-dimension logic used
    by :func:`ge_grid_tex`, but returns structured metadata rather than a TeX
    document. It exists primarily to support notebook workflows that want to
    attach TikZ paths to delimiter nodes without regex-parsing the generated TeX.

    Notes
    -----
    * Coordinates are 1-based nicematrix coordinates.
    * Blocks that are ``None`` (or empty) are omitted.
    * The first block-column width is inferred as square when it is entirely
      missing (common for the top E-block in the legacy 2-column layout).
    """

    # Keep this logic intentionally aligned with ge_grid_tex.
    grid: List[List[Any]] = [list(r) for r in (matrices or [])]
    if not grid:
        raise ValueError("matrices must be a non-empty nested list")

    n_block_rows = len(grid)
    n_block_cols = max((len(r) for r in grid), default=0)
    if n_block_cols == 0:
        raise ValueError("matrices must contain at least one column")

    for r in range(n_block_rows):
        if len(grid[r]) < n_block_cols:
            grid[r].extend([None] * (n_block_cols - len(grid[r])))

    block_heights: List[int] = [0] * n_block_rows
    block_widths: List[int] = [0] * n_block_cols
    cell_cache: List[List[Tuple[List[List[Any]], int, int]]] = [
        [([], 0, 0) for _ in range(n_block_cols)] for _ in range(n_block_rows)
    ]

    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            rows, h, w = _as_2d_list(grid[br][bc])
            cell_cache[br][bc] = (rows, h, w)
            block_heights[br] = max(block_heights[br], h)
            block_widths[bc] = max(block_widths[bc], w)

    max_h = max(block_heights) if block_heights else 0
    for bc in range(n_block_cols):
        if block_widths[bc] == 0 and max_h > 0:
            block_widths[bc] = max_h

    if any(w <= 0 for w in block_widths) or any(h <= 0 for h in block_heights):
        raise ValueError("Could not infer matrix block sizes from `matrices`.")

    # Build a single NiceArray format string so we keep the same inferred widths
    # as ge_grid_tex (including Nrhs behavior). We don't return it here, but the
    # computation is intentionally mirrored.
    _ = (Nrhs, outer_hspace_mm, cell_align)  # for signature parity / future use

    row_starts: List[int] = []
    acc = 1
    for H in block_heights:
        row_starts.append(acc)
        acc += H

    col_starts: List[int] = []
    acc = 1
    for W in block_widths:
        col_starts.append(acc)
        acc += W

    spans: List[SubMatrixSpan] = []
    for br in range(n_block_rows):
        for bc in range(n_block_cols):
            _, h, w = cell_cache[br][bc]
            if h == 0 or w == 0:
                continue

            r0 = row_starts[br]
            c0 = col_starts[bc]
            r1 = r0 + block_heights[br] - 1
            c1 = c0 + block_widths[bc] - 1

            if legacy_submatrix_names:
                name = f"A{br}x{bc}"
            else:
                if n_block_cols == 2:
                    base = ("E" if bc == 0 else "A")
                else:
                    base = f"M{bc}"
                name = f"{base}{br}"

            spans.append(
                SubMatrixSpan(
                    name=name,
                    row_start=r0,
                    col_start=c0,
                    row_end=r1,
                    col_end=c1,
                    block_row=br,
                    block_col=bc,
                )
            )

    return spans


def ge_grid_bundle(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    *,
    Nrhs: int = 0,
    formater: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    extension: str = "",
    fig_scale: Optional[Union[float, int, str]] = None,
    layout: Optional[Union[Dict[str, Any], GELayoutSpec]] = None,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    **kwargs: Any,
) -> GEGridBundle:
    """Return both the GE-grid TeX and the resolved ``\\SubMatrix`` spans.

    This is a notebook-oriented convenience wrapper around :func:`ge_grid_tex`
    and :func:`ge_grid_submatrix_spans`.

    Unlike :func:`ge_grid_tex`, this function returns structured metadata so
    callers can attach TikZ paths/callouts to known delimiter nodes without
    regex-parsing the generated TeX.
    """

    tex = ge_grid_tex(
        matrices=matrices,
        Nrhs=Nrhs,
        formater=formater,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        extension=extension,
        fig_scale=fig_scale,
        layout=layout,
        spec=spec,
        **kwargs,
    )
    use_spec = _coerce_grid_spec(spec)
    if use_spec is not None:
        matrices = use_spec.matrices
        Nrhs = use_spec.Nrhs
        outer_hspace_mm = int(use_spec.outer_hspace_mm)
        cell_align = str(use_spec.cell_align)
        legacy_submatrix_names = bool(use_spec.legacy_submatrix_names)
    else:
        legacy_submatrix_names = bool(kwargs.get("legacy_submatrix_names", False))
    spans = ge_grid_submatrix_spans(
        matrices,
        Nrhs=Nrhs,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        legacy_submatrix_names=legacy_submatrix_names,
    )
    return GEGridBundle(tex=tex, submatrix_spans=spans)


def ge_grid_svg(
    matrices: Optional[Sequence[Sequence[Any]]] = None,
    Nrhs: int = 0,
    formater: LatexFormatter = latexify,
    outer_hspace_mm: int = 6,
    cell_align: str = "r",
    extension: str = "",
    fig_scale: Optional[Union[float, int, str]] = None,
    toolchain_name: Optional[str] = None,
    crop: Optional[str] = None,
    padding: Any = None,
    output_dir: Optional[Union[str, "os.PathLike[str]"]] = None,
    output_stem: str = "output",
    frame: Any = None,
    *,
    spec: Optional[Union[GEGridSpec, Dict[str, Any]]] = None,
    **kwargs: Any,
) -> str:
    r"""Render the GE matrix stack to SVG.

    This is a convenience wrapper around :func:`ge_grid_tex` and the strict
    rendering boundary (:func:`matrixlayout.render.render_svg`).

    Parameters
    ----------
    matrices, Nrhs, formater, outer_hspace_mm, cell_align:
        See :func:`ge_grid_tex`.
    toolchain_name, crop, padding:
        Passed through to the renderer.

    Returns
    -------
    str
        SVG text.
    """
    tex = ge_grid_tex(
        matrices=matrices,
        Nrhs=Nrhs,
        formater=formater,
        outer_hspace_mm=outer_hspace_mm,
        cell_align=cell_align,
        extension=extension,
        fig_scale=fig_scale,
        spec=spec,
        **kwargs,
    )
    return _render_svg(
        tex,
        toolchain_name=toolchain_name,
        crop=crop,
        padding=padding,
        frame=frame,
        output_dir=output_dir,
        output_stem=output_stem,
    )
