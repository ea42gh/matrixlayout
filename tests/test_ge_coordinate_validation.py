from matrixlayout import validate_ge_spec


def test_validate_ge_coordinate_specs_accepts_valid_targets():
    spec = {
        "matrices": [
            [None, [[1, 2], [3, 4]]],
            [[[1, 0], [0, 1]], [[5, 6], [7, 8]]],
        ],
        "pivot_locs": [
            {"grid": (0, 1), "entries": [(0, 0)]},
            {"grid": (1, 1), "entries": [(0, 0), (1, 1)]},
        ],
        "rowechelon_paths": [
            {"grid": (1, 1), "pivots": [(0, 0), (1, 1)], "case": "vh"},
        ],
    }

    assert validate_ge_spec(spec) == []


def test_validate_ge_coordinate_specs_reports_invalid_targets():
    spec = {
        "matrices": [[[[1, 2], [3, 4]]]],
        "pivot_locs": [
            {"grid": (0, 1), "entries": [(0, 0)]},
            {"grid": (0, 0), "entries": [(2, 0)]},
        ],
        "rowechelon_paths": [
            {"grid": (0, 0), "pivots": [(0, 0)], "case": "diagonal"},
        ],
    }

    errors = validate_ge_spec(spec)

    assert any("pivot_locs[0].grid" in msg and "outside" in msg for msg in errors)
    assert any("pivot_locs[1].entries[0]" in msg and "outside" in msg for msg in errors)
    assert any("rowechelon_paths[0].case" in msg for msg in errors)