from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

import jinja2


@dataclass(frozen=True)
class JinjaConfig:
    '''
    Configuration for the Jinja2 environment used by matrixlayout.

    This matches the legacy nicematrix.py template conventions:
      - blocks:   {%% ... %%}
      - comments: {## ... ##}
      - variables remain default: {{ ... }}

    Notes:
      - matrixlayout should not enable autoescape for TeX/TikZ sources.
      - strict_undefined can be enabled in tests to fail fast on missing context keys.
    '''
    template_dirs: Optional[Sequence[Union[str, Path]]] = None
    strict_undefined: bool = False


def _make_loader(template_dirs: Optional[Sequence[Union[str, Path]]]) -> jinja2.BaseLoader:
    """Construct a Jinja2 template loader.

    If explicit ``template_dirs`` are provided, load templates from the
    filesystem; otherwise, load package templates from ``matrixlayout/templates``.
    """
    if template_dirs:
        dirs = [str(Path(p)) for p in template_dirs]
        return jinja2.FileSystemLoader(dirs)
    # Prefer PackageLoader for installed distributions.
    #
    # In some dev/interop setups (editable installs, PYTHONPATH hacks, Julia bridges),
    # Jinja's PackageLoader can fail to locate package data even when templates are
    # present on disk. Fall back to a FileSystemLoader rooted at the on-disk
    # `templates/` directory next to this module.
    try:
        return jinja2.PackageLoader("matrixlayout", "templates")
    except Exception:
        fallback = Path(__file__).resolve().parent / "templates"
        if fallback.is_dir():
            return jinja2.FileSystemLoader(str(fallback))
        raise


def make_environment(config: Optional[JinjaConfig] = None) -> jinja2.Environment:
    '''
    Create a new Jinja2 Environment using matrixlayout's legacy-compatible settings.

    Prefer get_environment() unless you need a custom template_dirs.
    '''
    config = config or JinjaConfig()
    undefined_cls = jinja2.StrictUndefined if config.strict_undefined else jinja2.Undefined

    env = jinja2.Environment(
        loader=_make_loader(config.template_dirs),
        undefined=undefined_cls,
        autoescape=False,
        # Keep whitespace behavior close to legacy: rely on explicit '-%%' trimming in templates.
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
        block_start_string="{%%",
        block_end_string="%%}",
        comment_start_string="{##",
        comment_end_string="##}",
        # variable_start_string and variable_end_string remain defaults: {{ }}
    )
    return env


@lru_cache(maxsize=4)
def get_environment(*, strict_undefined: bool = False) -> jinja2.Environment:
    '''
    Get a cached default environment (PackageLoader-based).

    Use strict_undefined=True in tests when you want missing keys to raise immediately.
    '''
    return make_environment(JinjaConfig(template_dirs=None, strict_undefined=strict_undefined))


def render_template(
    template_name: str,
    context: Mapping[str, Any],
    *,
    env: Optional[jinja2.Environment] = None,
) -> str:
    '''
    Render a template by name using the configured environment.

    template_name is relative to matrixlayout/templates/ when using the default environment.
    '''
    env = env or get_environment()
    tmpl = env.get_template(template_name)
    return tmpl.render(**dict(context))


def render_string(
    template_source: str,
    context: Mapping[str, Any],
    *,
    env: Optional[jinja2.Environment] = None,
) -> str:
    '''
    Render a template from an in-memory source string.
    Useful during migration when templates are still embedded as Python strings.
    '''
    env = env or get_environment()
    tmpl = env.from_string(template_source)
    return tmpl.render(**dict(context))
