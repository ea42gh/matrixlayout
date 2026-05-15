import pytest

from matrixlayout.formatting import latexify


def test_latexify_string_passthrough():
    assert latexify(r"\alpha + 1") == r"\alpha + 1"


def test_latexify_numbers():
    assert latexify(3) == "3"
    assert latexify(1.2300) == "1.23"


def test_latexify_tuple_rational():
    assert latexify((1, 2)) == r"\frac{1}{2}"


def test_latexify_fraction_unicode_bool_and_fallback():
    from fractions import Fraction

    assert latexify(Fraction(2, 3)) == r"\frac{2}{3}"
    assert latexify("Aᵀ") == r"A^{T}"
    assert latexify(True) == "True"
    assert latexify(object()).startswith("<object object at")


def test_latexify_sympy_objects():
    sym = pytest.importorskip("sympy")
    assert latexify(sym.pi) == r"\pi"
    assert latexify(sym.Rational(1, 2)) == r"\frac{1}{2}"
    assert latexify(sym.Symbol("x")) == "x"


def test_make_decorator_and_decorate_entries():
    from matrixlayout import decorate_tex_entries, make_decorator

    matrices = [[None, [[1, 2], [3, 4]]]]
    dec = make_decorator(text_color="red", bf=True)
    out = decorate_tex_entries(matrices, 0, 1, dec, entries=[(0, 1)])

    assert out[0][1][0][1] == r"\color{red}{\mathbf{2}}"
    assert out[0][1][0][0] == 1


def test_make_decorator_all_options():
    from matrixlayout import make_decorator

    dec = make_decorator(
        text_color="blue",
        bg_color="yellow!20",
        text_bg="green!10",
        boxed=True,
        box_color="red",
        bf=True,
        move_right=True,
        delim="|",
    )

    out = dec("x")

    assert r"\mathbf{x}" in out
    assert r"\boxed" in out
    assert r"\colorboxed{red}" in out
    assert r"\colorbox{yellow!20}" in out
    assert r"\Block[draw=blue,fill=green!10]" in out
    assert r"\color{blue}" in out
    assert r"\mathrlap" in out
    assert out.startswith("|")
    assert out.endswith("|")


def test_decorator_helpers_and_selectors():
    from matrixlayout import decorator_bf, decorator_bg, decorator_box, decorator_color
    from matrixlayout import sel_all, sel_box, sel_col, sel_cols, sel_entry, sel_row, sel_rows, sel_vec, sel_vec_range

    assert decorator_box()("x") == r"\color{black}{\boxed{x}}"
    assert decorator_box(color="red")("x") == r"\color{black}{\colorboxed{red}{x}}"
    assert decorator_color("blue")("x") == r"\color{blue}{x}"
    assert decorator_bg("yellow")("x") == r"\colorbox{yellow}{x}"
    assert decorator_bf()("x") == r"\color{black}{\mathbf{x}}"

    assert sel_entry("1", "2") == (1, 2)
    assert sel_box(("0", "1"), ("2", "3")) == ((0, 1), (2, 3))
    assert sel_row("1") == {"row": 1}
    assert sel_col("2") == {"col": 2}
    assert sel_rows(["1", 2]) == {"rows": [1, 2]}
    assert sel_cols(["3", 4]) == {"cols": [3, 4]}
    assert sel_all() == {"all": True}
    assert sel_vec("1", "2", "3") == (1, 2, 3)
    assert sel_vec_range(("0", "1", "2"), ("3", "4", "5")) == ((0, 1, 2), (3, 4, 5))


def test_decorate_tex_entries_bounds_none_and_array_like():
    import matrixlayout

    assert matrixlayout.decorate_tex_entries([[None]], 0, 0, lambda x: f"!{x}!") == [[None]]

    with pytest.raises(IndexError):
        matrixlayout.decorate_tex_entries([[None]], 4, 0, lambda x: x)

    class ArrayLike:
        def tolist(self):
            return [[1, 2]]

    out = matrixlayout.decorate_tex_entries([[ArrayLike()]], 0, 0, lambda x: f"!{x}!", entries=[(0, 1), (9, 9)])
    assert out == [[[[1, "!2!"]]]]


def test_expand_entry_selectors_variants_and_filtering():
    from matrixlayout.formatting import expand_entry_selectors

    assert expand_entry_selectors(None, 2, 2) == {(0, 0), (0, 1), (1, 0), (1, 1)}
    selectors = [
        {"all": True},
        {"row": 1},
        {"col": 0},
        {"rows": [0, 2]},
        {"cols": [1, 3]},
        ((0, 0), (1, 1)),
        (2, 2),
        1,
    ]
    out = expand_entry_selectors(selectors, 2, 2, allow_int=True, filter_bounds=True)
    assert out == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_apply_decorator_signatures_and_invalid_arity():
    from matrixlayout.formatting import apply_decorator

    assert apply_decorator(lambda tex: f"!{tex}!", 1, 2, 3, "x") == "!x!"
    assert apply_decorator(lambda i, j, v, tex: f"{i},{j},{v},{tex}", 1, 2, 3, "x") == "1,2,3,x"

    def no_signature(tex):
        return f"?{tex}?"

    no_signature.__signature__ = object()
    assert apply_decorator(no_signature, 1, 2, 3, "x") == "?x?"

    with pytest.raises(ValueError, match="Decorator must accept"):
        apply_decorator(lambda a, b: "bad", 1, 2, 3, "x")
