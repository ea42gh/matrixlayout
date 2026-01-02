"""Rendering boundary for matrixlayout.

matrixlayout must not manage subprocesses, LaTeX toolchains, cropping, or SVG
normalization. All rendering must go through :func:`jupyter_tikz.render_svg`.

This module provides a thin wrapper so the rest of the package does not import
jupyter_tikz directly.
"""

from __future__ import annotations

from typing import Optional


def render_svg(tex_source: str, *, toolchain_name: Optional[str] = None) -> str:
    """Compile TeX and return SVG text.

    Parameters
    ----------
    tex_source:
        Full TeX source.
    toolchain_name:
        Optional jupyter_tikz toolchain name. If not provided, jupyter_tikz's
        default toolchain is used.
    """

    # Import lazily so unit tests that do not exercise rendering do not require
    # a full TeX toolchain to be installed.
    import jupyter_tikz

    if toolchain_name is None:
        return jupyter_tikz.render_svg(tex_source)

    return jupyter_tikz.render_svg(tex_source, toolchain_name=toolchain_name)
