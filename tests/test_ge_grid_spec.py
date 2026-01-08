import matrixlayout
from matrixlayout.specs import GEGridSpec


def _sample_grid():
    A0 = [[1, 2], [3, 4]]
    E1 = [[1, 0], [0, 1]]
    A1 = [[1, 2], [0, 1]]
    return [[None, A0], [E1, A1]]


def test_ge_grid_tex_accepts_spec_object():
    matrices = _sample_grid()
    spec = GEGridSpec(
        matrices=matrices,
        Nrhs=0,
        outer_hspace_mm=9,
        legacy_submatrix_names=True,
    )
    tex_direct = matrixlayout.ge_grid_tex(matrices=matrices, outer_hspace_mm=9, legacy_submatrix_names=True)
    tex_spec = matrixlayout.ge_grid_tex(spec=spec)
    assert tex_direct == tex_spec


def test_ge_grid_tex_accepts_spec_dict_with_layout():
    matrices = _sample_grid()
    spec = {
        "matrices": matrices,
        "Nrhs": 0,
        "outer_hspace_mm": 9,
        "legacy_submatrix_names": True,
        "layout": {"preamble": "%spec-preamble"},
    }
    tex = matrixlayout.ge_grid_tex(spec=spec)
    assert "%spec-preamble" in tex
