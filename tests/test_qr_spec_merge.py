from matrixlayout.qr import (
    _mat_shape,
    _callout_rules,
    _known_zero_entries,
    _label_layouts,
)
from matrixlayout.qr import render_qr_tex
from matrixlayout.qr_spec_merge import (
    coerce_qr_spec,
    filter_qr_name_specs,
    merge_scalar_default,
    merge_scalar,
    qr_callout_rules,
    qr_default_name_specs,
    qr_known_zero_entries,
    qr_label_layouts,
    qr_name_specs_to_callouts,
)
from matrixlayout.specs import QRGridSpec


def test_qr_known_zero_entries_matches_qr_local_shape_adapter():
    grid = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 0], [2, 3]], [[1, 0], [0, 1]]],
    ]
    assert qr_known_zero_entries(grid, mat_shape=_mat_shape) == _known_zero_entries(grid)


def test_qr_known_zero_entries_handles_short_malformed_and_zero_shapes():
    assert qr_known_zero_entries([], mat_shape=_mat_shape) == []
    assert qr_known_zero_entries([[None]], mat_shape=_mat_shape) == []
    assert qr_known_zero_entries([[None], [None, None]], mat_shape=_mat_shape) == []
    assert qr_known_zero_entries(
        [[None, None, [[1]], [[1]]], [None, [[1]], [], []]],
        mat_shape=_mat_shape,
    ) == []


def test_qr_label_layouts_matches_qr_local_shape_adapter():
    grid = [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]], [None, [[1, 0], [0, 1]]]]
    assert qr_label_layouts(grid, "red", mat_shape=_mat_shape) == _label_layouts(grid, "red")


def test_filter_qr_name_specs_filters_invalid_entries():
    grid = [[None, None, [[1]], None], [None, [[1]]]]
    specs = [
        "bad",
        [(0,), "al", "bad-grid"],
        [(0, 0), "al", "empty"],
        [(0, 2), "al", "A"],
        [(1, 1), "br", "B"],
        [(4, 1), "br", "outside"],
    ]

    assert filter_qr_name_specs(specs, grid=grid) == [[(0, 2), "al", "A"], [(1, 1), "br", "B"]]


def test_qr_callout_rules_matches_qr_local_adapter():
    assert qr_callout_rules(a_rows=2, a_cols=2) == _callout_rules(a_rows=2, a_cols=2)


def test_qr_callout_rules_adjust_compact_a_block():
    label_shift_rules, length_rules = qr_callout_rules(a_rows=3, a_cols=2)

    assert (r"\mathbf{R = S W^T A}", -2.0) in label_shift_rules
    assert length_rules == [(r"\mathbf{Q^T = S W^T}", 14.0)]


def test_qr_callout_rules_default_width_uses_default_r_shift():
    label_shift_rules, length_rules = qr_callout_rules(a_rows=3, a_cols=4)

    assert (r"\mathbf{R = S W^T A}", -1.0) in label_shift_rules
    assert length_rules == []


def test_merge_scalar_default_lets_spec_override_renderer_default():
    assert merge_scalar_default("label_color", "blue", "green", "blue") == "green"


def test_merge_scalar_default_rejects_non_default_conflict():
    try:
        merge_scalar_default("label_color", "purple", "green", "blue")
    except ValueError as exc:
        assert "Conflicting values for label_color" in str(exc)
    else:
        raise AssertionError("expected conflicting non-default value to raise")


def test_merge_scalar_base_cases_and_conflict():
    assert merge_scalar("x", "explicit", None) == "explicit"
    assert merge_scalar("x", None, "spec") == "spec"
    assert merge_scalar("x", "same", "same") == "same"
    try:
        merge_scalar("x", "explicit", "spec")
    except ValueError as exc:
        assert "Conflicting values for x" in str(exc)
    else:
        raise AssertionError("expected merge conflict")


def test_coerce_qr_spec_accepts_none_object_and_dict():
    spec = QRGridSpec(matrices=[[None]])

    assert coerce_qr_spec(None) is None
    assert coerce_qr_spec(spec) is spec
    assert coerce_qr_spec({"matrices": [[None]], "strict": False}).matrices == [[None]]


def test_qr_label_layouts_handles_shape_failure():
    def bad_shape(_mat):
        raise TypeError("bad shape")

    assert qr_label_layouts([[None, None, object()]], "red", mat_shape=bad_shape) == ([], [])

def test_qr_name_specs_to_callouts_filters_invalid_and_applies_rules():
    callouts = qr_name_specs_to_callouts(
        [
            "bad",
            [(0,), "al", "bad-grid"],
            [(0, 1), "unknown", r"\mathbf{Q^T = S W^T}"],
            [(0, 2), "br", r"\mathbf{A}"],
        ],
        color="orange",
        label_shift_rules=[(r"\mathbf{Q^T", 2.5)],
        length_rules=[(r"\mathbf{A}", 9.0)],
    )

    assert len(callouts) == 2
    assert callouts[0]["side"] == "right"
    assert callouts[0]["anchor"] == "center"
    assert callouts[0]["angle_deg"] == 40.0
    assert callouts[0]["label_shift_mm"] == (0.0, 2.5)
    assert callouts[1]["length_mm"] == 9.0

def test_qr_default_name_specs_shape():
    specs = qr_default_name_specs()

    assert specs
    assert all(len(spec) == 3 for spec in specs)


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


def test_render_qr_tex_accepts_annotations():
    annotations = [{"grid": (0, 2), "side": "above", "labels": ["x"]}]

    tex = render_qr_tex(
        matrices=[[None, None, [[1]], [[1]]], [None, [[1]], [[1]], [[1]]]],
        annotations=annotations,
        array_names=False,
    )

    assert r"\text{x}" in tex


def test_qr_grid_spec_accepts_annotations():
    annotations = [{"grid": (0, 2), "side": "above", "labels": ["x"]}]

    spec = QRGridSpec.from_dict(
        {
            "matrices": [[None, None, [[1]], [[1]]], [None, [[1]], [[1]], [[1]]]],
            "annotations": annotations,
        }
    )

    assert spec.annotations == annotations


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
