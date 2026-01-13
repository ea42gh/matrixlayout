from matrixlayout.ge import grid_tex, tex


def test_grid_tex_inserts_rhs_partition_bar():
    # One GE layer with an augmented matrix [A|b] (2x3, Nrhs=1).
    matrices = [[None, [[1, 0, 3], [0, 2, 4]]]]
    tex_out = grid_tex(matrices, Nrhs=1)
    assert r"\begin{NiceArray}[vlines-in-sub-matrix = I]{rr@{\hspace{6mm}}rr|r}" in tex_out


def test_ge_tex_normalizes_julia_style_inputs():
    class SymLike:
        def __init__(self, s: str):
            self.s = s

        def __str__(self) -> str:
            return self.s

    tex_out = tex(
        mat_rep="1",
        mat_format="c",
        submatrix_locs=[(SymLike(":name=Z"), (1, 1), (1, 1))],
        pivot_locs=[(((1, 1), (1, 1)), SymLike("Symbol(:thick)"))],
        txt_with_locs=[((1, 1), "x", SymLike("Symbol(:red)"))],
    )

    assert r"\SubMatrix({1-1}{1-1})[name=Z]" in tex_out
    assert r"fit=(1-1)(1-1)" in tex_out
    assert r"\node[red] at (1-1)" in tex_out
