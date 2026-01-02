"""Gaussian-elimination style matrix grid layout template.

This module migrates ``GE_TEMPLATE`` from the legacy ``itikz.nicematrix`` implementation.

The template is treated as a layout/presentation artifact only:

- The caller provides a fully formatted NiceArray body (``mat_rep``) and any
  associated annotation descriptors (submatrix delimiters, pivot outlines,
  explanatory text, and optional row-echolon paths).
- matrixlayout generates TeX and (optionally) renders SVG via the strict
  :func:`jupyter_tikz.render_svg` rendering boundary.

Algorithmic decisions (pivoting, elimination steps, matrix decomposition, etc.)
must live outside of matrixlayout (e.g., in ``la_figures``).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from .jinja_env import render_template
from .render import render_svg


def _ensure_braced_format(fmt: str) -> str:
    """Ensure a NiceArray format argument is wrapped in braces.

    The legacy template expects ``mat_format`` to include the braces
    (e.g., ``"{cc}"``). For convenience, matrixlayout accepts either
    ``"cc"`` or ``"{cc}"`` and normalizes here.
    """
    s = fmt.strip()
    if s.startswith('{') and s.endswith('}'):
        return s
    return '{' + s + '}'


def _as_scale(value: Optional[Union[str, float, int]]) -> Optional[str]:
    """Normalize ``fig_scale`` to the legacy TeX wrapper (or None).

    - ``None``: no scaling wrapper
    - numeric: converted to ``\\scalebox{<value>}{%`` (template closes the brace)
    - string: inserted verbatim (caller may provide a custom wrapper)
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return r'\\scalebox{' + format(value, 'g') + r'}{%'


_SINGLE_BS_WS_RE = re.compile(r"(?<!\\)\\(\s)")


def _normalize_mat_rep(mat_rep: str) -> str:
    """Normalize a NiceArray body string for TeX.

    A common Python-string pitfall is writing a TeX row separator as ``"\\"``
    (two characters in source) which evaluates to a *single* backslash in the
    runtime string, followed by whitespace. In TeX, a row separator must be
    ``\\``.

    This helper converts *single* backslashes followed by whitespace into
    double backslashes, leaving correct ``\\`` sequences unchanged.
    """

    return _SINGLE_BS_WS_RE.sub(r"\\\\\1", mat_rep)



_SUBMATRIX_PARENS_RE = re.compile(r"^\(?(.*?)\)?$")

_SUBMATRIX_COORDS_RE = re.compile(r"\(\s*([^)]+?)\s*\)")

def _strip_parens(token: str) -> str:
    """Strip a single pair of outer parentheses from a coordinate token.

    Examples
    --------
    - "(1-1)" -> "1-1"
    - "1-1"   -> "1-1"

    This is used to normalize legacy inputs for nicematrix coordinates.
    """
    token = token.strip()
    if token.startswith("(") and token.endswith(")"):
        return token[1:-1].strip()
    return token


def _normalize_submatrix_locs(
    locs: Sequence[object],
) -> Sequence[Tuple[str, str, str]]:
    r"""Normalize submatrix location descriptors to (options, first, last) triples.

    The legacy code frequently represented a submatrix as a pair:
        (options, "(1-1)(2-2)")

    Nicematrix expects:
        \SubMatrix[<options>](<first>)(<last>)

    This helper accepts several convenient input shapes and emits a uniform
    representation consumed by the Jinja2 template.
    """
    out: list[Tuple[str, str, str]] = []
    for loc in locs:
        if isinstance(loc, dict):
            opts = str(loc.get("options") or loc.get("style") or "")
            first = _strip_parens(str(loc.get("first", "")))
            last = _strip_parens(str(loc.get("last", "")))
            if not (first and last):
                raise ValueError(f"Invalid submatrix loc dict: {loc!r}")
            out.append((opts, first, last))
            continue

        if not isinstance(loc, (tuple, list)):
            raise TypeError(f"Submatrix loc must be tuple/list/dict, got {type(loc)}")

        if len(loc) == 2:
            opts, coords = loc
            opts = str(opts)
            if isinstance(coords, (tuple, list)) and len(coords) == 2:
                first, last = coords
                out.append((opts, _strip_parens(str(first)), _strip_parens(str(last))))
                continue
            coords_s = str(coords)
            parts = _SUBMATRIX_COORDS_RE.findall(coords_s)
            if len(parts) == 2:
                out.append((opts, _strip_parens(parts[0]), _strip_parens(parts[1])))
                continue
            # Fallback: attempt to split on ")(" pattern without outer parens
            if ")(" in coords_s:
                a, b = coords_s.split(")(", 1)
                out.append((opts, _strip_parens(a + ")"), _strip_parens("(" + b)))
                continue
            raise ValueError(f"Unrecognized submatrix coords: {coords!r}")

        if len(loc) == 3:
            opts, first, last = loc
            out.append((str(opts), _strip_parens(str(first)), _strip_parens(str(last))))
            continue

        raise ValueError(f"Submatrix loc must have length 2 or 3, got {loc!r}")

    return tuple(out)


@dataclass(frozen=True)
class GEContext:
    """Context object for the ``ge.tex.j2`` template.

    All fields are presentation-layer inputs. In particular, ``mat_rep`` is
    the already-formatted body of the NiceArray (rows, columns, and entries),
    not a numeric matrix.
    """

    # LaTeX inserted before the NiceArray (after the document wrapper).
    preamble: str = ""
    # Optional raw TeX inserted where legacy code injected `extension` hooks.
    extension: str = ""

    # NiceArray environment arguments.
    mat_format: str = ""
    mat_options: str = ""

    # NiceArray body.
    mat_rep: str = ""

    # Optional CodeBefore entries (strings inserted verbatim).
    codebefore: Sequence[str] = ()

    # Submatrix delimiter declarations.
    #
    # User input is accepted in a few legacy-compatible forms:
    # - (options, "(1-1)(2-2)")
    # - (options, "(1-1)", "(2-2)")
    # - {"options": "name=SM", "first": "1-1", "last": "2-2"}
    #
    # The template receives normalized triples: (options, first, last) where
    # ``first`` and ``last`` are coordinate tokens like "1-1" (no parens).
    submatrix_locs: Sequence[Tuple[str, str, str]] = ()
    # Extra TeX lines to label submatrices (inserted verbatim).
    submatrix_names: Sequence[str] = ()

    # Pivot outline locs: each entry is (fit_target, extra_style)
    # Used by: \node [draw,<extra_style>,fit=<fit_target>] {} ;
    pivot_locs: Sequence[Tuple[str, str]] = ()

    # Explanatory text nodes: (tikz_coordinate, text, color)
    txt_with_locs: Sequence[Tuple[str, str, str]] = ()

    # Optional tikz path fragments for a "row echelon form" outline or other paths.
    rowechelon_paths: Sequence[str] = ()

    # Optional scale wrapper used by the template.
    fig_scale: Optional[str] = None

    # Whether to wrap the figure in a landscape environment. This is a purely
    # presentation-level option; disabled by default to avoid requiring the
    # ``pdflscape`` package in minimal TeX installations.
    landscape: bool = False

    def as_dict(self) -> Mapping[str, Any]:
        """Return a dict matching the template variable names."""
        return {
            "preamble": self.preamble,
            "extension": self.extension,
            "mat_format": self.mat_format,
            "mat_options": self.mat_options,
            "mat_rep": self.mat_rep,
            "codebefore": list(self.codebefore),
            "submatrix_locs": list(self.submatrix_locs),
            "submatrix_names": list(self.submatrix_names),
            "pivot_locs": list(self.pivot_locs),
            "txt_with_locs": list(self.txt_with_locs),
            "rowechelon_paths": list(self.rowechelon_paths),
            "fig_scale": self.fig_scale,
            "landscape": self.landscape,
        }


def ge_tex(
    *,
    mat_rep: str,
    mat_format: str,
    mat_options: str = "",
    preamble: str = "",
    extension: str = "",
    codebefore: Sequence[str] = (),
    submatrix_locs: Sequence[Tuple[str, str]] = (),
    submatrix_names: Sequence[str] = (),
    pivot_locs: Sequence[Tuple[str, str]] = (),
    txt_with_locs: Sequence[Tuple[str, str, str]] = (),
    rowechelon_paths: Sequence[str] = (),
    fig_scale: Optional[Union[str, float, int]] = None,
    landscape: bool = False,
) -> str:
    """Render the GE document template to TeX.

    Parameters are passed through to the underlying template with minimal
    processing. ``fig_scale`` may be a numeric factor or raw TeX wrapper.
    """
    ctx = GEContext(
        preamble=preamble,
        extension=extension,
        mat_format=_ensure_braced_format(mat_format),
        mat_options=mat_options,
        mat_rep=_normalize_mat_rep(mat_rep),
        codebefore=codebefore,
        submatrix_locs=_normalize_submatrix_locs(submatrix_locs),
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
        rowechelon_paths=rowechelon_paths,
        fig_scale=_as_scale(fig_scale),
        landscape=landscape,
    )
    return render_template("ge.tex.j2", ctx.as_dict())


def ge_svg(
    *,
    mat_rep: str,
    mat_format: str,
    mat_options: str = "",
    preamble: str = "",
    extension: str = "",
    codebefore: Sequence[str] = (),
    submatrix_locs: Sequence[Tuple[str, str]] = (),
    submatrix_names: Sequence[str] = (),
    pivot_locs: Sequence[Tuple[str, str]] = (),
    txt_with_locs: Sequence[Tuple[str, str, str]] = (),
    rowechelon_paths: Sequence[str] = (),
    fig_scale: Optional[Union[str, float, int]] = None,
    landscape: bool = False,
    toolchain_name: Optional[str] = None,
) -> str:
    """Render the GE document template to SVG using jupyter_tikz."""
    tex = ge_tex(
        mat_rep=mat_rep,
        mat_format=_ensure_braced_format(mat_format),
        mat_options=mat_options,
        preamble=preamble,
        extension=extension,
        codebefore=codebefore,
        submatrix_locs=_normalize_submatrix_locs(submatrix_locs),
        submatrix_names=submatrix_names,
        pivot_locs=pivot_locs,
        txt_with_locs=txt_with_locs,
        rowechelon_paths=rowechelon_paths,
        fig_scale=fig_scale,
        landscape=landscape,
    )
    return render_svg(tex, toolchain_name=toolchain_name)
