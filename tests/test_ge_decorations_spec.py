from matrixlayout.ge import render_ge_tex
from matrixlayout.ge_decorations import normalize_index_list
from matrixlayout.formatting import decorator_bg, decorator_box, sel_col, sel_entry


def test_render_ge_tex_decorations_background_submatrix():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "submatrix": ("0:1", "0:1"), "background": "yellow!25"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "fill=yellow!25" in tex


def test_ge_decorations_module_normalizes_index_selectors():
    assert normalize_index_list("1:2", 4) == [1, 2]
    assert normalize_index_list(slice(1, 3), 4) == [1, 2]
    assert normalize_index_list((2, 0), 4) == [0, 1, 2]
    assert normalize_index_list(None, 3) == [0, 1, 2]


def test_render_ge_tex_decorations_background_entries_do_not_fill_whole_block():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "entries": [(0, 0)], "background": "yellow!25"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "fit=(1-1-medium) (1-1-medium)" in tex
    assert "fit=(1-1-medium) (2-2-medium)" not in tex


def test_render_ge_tex_decorations_background_entry_selectors():
    matrices = [[[1, 2], [3, 4]]]
    decorations = [
        {"grid": (0, 0), "entries": [sel_col(1)], "background": "yellow!25"},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)
    assert "fit=(1-2-medium) (1-2-medium)" in tex
    assert "fit=(2-2-medium) (2-2-medium)" in tex
    assert "fit=(1-1-medium) (1-1-medium)" not in tex


def test_render_ge_tex_multi_block_backgrounds_stay_on_target_grid():
    matrices = [
        [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
        [[[9, 10], [11, 12]], [[13, 14], [15, 16]]],
    ]
    decorations = [
        {"grid": (1, 1), "entries": [(0, 0)], "background": "yellow!25"},
    ]

    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str, create_medium_nodes=True)

    assert tex.count("fill=yellow!25") == 1
    assert "fit=(3-3-medium) (3-3-medium)" in tex
    assert "fit=(1-1-medium) (1-1-medium)" not in tex


def test_render_ge_tex_decorations_accept_callable_decorator_specs():
    matrices = [[[1, 2], [0, -2], [0, 0]]]
    decorations = [
        {"grid": (0, 0), "entries": [sel_col(0)], "decorator": decorator_bg("green!15")},
        {"grid": (0, 0), "entries": [sel_entry(0, 0), sel_entry(1, 1)], "decorator": decorator_box(color="red")},
    ]
    tex = render_ge_tex(matrices=matrices, decorations=decorations, formatter=str)
    assert r"\colorbox{green!15}" in tex
    assert r"\colorboxed{red}" in tex
    assert r"\color{black}{\colorboxed{red}{1}}" in tex
    assert r"\colorbox{green!15}{0}" in tex


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
        {"grid": (0, 0), "label": r"\\mathbf{A}", "side": "right", "angle_deg": -35, "length_mm": 8},
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
