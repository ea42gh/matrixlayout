from matrixlayout import validate_ge_spec, validate_qr_spec
from matrixlayout.specs import GEGridSpec, QRGridSpec


def test_validate_ge_spec_requires_matrices():
    errors = validate_ge_spec({"n_rhs": 1})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_ge_spec_detects_shape_mismatch():
    spec = {"matrices": [[[[1]]], [[[1, 2]]]]}
    errors = validate_ge_spec(spec)
    assert any("shape mismatch" in msg or "row" in msg for msg in errors)


def test_validate_ge_spec_checks_nested_label_specs():
    spec = {
        "matrices": [[[[1, 2], [3, 4]]]],
        "label_rows": [{"grid": (0, 0), "side": "left", "labels": [["x"]]}],
        "label_cols": [{"grid": (2, 0), "labels": [["r1"]]}],
    }

    errors = validate_ge_spec(spec)

    assert any("label_rows[0].side" in msg for msg in errors)
    assert any("label_cols[0].grid" in msg and "outside" in msg for msg in errors)


def test_validate_ge_spec_rejects_label_rows_cols_payload_aliases():
    spec = {
        "matrices": [[[[1, 2], [3, 4]]]],
        "label_rows": [{"grid": (0, 0), "side": "above", "rows": [["x"]]}],
        "label_cols": [{"grid": (0, 0), "side": "left", "cols": [["r1"]]}],
    }

    errors = validate_ge_spec(spec)

    assert any("label_rows[0] has unknown field" in msg and "rows" in msg for msg in errors)
    assert any("label_rows[0] must include 'labels'" in msg for msg in errors)
    assert any("label_cols[0] has unknown field" in msg and "cols" in msg for msg in errors)
    assert any("label_cols[0] must include 'labels'" in msg for msg in errors)


def test_validate_ge_spec_checks_nested_decorations():
    spec = {
        "matrices": [[[[1]], [[2]]]],
        "decorations": [
            {"entries": [(0, 0)], "background": "yellow!40"},
            {"grid": (0, 1), "decorator": "not callable"},
            {"grid": (0, 9), "background": "yellow!40", "typo": True},
        ],
    }

    errors = validate_ge_spec(spec)

    assert any("requires grid" in msg for msg in errors)
    assert any("decorator must be callable" in msg for msg in errors)
    assert any("unknown field" in msg for msg in errors)
    assert any("outside" in msg for msg in errors)


def test_validate_ge_spec_rejects_decoration_label_shorthand():
    spec = {
        "matrices": [[[[1]]]],
        "decorations": [{"grid": (0, 0), "label": "A", "side": "right"}],
    }

    errors = validate_ge_spec(spec, strict=True)

    assert any("decorations[0] has unknown field" in msg and "label" in msg for msg in errors)
    assert any("decorations[0] has unknown field" in msg and "side" in msg for msg in errors)


def test_validate_ge_spec_accepts_typed_grid_spec():
    spec = GEGridSpec(
        matrices=[[[[1, 2], [3, 4]]]],
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["x", "y"]]}],
        decorations=[{"grid": (0, 0), "entries": [(0, 0)], "background": "yellow!40"}],
    )

    assert validate_ge_spec(spec) == []


def test_validate_ge_spec_rejects_non_mapping_or_typed_spec():
    errors = validate_ge_spec(["not", "a", "spec"])

    assert errors == ["GE spec must be a mapping or typed spec object"]


def test_ge_gridspec_from_dict_shared_filtering_rules():
    assert GEGridSpec.from_dict({"matrices": [[1]], "strict": False, "unknown": 1}).matrices == [[1]]

    try:
        GEGridSpec.from_dict({"matrices": [[1]], "strict": True, "unknown": 1})
    except ValueError as exc:
        assert "Unknown GEGridSpec fields" in str(exc)
    else:
        raise AssertionError("expected unknown strict GEGridSpec field to raise")

    try:
        GEGridSpec.from_dict(None)
    except ValueError as exc:
        assert "GEGridSpec.from_dict requires a mapping" in str(exc)
    else:
        raise AssertionError("expected GEGridSpec.from_dict(None) to raise")


