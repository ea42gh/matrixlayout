from matrixlayout.qr import _mat_shape, _qr_known_zero_entries, _qr_label_layouts, _qr_name_specs_to_callouts
from matrixlayout.qr_spec_merge import (
    qr_known_zero_entries,
    qr_label_layouts,
    qr_name_specs_to_callouts,
)


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

