import pytest

from matrixlayout.formatting import latexify


def test_latexify_string_passthrough():
    assert latexify(r"\alpha + 1") == r"\alpha + 1"


def test_latexify_numbers():
    assert latexify(3) == "3"
    assert latexify(1.2300) == "1.23"


def test_latexify_tuple_rational():
    assert latexify((1, 2)) == r"\frac{1}{2}"


def test_latexify_sympy_objects():
    sym = pytest.importorskip("sympy")
    assert latexify(sym.pi) == r"\pi"
    assert latexify(sym.Rational(1, 2)) == r"\frac{1}{2}"
    assert latexify(sym.Symbol("x")) == "x"
