from matrixlayout.ge import render_ge_tex


def test_render_ge_tex_decorations_background_submatrix():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:1", "0:1"), "background": "yellow!25"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "fill=yellow!25" in tex


def test_render_ge_tex_decorations_box_submatrix():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ((0, 0), (0, 1)), "box": True},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\boxed{1}" in tex
    assert r"\boxed{2}" in tex
    assert r"\boxed{3}" not in tex


def test_render_ge_tex_decorations_color_rows_cols_range():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "rows": "0:1", "cols": "1:1", "color": "red"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\color{red}{2}" in tex
    assert r"\color{red}{4}" in tex


def test_render_ge_tex_decorations_color_and_bold():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "entries": [(0, 0)], "color": "red", "bold": True},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\color{red}{\mathbf{1}}" in tex


def test_render_ge_tex_decorations_outline():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:1", "0:1"), "outline": True, "color": "blue"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "draw=blue" in tex


def test_render_ge_tex_decorations_lines_and_label():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "hlines": 1},
        {"grid": (0, 0), "vlines": 1},
        {"grid": (0, 0), "label": r"\\mathbf{A}", "side": "right", "angle": -35, "length": 8},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert "hlines=1" in tex
    assert "vlines=1" in tex
    assert r"\mathbf{A}" in tex


def test_render_ge_tex_decorations_lines_submatrix_shorthand():
    matrices = [[[1, 2, 3, 4], [5, 6, 7, 8]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:0", None), "hlines": "submatrix"},
        {"grid": (0, 0), "submatrix": (None, "0:2"), "vlines": True},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert "hlines=1" in tex
    assert "vlines=3" in tex


def test_render_ge_tex_decorations_lines_bounds():
    matrices = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:1", None), "hlines": "bounds"},
        {"grid": (0, 0), "submatrix": (None, "0:1"), "vlines": "bounds"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert "hlines=2" in tex
    assert "vlines=2" in tex


def test_render_ge_tex_decorations_lines_all():
    matrices = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:2", None), "hlines": "all"},
        {"grid": (0, 0), "submatrix": (None, "0:2"), "vlines": "all"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert "hlines={1,2}" in tex or "hlines={1, 2}" in tex
    assert "vlines={1,2}" in tex or "vlines={1, 2}" in tex


def test_render_ge_tex_decorations_rows_cols_selection():
    matrices = [[[1, 2, 3], [4, 5, 6]]]
    decorations = [
        {"grid": (0, 0), "rows": [0], "cols": [1, 2], "color": "red"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\color{red}{2}" in tex
    assert r"\color{red}{3}" in tex
