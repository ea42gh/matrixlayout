import pytest


from matrixlayout.ge import render_ge_tex, _tex
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
        text_annotations=[((1, 1), "x", SymLike(":red"))],
    )

    tex_out = _tex(
        mat_rep="1",
        mat_format="c",
        layout=layout,
    )

    assert r"\SubMatrix({1-1}{1-1})[name=Z]" in tex_out
    assert r"fit=(1-1)(1-1)" in tex_out
    assert r"\node[red] at (1-1)" in tex_out


def test_ge_tex_accepts_layout_spec_text_annotations():
    layout = GELayoutSpec(text_annotations=[((1, 1), "new", "blue")])

    tex_out = _tex(
        mat_rep="1",
        mat_format="c",
        layout=layout,
    )

    assert r"\node[blue] at (1-1)" in tex_out
    assert "{ new }" in tex_out


def test_ge_tex_accepts_direct_text_annotations():
    tex_out = _tex(
        mat_rep="1",
        mat_format="c",
        text_annotations=[((1, 1), "direct", "green")],
    )

    assert r"\node[green] at (1-1)" in tex_out
    assert "{ direct }" in tex_out


def test_render_ge_tex_merges_layout_spec_callouts():
    # One GE layer in the stack 2-column layout: [[None, A0]]
    matrices = [[None, [[1, 2], [3, 4]]]]

    layout = GELayoutSpec(
        callouts=[{"name": "A0", "label": "A_0", "side": "right"}],
    )

    tex_out = render_ge_tex(matrices=matrices, layout=layout)
    assert "A0-right" in tex_out
    assert r"\draw[" in tex_out




def test_ge_tex_layout_sets_outer_delims_without_conflict_when_not_explicit():
    # layout sets outer_delims, and tex should treat its own defaults as "unset"
    tex_out = _tex(
        mat_rep=r"1 & 2 \\ 3 & 4",
        mat_format="cc",
        layout={
            "outer_delims": True,
            "outer_delims_span": (2, 2),
            "outer_delims_name": "Z0",
        },
    )
    assert r"\SubMatrix({1-1}{2-2})[name=Z0]" in tex_out

def test_ge_tex_layout_conflict_raises():
    layout = GELayoutSpec(landscape=True)
    with pytest.raises(ValueError):
        _tex(mat_rep="1", mat_format="c", landscape=False, layout=layout)

