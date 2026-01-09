from matrixlayout import (
    decorator_box,
    decorator_color,
    decorator_bg,
    decorator_bf,
    sel_entry,
    sel_box,
    sel_row,
    sel_col,
    sel_rows,
    sel_cols,
    sel_all,
    sel_vec,
    sel_vec_range,
)


def test_decorator_presets_wrap_tex():
    assert r"\boxed{a}" in decorator_box()("a")
    assert r"\color{red}{a}" in decorator_color("red")("a")
    assert r"\colorbox{yellow}{a}" in decorator_bg("yellow")("a")
    assert r"\mathbf{a}" in decorator_bf()("a")


def test_selector_helpers():
    assert sel_entry(1, 2) == (1, 2)
    assert sel_box((0, 0), (1, 1)) == ((0, 0), (1, 1))
    assert sel_row(3) == {"row": 3}
    assert sel_col(4) == {"col": 4}
    assert sel_rows([1, 2]) == {"rows": [1, 2]}
    assert sel_cols([2, 3]) == {"cols": [2, 3]}
    assert sel_all() == {"all": True}
    assert sel_vec(0, 1, 2) == (0, 1, 2)
    assert sel_vec_range((0, 1, 0), (0, 1, 2)) == ((0, 1, 0), (0, 1, 2))
