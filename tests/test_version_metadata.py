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

    assert '"jupyter-tikz>=0.5.6"' in text


def test_coverage_gate_tracks_current_quality_level():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "fail_under = 90" in text
