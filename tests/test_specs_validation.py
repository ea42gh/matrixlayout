from matrixlayout import validate_ge_spec, validate_qr_spec


def test_validate_ge_spec_requires_matrices():
    errors = validate_ge_spec({"Nrhs": 1})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_ge_spec_detects_shape_mismatch():
    spec = {"matrices": [[[[1]]], [[[1, 2]]]]}
    errors = validate_ge_spec(spec)
    assert any("shape mismatch" in msg or "row" in msg for msg in errors)


def test_validate_ge_spec_checks_nested_label_specs():
    spec = {
        "matrices": [[[[1, 2], [3, 4]]]],
        "label_rows": [{"grid": (0, 0), "side": "left", "rows": [["x"]]}],
        "label_cols": [{"grid": (2, 0), "cols": [["r1"]]}],
    }

    errors = validate_ge_spec(spec)

    assert any("label_rows[0].side" in msg for msg in errors)
    assert any("label_cols[0].grid" in msg and "outside" in msg for msg in errors)


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


def test_validate_qr_spec_requires_matrices():
    errors = validate_qr_spec({"array_names": True})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_qr_spec_detects_non_rectangular_grid():
    spec = {"matrices": [[[[1]]], [[[1]], [[2]]]]}
    errors = validate_qr_spec(spec)
    assert any("rectangular" in msg for msg in errors)


def test_validate_qr_spec_checks_specs_are_mappings():
    spec = {"matrices": [[[[1]]]], "specs": ["not a mapping"]}
    errors = validate_qr_spec(spec)

    assert any("specs[0] must be a mapping" in msg for msg in errors)
