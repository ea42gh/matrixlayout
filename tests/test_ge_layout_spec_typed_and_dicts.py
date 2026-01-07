import shutil

import pytest

from matrixlayout.ge import ge_tex, ge_svg
from matrixlayout.specs import GELayoutSpec, PivotBox, RowEchelonPath, SubMatrixLoc, TextAt


def _pick_toolchain_name_or_skip() -> str:
    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not found")

    if shutil.which("dvisvgm") is not None:
        return "pdftex_dvisvgm"
    if shutil.which("pdftocairo") is not None:
        return "pdftex_pdftocairo"
    if shutil.which("pdf2svg") is not None:
        return "pdftex_pdf2svg"

    pytest.skip("no SVG converter found (need dvisvgm, pdftocairo, or pdf2svg)")
    raise AssertionError("unreachable")


def test_ge_tex_accepts_typed_layout_items():
    layout = GELayoutSpec(
        submatrix_locs=[SubMatrixLoc("name=A0", "1-1", "1-1")],
        pivot_locs=[PivotBox("(1-1)(1-1)", "draw, dashed")],
        txt_with_locs=[TextAt("(1-1)", "x_label", "anchor=west")],
        rowechelon_paths=[RowEchelonPath(r"\draw (1-1) -- (1-1);")],
    )
    tex = ge_tex(mat_rep="1", mat_format="r", layout=layout)
    assert r"\SubMatrix({1-1}{1-1})[name=A0]" in tex
    assert "fit=(1-1)(1-1)" in tex
    assert "x_label" in tex
    assert r"\draw (1-1) -- (1-1);" in tex


def test_ge_tex_accepts_dict_layout_items():
    layout = {
        "submatrix_locs": [
            {"opts": "name=A0", "start": "1-1", "end": "1-1"},
        ],
        "pivot_locs": [
            {"fit_target": "(1-1)(1-1)", "style": "draw, dashed"},
        ],
        "txt_with_locs": [
            {"coord": "(1-1)", "text": "x_label", "style": "anchor=west"},
        ],
        "rowechelon_paths": [
            {"tikz": r"\draw (1-1) -- (1-1);"},
        ],
    }
    tex = ge_tex(mat_rep="1", mat_format="r", layout=layout)
    assert r"\SubMatrix({1-1}{1-1})[name=A0]" in tex
    assert "fit=(1-1)(1-1)" in tex
    assert "x_label" in tex
    assert r"\draw (1-1) -- (1-1);" in tex


def test_ge_tex_submatrix_left_right_delims():
    layout = GELayoutSpec(
        submatrix_locs=[SubMatrixLoc("name=Z0", "1-1", "1-1", left_delim="[", right_delim="]")],
    )
    tex = ge_tex(mat_rep="1", mat_format="r", layout=layout)
    assert "name=Z0" in tex
    assert "_{" in tex
    assert "}^{" in tex


def test_ge_tex_dict_submatrix_left_right_delims():
    layout = {
        "submatrix_locs": [
            {"opts": "name=Z0", "start": "1-1", "end": "1-1", "left_delim": "[", "right_delim": "]"},
        ],
    }
    tex = ge_tex(mat_rep="1", mat_format="r", layout=layout)
    assert "name=Z0" in tex
    assert "_{" in tex
    assert "}^{" in tex


def test_ge_tex_dict_rowechelon_paths_with_tikz_key():
    layout = {
        "rowechelon_paths": [
            {"tikz": r"\draw (1-1) -- (1-1);"},
        ],
    }
    tex = ge_tex(mat_rep="1", mat_format="r", layout=layout)
    assert r"\draw (1-1) -- (1-1);" in tex


@pytest.mark.render
def test_ge_svg_smoke_with_typed_layout_items():
    pytest.importorskip("jupyter_tikz")
    layout = GELayoutSpec(
        submatrix_locs=[SubMatrixLoc("name=A0", "1-1", "1-1")],
        pivot_locs=[PivotBox("(1-1)(1-1)", "draw, dashed")],
        txt_with_locs=[TextAt("(1-1)", r"$x_1$", "anchor=west")],
        rowechelon_paths=[RowEchelonPath(r"\draw (1-1) -- (1-1);")],
    )
    svg = ge_svg(
        mat_rep="1",
        mat_format="r",
        layout=layout,
        toolchain_name=_pick_toolchain_name_or_skip(),
        crop="tight",
        padding=2,
    )
    assert "<svg" in svg
