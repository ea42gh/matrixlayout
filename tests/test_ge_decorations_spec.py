from matrixlayout.ge import ge_grid_tex


def test_ge_grid_tex_decorations_background_submatrix():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorations = [
        {"grid": (0, 1), "submatrix": ("0:1", "0:1"), "background": "yellow!25"},
    ]
    tex = ge_grid_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "fill=yellow!25" in tex


def test_ge_grid_tex_decorations_box_submatrix():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorations = [
        {"grid": (0, 1), "submatrix": ((0, 0), (0, 1)), "box": True},
    ]
    tex = ge_grid_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\boxed{1}" in tex
    assert r"\boxed{2}" in tex
    assert r"\boxed{3}" not in tex


def test_ge_grid_tex_decorations_color_rows_cols_range():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorations = [
        {"grid": (0, 1), "rows": "0:1", "cols": "1:1", "color": "red"},
    ]
    tex = ge_grid_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\color{red}{2}" in tex
    assert r"\color{red}{4}" in tex


def test_ge_grid_tex_decorations_lines_and_label():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorations = [
        {"grid": (0, 1), "hlines": 1},
        {"grid": (0, 1), "vlines": 1},
        {"grid": (0, 1), "label": r"\\mathbf{A}", "side": "right", "angle": -35, "length": 8},
    ]
    tex = ge_grid_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert "hlines=1" in tex
    assert "vlines=1" in tex
    assert r"\mathbf{A}" in tex
