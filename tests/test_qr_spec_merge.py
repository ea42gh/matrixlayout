from matrixlayout.qr import _mat_shape, _qr_known_zero_entries, _qr_label_layouts, _qr_name_specs_to_callouts
from matrixlayout.qr import render_qr_tex
from matrixlayout.qr_spec_merge import (
    merge_scalar_default,
    qr_known_zero_entries,
    qr_label_layouts,
    qr_name_specs_to_callouts,
)
from matrixlayout.specs import QRGridSpec


def test_qr_known_zero_entries_module_matches_compatibility_alias():
    grid = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 0], [2, 3]], [[1, 0], [0, 1]]],
    ]
    assert qr_known_zero_entries(grid, mat_shape=_mat_shape) == _qr_known_zero_entries(grid)


def test_qr_label_layouts_module_matches_compatibility_alias():
    grid = [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]], [None, [[1, 0], [0, 1]]]]
    assert qr_label_layouts(grid, "red", mat_shape=_mat_shape) == _qr_label_layouts(grid, "red")


def test_qr_name_specs_to_callouts_module_matches_compatibility_alias():
    specs = [[(0, 2), "al", r"\mathbf{A}"], [(2, 2), "br", r"\mathbf{R = S W^T A}"]]
    kwargs = {
        "color": "blue",
        "label_shift_rules": [(r"\mathbf{R = S W^T A}", -1.0)],
        "length_rules": [(r"\mathbf{A}", 8.0)],
    }
    assert qr_name_specs_to_callouts(specs, **kwargs) == _qr_name_specs_to_callouts(specs, **kwargs)


def test_merge_scalar_default_lets_spec_override_renderer_default():
    assert merge_scalar_default("label_color", "blue", "green", "blue") == "green"


def test_merge_scalar_default_rejects_non_default_conflict():
    try:
        merge_scalar_default("label_color", "purple", "green", "blue")
    except ValueError as exc:
        assert "Conflicting values for label_color" in str(exc)
    else:
        raise AssertionError("expected conflicting non-default value to raise")


def test_render_qr_tex_spec_overrides_default_label_text_color():
    spec = QRGridSpec(
        matrices=[
            [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
            [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        ],
        label_text_color="green",
    )

    tex = render_qr_tex(spec=spec, array_names=False)

    assert r"\textcolor{green}" in tex


def test_render_qr_tex_spec_strict_is_not_overridden_by_default_false():
    spec = QRGridSpec(
        matrices=[[None, None, [[1]], [[1]]], [None, [[1]], [[1]], [[1]]]],
        decorators=[{"grid": (0, 2), "entries": [(9, 9)], "decorator": lambda tex: tex}],
        strict=True,
    )

    try:
        render_qr_tex(spec=spec, array_names=False)
    except ValueError as exc:
        assert "decorator selector did not match" in str(exc)
    else:
        raise AssertionError("expected spec strict=True to be honored")
