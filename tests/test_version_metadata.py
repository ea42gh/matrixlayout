import re
from pathlib import Path

import matrixlayout


def _pyproject_version() -> str:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
    if match is None:
        raise AssertionError("pyproject.toml does not define a project version")
    return match.group(1)


def test_package_version_matches_pyproject():
    assert matrixlayout.__version__ == _pyproject_version()
