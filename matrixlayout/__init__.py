"""matrixlayout: matrix-based layout and presentation library.

This snapshot contains the shared Jinja2 template environment used during migration
from nicematrix.py templates.
"""

from .jinja_env import (
    JinjaConfig,
    get_environment,
    make_environment,
    render_template,
    render_string,
)

from .backsubst import backsubst_svg, backsubst_tex
from .render import render_svg
from .shortcascade import BackSubTrace, BackSubStep, mk_shortcascade_lines

__all__ = [
    "JinjaConfig",
    "get_environment",
    "make_environment",
    "render_template",
    "render_string",
    "render_svg",
    "backsubst_tex",
    "backsubst_svg",
    "BackSubTrace",
    "BackSubStep",
    "mk_shortcascade_lines",
]
