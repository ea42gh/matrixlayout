import pytest

from matrixlayout.backsubst_helpers import apply_line_decorators
from matrixlayout.backsubst_helpers import as_lines
from matrixlayout.backsubst_helpers import as_scale


def test_as_lines_normalizes_none_string_and_sequence():
    assert as_lines(None) == []
    assert as_lines("x") == ["x"]
    assert as_lines(("x", 2)) == ["x", "2"]


def test_as_scale_formats_numeric_values():
    assert as_scale(None) is None
    assert as_scale("0.75") == "0.75"
    assert as_scale(1.25) == "1.25"


def test_apply_line_decorators_applies_integer_selector():
    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    out = apply_line_decorators(
        ["L1", "L2"],
        [{"block": "cascade", "entries": [1], "decorator": dec}],
        "cascade",
        strict=True,
    )

    assert out == ["L1", r"\boxed{L2}"]


def test_apply_line_decorators_strict_rejects_empty_targeted_block():
    def dec(tex: str) -> str:
        return tex

    with pytest.raises(ValueError, match="decorator selector did not match"):
        apply_line_decorators(
            [],
            [{"block": "system", "entries": [0], "decorator": dec}],
            "system",
            strict=True,
        )


def test_apply_line_decorators_rejects_nondict_spec():
    with pytest.raises(ValueError, match="decorators must be dict"):
        apply_line_decorators(["L1"], ["bad"], "cascade", strict=False)


def test_apply_line_decorators_rejects_noncallable_decorator():
    with pytest.raises(ValueError, match="decorator must be callable"):
        apply_line_decorators(
            ["L1"],
            [{"block": "cascade", "entries": [0], "decorator": "bad"}],
            "cascade",
            strict=False,
        )


def test_apply_line_decorators_ignores_other_blocks_and_out_of_bounds_when_not_strict():
    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    out = apply_line_decorators(
        ["L1"],
        [
            {"block": "system", "entries": [0], "decorator": dec},
            {"block": "cascade", "entries": [3], "decorator": dec},
        ],
        "cascade",
        strict=False,
    )

    assert out == ["L1"]


def test_apply_line_decorators_strict_empty_block_rejects_nondict_spec():
    with pytest.raises(ValueError, match="decorators must be dict"):
        apply_line_decorators([], ["bad"], "system", strict=True)


def test_apply_line_decorators_strict_empty_block_rejects_noncallable_decorator():
    with pytest.raises(ValueError, match="decorator must be callable"):
        apply_line_decorators(
            [],
            [{"block": "system", "entries": [0], "decorator": "bad"}],
            "system",
            strict=True,
        )
