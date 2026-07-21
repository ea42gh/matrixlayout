from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import UndefinedError

from matrixlayout.jinja_env import JinjaConfig, get_environment, make_environment, render_string


def test_environment_uses_tex_safe_delimiters():
    env = get_environment()
    assert env.block_start_string == "{%%"
    assert env.block_end_string == "%%}"
    assert env.comment_start_string == "{##"
    assert env.comment_end_string == "##}"
    # Variables remain Jinja defaults
    assert env.variable_start_string == "{{"
    assert env.variable_end_string == "}}"


def test_render_string_supports_tex_safe_blocks_and_colon_syntax():
    # nicematrix.py templates commonly used a trailing ':' in for/if blocks.
    src = r'''
Hello
{%% for x in xs: %%}
- {{x}}
{%% endfor %%}
'''
    out = render_string(src, {"xs": [1, 2, 3]})
    assert "Hello" in out
    assert "- 1" in out and "- 2" in out and "- 3" in out


def test_filesystem_loader_works(tmp_path: Path):
    # Create a template file on disk and load via FileSystemLoader.
    (tmp_path / "t.tex.j2").write_text("A={%% if ok %%}Y{%% endif %%}", encoding="utf-8")
    env = make_environment(JinjaConfig(template_dirs=[tmp_path], strict_undefined=True))
    out = env.get_template("t.tex.j2").render(ok=True)
    assert out == "A=Y"
    with pytest.raises(UndefinedError):
        # strict undefined should raise for missing 'ok'
        env.get_template("t.tex.j2").render()
