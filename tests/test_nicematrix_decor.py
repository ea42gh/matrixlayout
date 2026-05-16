import pytest

from matrixlayout.nicematrix_decor import (
    infer_ge_layer_callouts,
    render_delim_callout,
    render_delim_callouts,
    validate_callouts,
)


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
        [{"grid": (0, 0), "label": "A", "side": "left"}],
        available_names=["A0"],
        name_map={(0, 0): "A0"},
        strict=False,
    )
    assert errs == []


def test_render_delim_callout_defaults_unknown_side_and_anchor():
    tex = render_delim_callout({"name": "A0", "label": "A", "side": "diagonal", "anchor": "nowhere"})

    assert "(A0-right.north)" in tex
    assert "{$A$}" in tex


def test_ge_layer_callouts_merges_style_without_mutating_it():
    style = {"color": "red", "angle_deg": -20.0}

    callouts = infer_ge_layer_callouts([[[None, [[1]]]], [[[1]], [[2]]]], **style)

    assert style == {"color": "red", "angle_deg": -20.0}
    assert {"grid": (0, 1), "label": r"A_{0}", "side": "right", **style} in callouts
    assert {"grid": (1, 0), "label": r"E_{1}", "side": "left", **style} in callouts


def test_render_delim_callouts_true_generates_default_callouts():
    rendered = render_delim_callouts(True, available_names=["A0", "E1"])

    assert len(rendered) == 2
    assert any("(A0-right.north)" in item and r"$A_{0}$" in item for item in rendered)
    assert any("(E1-left.north)" in item and r"$E_{1}$" in item for item in rendered)


def test_render_delim_callouts_resolves_block_row_and_column():
    rendered = render_delim_callouts(
        [{"block_row": 2, "block_col": 1, "label": "B", "side": "right"}],
        available_names=["A2"],
        name_map={(2, 1): "A2"},
    )

    assert len(rendered) == 1
    assert "(A2-right.north)" in rendered[0]
