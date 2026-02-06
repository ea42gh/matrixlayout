from matrixlayout import validate_ge_spec, validate_qr_spec


def test_validate_ge_spec_requires_matrices():
    errors = validate_ge_spec({"Nrhs": 1})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_ge_spec_detects_shape_mismatch():
    spec = {"matrices": [[[[1]]], [[[1, 2]]]]}
    errors = validate_ge_spec(spec)
    assert any("shape mismatch" in msg or "row" in msg for msg in errors)


def test_validate_qr_spec_requires_matrices():
    errors = validate_qr_spec({"array_names": True})
    assert any("requires 'matrices'" in msg for msg in errors)


def test_validate_qr_spec_detects_non_rectangular_grid():
    spec = {"matrices": [[[[1]]], [[[1]], [[2]]]]}
    errors = validate_qr_spec(spec)
    assert any("rectangular" in msg for msg in errors)
