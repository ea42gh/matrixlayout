import re
from pathlib import Path

import matrixlayout


def _pyproject_has_dynamic_version() -> bool:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    return bool(re.search(r'(?m)^dynamic\s*=\s*\[\s*"version"\s*\]\s*$', text))


def _pyproject_has_static_project_version() -> bool:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    project_match = re.search(r"(?ms)^\[project\]\s*(.*?)(?:^\[|\Z)", text)
    if project_match is None:
        raise AssertionError("pyproject.toml does not define a [project] table")
    return bool(re.search(r'(?m)^version\s*=\s*"[^"]+"\s*$', project_match.group(1)))


def test_pyproject_uses_dynamic_version_metadata():
    assert _pyproject_has_dynamic_version()
    assert not _pyproject_has_static_project_version()


def test_package_version_is_nonempty():
    assert matrixlayout.__version__


def test_render_extra_requires_patched_jupyter_tikz():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"jupyter-tikz @ git+https://github.com/ea42gh/jupyter-tikz.git@47ca7ea' in text
    assert '"jupyter-tikz>=' not in text


def test_binder_uses_same_patched_jupyter_tikz_source():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    binder_requirements = Path("binder/requirements.txt").read_text(encoding="utf-8")

    source = "git+https://github.com/ea42gh/jupyter-tikz.git@47ca7ea885075871631852eda1433a695260490a"
    assert source in pyproject
    assert source in binder_requirements


def test_docs_warn_against_pypi_jupyter_tikz_renderer():
    readme = Path("README.md").read_text(encoding="utf-8")
    overview = Path("docs/overview.md").read_text(encoding="utf-8")

    assert "PyPI `jupyter-tikz`" in readme
    assert "`render_svg_with_artifacts` API" in readme
    assert "do not substitute PyPI `jupyter-tikz`" in overview


def test_coverage_gate_tracks_current_quality_level():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "fail_under = 90" in text
