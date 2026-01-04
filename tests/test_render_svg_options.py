import types
import sys

import pytest

from matrixlayout import render as ml_render
import matrixlayout.backsubst as ml_backsubst


def test_matrixlayout_render_svg_forwards_crop_and_padding(monkeypatch):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg(tex_source, **kwargs):
        calls.append((tex_source, kwargs))
        return "<svg/>"

    fake.render_svg = fake_render_svg

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg("TEX", crop="tight", padding={"left": 2, "bottom": 1})
    assert out == "<svg/>"
    assert calls == [("TEX", {"crop": "tight", "padding": {"left": 2, "bottom": 1}})]


def test_matrixlayout_render_svg_forwards_toolchain_and_options(monkeypatch):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg(tex_source, **kwargs):
        calls.append((tex_source, kwargs))
        return "<svg/>"

    fake.render_svg = fake_render_svg

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg(
        "TEX",
        toolchain_name="xelatex_dvisvgm",
        crop="page",
        padding=(1, 2, 3, 4),
    )
    assert out == "<svg/>"
    assert calls == [
        (
            "TEX",
            {
                "toolchain_name": "xelatex_dvisvgm",
                "crop": "page",
                "padding": (1, 2, 3, 4),
            },
        )
    ]


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