def test_validate_qr_spec_requires_matrices():
    errors = validate_qr_spec({"array_names": True})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_qr_spec_detects_non_rectangular_grid():
    spec = {"matrices": [[[[1]]], [[[1]], [[2]]]]}
    errors = validate_qr_spec(spec)
    assert any("rectangular" in msg for msg in errors)


def test_validate_qr_spec_checks_annotations_are_mappings():
    spec = {"matrices": [[[[1]]]], "annotations": ["not a mapping"]}
    errors = validate_qr_spec(spec)

    assert any("annotations[0] must be a mapping" in msg for msg in errors)


def test_validate_qr_spec_rejects_string_annotations():
    spec = {"matrices": [[[[1]]]], "annotations": "not a sequence of mappings"}
    errors = validate_qr_spec(spec)

    assert any("annotations must be a sequence of mappings" in msg for msg in errors)


def test_validate_qr_spec_checks_nested_annotations_and_decorators():
    spec = {
        "matrices": [[[[1]], [[2]]]],
        "annotations": [
            {"grid": (0, 9), "labels": ["bad"], "side": "diagonal"},
            {"entries": [(0, 0)], "background": "yellow!40"},
            {"grid": (0, 1), "labels": ["ok"], "typo": True},
        ],
        "decorators": [
            {"grid": (0, 1), "entries": [(0, 0)], "decorator": "not callable"},
        ],
    }

    errors = validate_qr_spec(spec)

    assert any("annotations[0].grid" in msg and "outside" in msg for msg in errors)
    assert any("annotations[0].side" in msg for msg in errors)
    assert any("annotations[1] requires grid" in msg for msg in errors)
    assert any("annotations[1] must include 'labels'" in msg for msg in errors)
    assert any("annotations[2] has unknown field" in msg for msg in errors)
    assert any("decorators[0].decorator must be callable" in msg for msg in errors)


def test_validate_qr_spec_accepts_typed_grid_spec():
    spec = QRGridSpec(
        matrices=[[[[1, 0], [0, 1]]]],
        callouts=[{"name": "M-0-0", "label": "A", "side": "right"}],
        annotations=[
            {"grid": (0, 0), "side": "above", "labels": ["x_1", "x_2"]},
        ],
    )

    assert validate_qr_spec(spec) == []


def test_validate_qr_spec_rejects_string_callouts():
    spec = {"matrices": [[[[1]]]], "callouts": "not a sequence of mappings"}
    errors = validate_qr_spec(spec)

    assert any("callouts must be a sequence of mappings" in msg for msg in errors)


def test_validate_qr_spec_rejects_decoration_actions_as_annotations():
    spec = {
        "matrices": [[[[1, 0], [0, 1]]]],
        "annotations": [{"grid": (0, 0), "entries": [(0, 0)], "background": "yellow!40"}],
    }

    errors = validate_qr_spec(spec)

    assert any("annotations[0] has unknown field" in msg and "background" in msg for msg in errors)
    assert any("annotations[0] must include 'labels'" in msg for msg in errors)


def test_qr_gridspec_from_dict_shared_filtering_rules():
    assert QRGridSpec.from_dict({"matrices": [[1]], "strict": False, "unknown": 1}).matrices == [[1]]

    try:
        QRGridSpec.from_dict({"matrices": [[1]], "strict": True, "unknown": 1})
    except ValueError as exc:
        assert "Unknown QRGridSpec fields" in str(exc)
    else:
        raise AssertionError("expected unknown strict QRGridSpec field to raise")

    try:
        QRGridSpec.from_dict(None)
    except ValueError as exc:
        assert "QRGridSpec.from_dict requires a mapping" in str(exc)
    else:
        raise AssertionError("expected QRGridSpec.from_dict(None) to raise")
