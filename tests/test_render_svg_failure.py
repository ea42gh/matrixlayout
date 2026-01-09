from pathlib import Path

import pytest


def test_render_svg_keeps_temp_dir_on_failure(monkeypatch):
    from matrixlayout import render as ml_render

    kept: dict[str, Path] = {}

    def fake_render_svg_with_artifacts(tex_source, *, output_dir, **kwargs):
        kept["dir"] = Path(output_dir)
        raise RuntimeError("boom")

    monkeypatch.setattr(ml_render, "render_svg_with_artifacts", fake_render_svg_with_artifacts)

    with pytest.raises(RuntimeError):
        ml_render.render_svg(r"\\documentclass{standalone}\\begin{document}x\\end{document}")

    assert kept["dir"].exists()
