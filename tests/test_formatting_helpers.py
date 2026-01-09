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
from matrixlayout.formatting import expand_entry_selectors, apply_decorator


def test_decorator_presets_wrap_tex():
    out = [
        decorator_box()("a"),
        decorator_color("red")("a"),
        decorator_bg("yellow")("a"),
        decorator_bf()("a"),
    ]
    assert r"\boxed{a}" in out[0]
    assert r"\color{red}{a}" in out[1]
    assert r"\colorbox{yellow}{a}" in out[2]
    assert r"\mathbf{a}" in out[3]
    for s in out:
        assert s and "None" not in s


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


def test_expand_entry_selectors_and_apply_decorator():
    entries = expand_entry_selectors([sel_entry(0, 0), sel_box((0, 1), (1, 1))], 2, 2, filter_bounds=True)
    assert entries == {(0, 0), (0, 1), (1, 1)}

    def dec(tex: str) -> str:
        return rf"[{tex}]"

    assert apply_decorator(dec, 0, 0, 5, "5") == "[5]"
