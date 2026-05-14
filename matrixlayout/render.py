"""Rendering boundary for matrixlayout.

matrixlayout must not manage subprocesses, LaTeX toolchains, cropping, or SVG
normalization. All rendering must go through jupyter_tikz, and matrixlayout
must remain importable without a TeX toolchain installed.

Policy
------
- No subprocess calls in matrixlayout.
- Import jupyter_tikz lazily, inside rendering functions only.
- Use :func:`jupyter_tikz.render_svg_with_artifacts` as the single rendering
  boundary so failures always have inspectable artifacts.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import inspect
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from .formatting import norm_str

_PathLike = Union[str, os.PathLike, Path]

_SVG_HEADER_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*", flags=re.DOTALL)
_RENDER_OPTION_KEYS = frozenset(
    {
        "toolchain_name",
        "output_stem",
        "crop",
        "padding",
        "frame",
        "exact_bbox",
        "output_dir",
    }
)


def _strip_svg_header_comment(svg_text: str) -> str:
    """Remove leading XML comments (e.g., dvisvgm generator headers)."""
    if not svg_text:
        return svg_text
    return _SVG_HEADER_COMMENT_RE.sub("", svg_text, count=1)


def _validate_toolchain_name(jupyter_tikz: Any, toolchain_name: Optional[str]) -> None:
    """Raise a clear error for unknown jupyter_tikz toolchain names."""
    if toolchain_name is None:
        return

    toolchains = getattr(jupyter_tikz, "TOOLCHAINS", None)
    if toolchains is None:
        return
    try:
        known = set(toolchains.keys())
    except AttributeError:
        return

    if toolchain_name not in known:
        available = ", ".join(sorted(str(name) for name in known))
        raise ValueError(
            f"Unknown jupyter_tikz toolchain: {toolchain_name!r}. "
            f"Available toolchains: {available}"
        )


def validate_render_opts(render_opts: Optional[Mapping[str, Any]]) -> None:
    """Raise a clear error for unsupported render option keys."""
    if render_opts is None:
        return
    if not isinstance(render_opts, Mapping):
        raise TypeError("render_opts must be a mapping of render option names to values")

    unknown = set(render_opts) - _RENDER_OPTION_KEYS
    if unknown:
        available = ", ".join(sorted(_RENDER_OPTION_KEYS))
        bad = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"Unknown render option(s): {bad}. Supported options: {available}")


def render_svg_with_artifacts(
    tex_source: str,
    *,
    output_dir: _PathLike,
    toolchain_name: Optional[str] = None,
    output_stem: str = "output",
    crop: Optional[str] = None,
    padding: Any = None,
    frame: Any = None,
    exact_bbox: bool = False,
):
    """Compile TeX and keep artifacts in ``output_dir``.

    This is a thin wrapper around :func:`jupyter_tikz.render_svg_with_artifacts`.
    The return type is intentionally un-annotated to avoid importing jupyter_tikz
    at module import time.
    """
    # Import lazily so unit tests that do not exercise rendering do not require
    # a full TeX toolchain to be installed.

    try:
        import jupyter_tikz
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "jupyter_tikz is required for SVG rendering. Install the optional dependency via: pip install 'matrixlayout[render]'"
        ) from e

    toolchain_name = norm_str(toolchain_name)
    crop = norm_str(crop)
    _validate_toolchain_name(jupyter_tikz, toolchain_name)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    if hasattr(jupyter_tikz, "render_svg_with_artifacts"):
        return jupyter_tikz.render_svg_with_artifacts(
            tex_source,
            output_dir=outdir,
            toolchain_name=toolchain_name,
            output_stem=output_stem,
            crop=crop,
            padding=padding,
            frame=frame,
            exact_bbox=exact_bbox,
        )

    if not hasattr(jupyter_tikz, "render_svg"):
        raise AttributeError(
            "jupyter_tikz must provide render_svg or render_svg_with_artifacts. "
            "Upgrade jupyter-tikz or install matrixlayout with the render extra."
        )

    render_svg = jupyter_tikz.render_svg
    kwargs = {
        "toolchain_name": toolchain_name,
        "output_stem": output_stem,
        "crop": crop,
        "padding": padding,
        "frame": frame,
        "exact_bbox": exact_bbox,
    }
    try:
        params = inspect.signature(render_svg).parameters
    except (TypeError, ValueError):
        params = {}
    accepts_var_kwargs = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if "output_dir" in params:
        kwargs["output_dir"] = outdir
    elif "artifacts_path" in params:
        kwargs["artifacts_path"] = outdir
    if params and not accepts_var_kwargs:
        kwargs = {key: value for key, value in kwargs.items() if key in params}

    svg_text = render_svg(tex_source, **kwargs)

    class _LegacyArtifacts:
        def read_svg(self) -> str:
            return str(svg_text)

    return _LegacyArtifacts()


def render_svg(
    tex_source: str,
    *,
    toolchain_name: Optional[str] = None,
    output_stem: str = "output",
    crop: Optional[str] = None,
    padding: Any = None,
    frame: Any = None,
    exact_bbox: bool = False,
    output_dir: Optional[_PathLike] = None,
) -> str:
    """Compile TeX and return SVG text.

    By default this function creates a temporary output directory and routes all
    work through :func:`render_svg_with_artifacts`. If compilation/conversion
    fails, the temporary directory is intentionally *not* deleted so callers can
    inspect the artifacts referenced by the raised exception.

    To force artifacts to be retained on success, set ``MATRIXLAYOUT_KEEP_ARTIFACTS=1``
    or pass an explicit ``output_dir``.
    """

    keep_on_success = os.environ.get("MATRIXLAYOUT_KEEP_ARTIFACTS") == "1"

    if output_dir is not None:
        # Treat output_dir as a root and always isolate artifacts per call to
        # avoid stale files from previous renders.
        out_root = Path(output_dir)
        out_root.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="matrixlayout_render_", dir=out_root))
        artifacts = render_svg_with_artifacts(
            tex_source,
            output_dir=tmp,
            toolchain_name=toolchain_name,
            output_stem=output_stem,
            crop=crop,
            padding=padding,
            frame=frame,
            exact_bbox=exact_bbox,
        )
        return _strip_svg_header_comment(artifacts.read_svg())

    # Default: isolate artifacts per-call, keep them on failure for diagnostics.
    tmp_root = Path(tempfile.gettempdir()) / "la"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="matrixlayout_render_", dir=tmp_root))
    try:
        artifacts = render_svg_with_artifacts(
            tex_source,
            output_dir=tmp,
            toolchain_name=toolchain_name,
            output_stem=output_stem,
            crop=crop,
            padding=padding,
            frame=frame,
            exact_bbox=exact_bbox,
        )
        svg_text = _strip_svg_header_comment(artifacts.read_svg())
    except Exception:
        # Keep tmp directory for inspection on failure.
        raise
    else:
        if not keep_on_success:
            shutil.rmtree(tmp, ignore_errors=True)
        return svg_text
