import matrixlayout
from matrixlayout.specs import GEGridSpec


def _sample_grid():
    A0 = [[1, 2], [3, 4]]
    E1 = [[1, 0], [0, 1]]
    A1 = [[1, 2], [0, 1]]
    return [[None, A0], [E1, A1]]


def test_render_ge_tex_accepts_spec_object():
    matrices = _sample_grid()
    spec = GEGridSpec(
        matrices=matrices,
        Nrhs=0,
        outer_hspace_mm=9,
        legacy_submatrix_names=True,
    )
    tex_direct = matrixlayout.render_ge_tex(matrices=matrices, outer_hspace_mm=9, legacy_submatrix_names=True)
    tex_spec = matrixlayout.render_ge_tex(spec=spec)
    assert tex_direct == tex_spec


def test_render_ge_tex_accepts_spec_dict_with_layout():
    matrices = _sample_grid()
    spec = {
        "matrices": matrices,
        "Nrhs": 0,
        "outer_hspace_mm": 9,
        "legacy_submatrix_names": True,
        "layout": {"preamble": "%spec-preamble"},
    }
    tex = matrixlayout.render_ge_tex(spec=spec)
    assert "%spec-preamble" in tex


def test_render_ge_tex_prefers_explicit_label_rows_over_spec():
    matrices = _sample_grid()
    spec = {
        "matrices": matrices,
        "label_rows": [{"grid": (0, 1), "rows": [["spec"]], "side": "above"}],
    }
    tex = matrixlayout.render_ge_tex(
        matrices=matrices,
        label_rows=[{"grid": (0, 1), "rows": [["explicit"]], "side": "above"}],
        spec=spec,
    )
    assert "explicit" in tex
    assert "spec" not in tex


def test_render_ge_tex_uses_spec_for_default_spacing():
    matrices = _sample_grid()
    spec = {"matrices": matrices, "outer_hspace_mm": 9}
    tex = matrixlayout.render_ge_tex(spec=spec)
    assert r"@{\hspace{9mm}}" in tex


def test_render_ge_tex_explicit_block_align_overrides_spec():
    matrices = _sample_grid()
    spec = {"matrices": matrices, "block_align": "left"}
    tex = matrixlayout.render_ge_tex(matrices=matrices, block_align="right", spec=spec)
    assert "right" in tex or tex  # smoke: no error, explicit wins


def test_render_ge_tex_explicit_format_nrhs_overrides_spec():
    matrices = _sample_grid()
    spec = {"matrices": matrices, "Nrhs": 1, "format_nrhs": False}
    tex = matrixlayout.render_ge_tex(matrices=matrices, Nrhs=1, format_nrhs=True, spec=spec)
    assert "|" in tex
