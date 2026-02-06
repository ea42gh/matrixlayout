import pytest

from matrixlayout.nicematrix_decor import render_delim_callout, validate_callouts


def test_render_delim_callout_math_mode_wraps_label():
    tex = render_delim_callout({"name": "A0", "label": r"\mathbf{A}", "math_mode": True})
    assert "{$\\mathbf{A}$}" in tex

    tex_no_math = render_delim_callout({"name": "A0", "label": "Label", "math_mode": False})
    assert "{$Label$}" not in tex_no_math


def test_validate_callouts_strict_mode_raises_on_unknown_name():
    with pytest.raises(ValueError):
        validate_callouts(
            [{"grid_pos": (1, 1), "label": "X", "side": "left"}],
            available_names=["A0"],
            name_map={(0, 0): "A0"},
            strict=True,
        )


def test_validate_callouts_non_strict_returns_errors():
    errs = validate_callouts(
        [{"grid_pos": (1, 1), "label": "X", "side": "left"}],
        available_names=["A0"],
        name_map={(0, 0): "A0"},
        strict=False,
    )
    assert errs and "grid_pos" in errs[0]


def test_validate_callouts_passes_on_known_name():
    errs = validate_callouts(
        [{"grid_pos": (0, 0), "label": "A", "side": "left"}],
        available_names=["A0"],
        name_map={(0, 0): "A0"},
        strict=False,
    )
    assert errs == []
