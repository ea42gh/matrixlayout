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

__all__ = [
    "JinjaConfig",
    "get_environment",
    "make_environment",
    "render_template",
    "render_string",
]
