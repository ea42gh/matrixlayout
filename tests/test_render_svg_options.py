import types
import sys
from pathlib import Path

import pytest

from matrixlayout import render as ml_render
import matrixlayout.backsubst as ml_backsubst
import matrixlayout.ge as ml_ge
import matrixlayout.qr as ml_qr
import matrixlayout.eigproblem as ml_eig


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
    assert Path(kwargs["output_dir"]).parent == tmp_path
    assert Path(kwargs["output_dir"]).name.startswith("matrixlayout_render_")


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
    assert Path(kwargs["output_dir"]).parent == tmp_path
    assert Path(kwargs["output_dir"]).name.startswith("matrixlayout_render_")


def test_matrixlayout_render_svg_rejects_unknown_toolchain_early(monkeypatch, tmp_path):
    fake = types.SimpleNamespace(TOOLCHAINS={"pdftex_pdftocairo": object()})

    def fake_render_svg_with_artifacts(tex_source, **kwargs):
        raise AssertionError("rendering should not be called for an unknown toolchain")

    fake.render_svg_with_artifacts = fake_render_svg_with_artifacts

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    with pytest.raises(ValueError, match="Unknown jupyter_tikz toolchain"):
        ml_render.render_svg("TEX", toolchain_name="missing_toolchain", output_dir=tmp_path)


def test_validate_render_opts_accepts_supported_keys(tmp_path):
    ml_render.validate_render_opts(
        {
            "toolchain_name": "pdftex_pdftocairo",
            "output_stem": "demo",
            "crop": "tight",
            "padding": (1, 2, 3, 4),
            "frame": True,
            "exact_bbox": False,
            "output_dir": tmp_path,
        }
    )


def test_validate_render_opts_rejects_unknown_keys():
    with pytest.raises(ValueError, match="Unknown render option"):
        ml_render.validate_render_opts({"toolchain": "pdftex_pdftocairo"})


def test_validate_render_opts_rejects_non_mapping():
    with pytest.raises(TypeError, match="render_opts must be a mapping"):
        ml_render.validate_render_opts(["crop", "tight"])


def test_merge_render_opts_preserves_render_opts_without_overrides(tmp_path):
    opts = ml_render.merge_render_opts(
        {
            "toolchain_name": "pdftex_pdftocairo",
            "crop": "page",
            "output_dir": tmp_path,
        }
    )

    assert opts == {
        "toolchain_name": "pdftex_pdftocairo",
        "crop": "page",
        "output_dir": tmp_path,
    }


def test_merge_render_opts_applies_non_none_overrides():
    opts = ml_render.merge_render_opts(
        {"crop": "page", "padding": (1, 1, 1, 1), "frame": True},
        crop="tight",
        padding=None,
        frame=False,
    )

    assert opts["crop"] == "tight"
    assert opts["padding"] == (1, 1, 1, 1)
    assert opts["frame"] is False


def test_matrixlayout_render_svg_falls_back_to_legacy_render_svg(monkeypatch, tmp_path):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg(tex_source, **kwargs):
        calls.append((tex_source, kwargs))
        return "<svg>legacy</svg>"

    fake.render_svg = fake_render_svg

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg(
        "TEX",
        crop="tight",
        padding=(1, 2, 3, 4),
        output_dir=tmp_path,
    )

    assert out == "<svg>legacy</svg>"
    assert len(calls) == 1
    tex_source, kwargs = calls[0]
    assert tex_source == "TEX"
    assert kwargs["crop"] == "tight"
    assert kwargs["padding"] == (1, 2, 3, 4)
    assert "output_dir" not in kwargs


def test_matrixlayout_render_svg_fallback_uses_artifacts_path_when_available(monkeypatch, tmp_path):
    calls = []

    fake = types.SimpleNamespace()

    def fake_render_svg(tex_source, *, artifacts_path=None):
        calls.append((tex_source, artifacts_path))
        return "<svg>legacy-artifacts</svg>"

    fake.render_svg = fake_render_svg

    monkeypatch.setitem(sys.modules, "jupyter_tikz", fake)

    out = ml_render.render_svg("TEX", output_dir=tmp_path)

    assert out == "<svg>legacy-artifacts</svg>"
    assert len(calls) == 1
    tex_source, artifacts_path = calls[0]
    assert tex_source == "TEX"
    assert Path(artifacts_path).parent == tmp_path
    assert Path(artifacts_path).name.startswith("matrixlayout_render_")


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


