import pytest


from matrixlayout.ge import ge_grid_tex, ge_tex
from matrixlayout.specs import GELayoutSpec


def test_ge_tex_accepts_layout_spec_for_julia_style_inputs():
    class SymLike:
        def __init__(self, s: str):
            self.s = s

        def __str__(self) -> str:
            return self.s

    layout = GELayoutSpec(
        submatrix_locs=[(SymLike(":name=Z"), (1, 1), (1, 1))],
        pivot_locs=[(((1, 1), (1, 1)), SymLike(":thick"))],
        txt_with_locs=[((1, 1), "x", SymLike(":red"))],
    )

    tex = ge_tex(
        mat_rep="1",
        mat_format="c",
        layout=layout,
    )

    assert r"\SubMatrix({1-1}{1-1})[name=Z]" in tex
    assert r"fit=(1-1)(1-1)" in tex
    assert r"\node[red] at (1-1)" in tex


def test_ge_grid_tex_merges_layout_spec_callouts():
    # One GE layer in the legacy 2-column layout: [[None, A0]]
    matrices = [[None, [[1, 2], [3, 4]]]]

    layout = GELayoutSpec(
        callouts=[{"name": "A0", "label": "A_0", "side": "right"}],
    )

    tex = ge_grid_tex(matrices=matrices, layout=layout)
    assert "A0-right" in tex
    assert r"\draw[" in tex


def test_ge_tex_layout_conflict_raises():
    layout = GELayoutSpec(landscape=True)
    with pytest.raises(ValueError):
        ge_tex(mat_rep="1", mat_format="c", landscape=False, layout=layout)
