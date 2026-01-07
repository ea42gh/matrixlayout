from __future__ import annotations

import os
import sys

import pytest
from pathlib import Path


def _ensure_monorepo_imports() -> None:
    """Ensure monorepo sibling packages are importable for integration tests.

    :mod:`matrixlayout` lazily imports :mod:`jupyter_tikz` at the strict
    rendering boundary. When running pytest from a checkout (without editable
    installs), we add the sibling package roots to ``sys.path`` so tests can
    exercise the integration layer.
    """

    # This file lives at matrixlayout/tests/...; the monorepo root is two levels up.
    repo_root = Path(__file__).resolve().parents[2]

    pkg_roots = [
        repo_root / "matrixlayout",
        repo_root / "jupyter_tikz",
    ]

    for p in reversed(pkg_roots):
        s = str(p)
        if s in sys.path:
            sys.path.remove(s)
        sys.path.insert(0, s)


_ensure_monorepo_imports()


# --- render test controls -------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--skip-render-tests",
        action="store_true",
        default=False,
        help="Skip tests marked with @pytest.mark.render",
    )


def pytest_collection_modifyitems(config, items):
    skip = config.getoption("--skip-render-tests") or os.environ.get("ITIKZ_SKIP_RENDER_TESTS") == "1"
    if not skip:
        return

    import pytest

    marker = pytest.mark.skip(reason="render tests skipped (set ITIKZ_SKIP_RENDER_TESTS=0 / omit --skip-render-tests)")
    for item in items:
        if 'render' in item.keywords:
            item.add_marker(marker)
