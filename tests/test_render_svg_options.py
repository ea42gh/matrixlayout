import types
import sys
from pathlib import Path

import pytest

from matrixlayout import render as ml_render
import matrixlayout.backsubst as ml_backsubst


class _FakeArtifacts:
    def __init__(self, svg_text: str = "<svg/>"):
        self._svg_text = svg_text

    def read_svg(self) -> str:
        return self._svg_text


def test_matrixlayout_render_svg_uses_with_artifacts_and_forwards_options(monkeypatch, tmp_path):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg_with_artifacts(tex_source, **kwargs):
        calls.append((tex_source, kwargs))
        return _FakeArtifacts("<svg/>")

    fake.render_svg_with_artifacts = fake_render_svg_with_artifacts

    # matrixlayout.render imports jupyter_tikz lazily inside the function.
    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg(
        "TEX",
        crop="tight",
        padding={"left": 2, "bottom": 1},
        output_dir=tmp_path,
    )

    assert out == "<svg/>"
    assert len(calls) == 1
    tex_source, kwargs = calls[0]
    assert tex_source == "TEX"
    assert kwargs["crop"] == "tight"
    assert kwargs["padding"] == {"left": 2, "bottom": 1}
    assert Path(kwargs["output_dir"]) == tmp_path


def test_matrixlayout_render_svg_forwards_toolchain_and_options(monkeypatch, tmp_path):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg_with_artifacts(tex_source, **kwargs):
        calls.append((tex_source, kwargs))
        return _FakeArtifacts("<svg/>")

    fake.render_svg_with_artifacts = fake_render_svg_with_artifacts

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg(
        "TEX",
        toolchain_name="xelatex_dvisvgm",
        crop="page",
        padding=(1, 2, 3, 4),
        output_dir=tmp_path,
    )
    assert out == "<svg/>"
    assert len(calls) == 1
    tex_source, kwargs = calls[0]
    assert tex_source == "TEX"
    assert kwargs["toolchain_name"] == "xelatex_dvisvgm"
    assert kwargs["crop"] == "page"
    assert kwargs["padding"] == (1, 2, 3, 4)
    assert Path(kwargs["output_dir"]) == tmp_path


def test_backsubst_svg_passes_through_options(monkeypatch):
    # Patch the function reference used inside backsubst_svg so no TeX toolchain is needed.
    recorded = {}

    def fake_ml_render_svg(tex_source, **kwargs):
        recorded["tex_source"] = tex_source
        recorded["kwargs"] = kwargs
        return "<svg/>"

    monkeypatch.setattr(ml_backsubst, "render_svg", fake_ml_render_svg)

    out = ml_backsubst.backsubst_svg(
        system_txt="SYS",
        cascade_txt="CAS",
        solution_txt="SOL",
        crop="tight",
        padding={"top": 5},
        toolchain_name="pdftex_pdftocairo",
    )

    assert out == "<svg/>"
    assert recorded["kwargs"]["toolchain_name"] == "pdftex_pdftocairo"
    assert recorded["kwargs"]["crop"] == "tight"
    assert recorded["kwargs"]["padding"] == {"top": 5}