def test_backsubst_svg_rejects_unknown_render_opts(monkeypatch):
    monkeypatch.setattr(
        ml_backsubst,
        "render_svg",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    with pytest.raises(ValueError, match="Unknown render option"):
        ml_backsubst.backsubst_svg(system_txt="SYS", render_opts={"toolchain": "tc"})


def test_render_ge_svg_merges_render_opts(monkeypatch):
    recorded = {}

    def fake_render_svg(tex_source, **kwargs):
        recorded["tex_source"] = tex_source
        recorded["kwargs"] = kwargs
        return "<svg/>"

    monkeypatch.setattr(ml_ge, "_render_svg", fake_render_svg)

    out = ml_ge.render_ge_svg(
        matrices=[[None, [[1]]]],
        render_opts={"crop": "page", "padding": (1, 1, 1, 1), "toolchain_name": "tc"},
        crop="tight",
        padding=(2, 2, 2, 2),
        frame=True,
        exact_bbox=True,
        output_stem="ge_opts",
    )

    assert out == "<svg/>"
    assert recorded["kwargs"]["crop"] == "tight"
    assert recorded["kwargs"]["padding"] == (2, 2, 2, 2)
    assert recorded["kwargs"]["toolchain_name"] == "tc"
    assert recorded["kwargs"]["frame"] is True
    assert recorded["kwargs"]["exact_bbox"] is True
    assert recorded["kwargs"]["output_stem"] == "ge_opts"


def test_render_ge_svg_rejects_unknown_render_opts(monkeypatch):
    monkeypatch.setattr(
        ml_ge,
        "_render_svg",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    with pytest.raises(ValueError, match="Unknown render option"):
        ml_ge.render_ge_svg(matrices=[[None, [[1]]]], render_opts={"toolchain": "tc"})


def test_render_qr_svg_merges_render_opts(monkeypatch):
    recorded = {}

    def fake_render_svg(tex_source, **kwargs):
        recorded["tex_source"] = tex_source
        recorded["kwargs"] = kwargs
        return "<svg/>"

    monkeypatch.setattr(ml_qr, "render_svg", fake_render_svg)
    monkeypatch.setattr(ml_qr, "render_qr_tex", lambda *args, **kwargs: "TEX")

    out = ml_qr.render_qr_svg(
        matrices=[[None, [[1]]]],
        render_opts={"crop": "page", "padding": (1, 1, 1, 1)},
        crop="tight",
        padding=(2, 2, 2, 2),
        exact_bbox=True,
        output_stem="qr_opts",
    )

    assert out == "<svg/>"
    assert recorded["kwargs"]["crop"] == "tight"
    assert recorded["kwargs"]["padding"] == (2, 2, 2, 2)
    assert recorded["kwargs"]["exact_bbox"] is True
    assert recorded["kwargs"]["output_stem"] == "qr_opts"


def test_render_qr_svg_rejects_unknown_render_opts(monkeypatch):
    monkeypatch.setattr(
        ml_qr,
        "render_svg",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )
    monkeypatch.setattr(ml_qr, "render_qr_tex", lambda *args, **kwargs: "TEX")

    with pytest.raises(ValueError, match="Unknown render option"):
        ml_qr.render_qr_svg(matrices=[[None, [[1]]]], render_opts={"toolchain": "tc"})


def test_render_eig_svg_merges_render_opts(monkeypatch):
    recorded = {}

    def fake_render_svg(tex_source, **kwargs):
        recorded["tex_source"] = tex_source
        recorded["kwargs"] = kwargs
        return "<svg/>"

    monkeypatch.setattr(ml_eig, "render_svg", fake_render_svg)
    monkeypatch.setattr(ml_eig, "render_eig_tex", lambda *args, **kwargs: "TEX")

    out = ml_eig.render_eig_svg(
        {"dummy": True},
        render_opts={"crop": "page", "padding": (1, 1, 1, 1)},
        crop="tight",
        padding=(2, 2, 2, 2),
        exact_bbox=True,
        output_stem="eig_opts",
    )

    assert out == "<svg/>"
    assert recorded["kwargs"]["crop"] == "tight"
    assert recorded["kwargs"]["padding"] == (2, 2, 2, 2)
    assert recorded["kwargs"]["exact_bbox"] is True
    assert recorded["kwargs"]["output_stem"] == "eig_opts"


def test_render_eig_svg_rejects_unknown_render_opts(monkeypatch):
    monkeypatch.setattr(
        ml_eig,
        "render_svg",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )
    monkeypatch.setattr(ml_eig, "render_eig_tex", lambda *args, **kwargs: "TEX")

    with pytest.raises(ValueError, match="Unknown render option"):
        ml_eig.render_eig_svg({"dummy": True}, render_opts={"toolchain": "tc"})
