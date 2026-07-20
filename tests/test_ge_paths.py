import re

from matrixlayout.ge_paths import rowechelon_paths_from_specs


def _path_anchor_keys(path):
    out = []
    for row, col in re.findall(r"\((\d+)-\|([A-Za-z0-9_-]+)\)", path):
        col_key = int(col) if col.isdigit() else col
        out.append(((int(row), "rule"), (col_key, "rule")))
    for row, col, anchor in re.findall(r"\((\d+)-(\d+)\.([a-z ]+)\)", path):
        parts = set(anchor.split())
        vertical = "north" if "north" in parts else "south" if "south" in parts else "center"
        horizontal = "west" if "west" in parts else "east" if "east" in parts else "center"
        out.append(((int(row), vertical), (int(col), horizontal)))
    return out


def _assert_manhattan_path(path):
    keys = _path_anchor_keys(path)
    assert len(keys) >= 2
    for prev, cur in zip(keys, keys[1:], strict=False):
        row_changes = prev[0] != cur[0]
        col_changes = prev[1] != cur[1]
        assert not (row_changes and col_changes), path


def _assert_no_cell_anchor_path(path):
    assert ".north" not in path
    assert ".south" not in path
    assert ".east" not in path
    assert ".west" not in path


def test_ge_paths_does_not_expose_legacy_tuple_alias():
    import matrixlayout.ge_paths as ge_paths

    assert not hasattr(ge_paths, "rowechelon_paths_from_legacy_tuples")


def test_rowechelon_paths_use_left_bottom_staircase_for_all_cases():
    matrices = [[None, [[1, 2, 4, 1], [0, "k", 8, "h"], [0, 0, 0, 0]]]]
    pivots = [(0, 0), (1, 1)]
    expected = {
        "hh": r"\draw[red] ($ (2-|A0x1-left) + (0.1,0) $) -- (2-|5) -- (3-|5) -- (3-|8);",
        "vh": r"\draw[red] ($ (1-|A0x1-left) + (0.1,0) $) -- ($ (2-|A0x1-left) + (0.1,0) $) -- (2-|5) -- (3-|5) -- (3-|8);",
        "vv": r"\draw[red] ($ (1-|A0x1-left) + (0.1,0) $) -- ($ (2-|A0x1-left) + (0.1,0) $) -- (2-|5) -- (4-|5);",
        "hv": r"\draw[red] ($ (2-|A0x1-left) + (0.1,0) $) -- (2-|5) -- (4-|5);",
    }
    for case, path in expected.items():
        paths = rowechelon_paths_from_specs(
            matrices,
            [{"grid": (0, 1), "pivots": pivots, "case": case, "color": "red"}],
            legacy_submatrix_names=True,
        )
        assert paths == [path]
        _assert_no_cell_anchor_path(paths[0])
        _assert_manhattan_path(paths[0])


def test_rowechelon_paths_single_pivot_first_column_uses_matrix_left_edge():
    matrices = [[None, [[1, 2], [3, 4]]], [[[1, 0], [0, 1]], [[1, 2], [3, 4]]]]
    paths = rowechelon_paths_from_specs(
        matrices,
        [{"grid": (0, 1), "pivots": [(0, 0)], "case": "vv"}],
        legacy_submatrix_names=True,
    )
    assert paths == [r"\draw[blue,line width=0.4mm] ($ (1-|A0x1-left) + (0.1,0) $) -- ($ (3-|A0x1-left) + (0.1,0) $);"]
    _assert_manhattan_path(paths[0])


def test_rowechelon_paths_single_pivot_nonfirst_column_uses_column_left_edge():
    matrices = [[None, [[1, 2, 4, 1], [0, "k", 8, "h"], [0, 0, 0, 0]]]]
    paths = rowechelon_paths_from_specs(
        matrices,
        [{"grid": (0, 1), "pivots": [(0, 2)], "case": "vv"}],
        legacy_submatrix_names=True,
    )
    assert paths == [r"\draw[blue,line width=0.4mm] (1-|6) -- (4-|6);"]
    _assert_manhattan_path(paths[0])


def test_rowechelon_path_structured_spec_applies_node_offsets():
    matrices = [[None, [[1, 2, 4, 1], [0, "k", 8, "h"], [0, 0, 0, 0]]]]
    paths = rowechelon_paths_from_specs(
        matrices,
        [
            {
                "grid": (0, 1),
                "pivots": [(0, 0), (1, 1)],
                "case": "vh",
                "color": "red",
                "node_offsets": (0.2, -0.05),
            }
        ],
        legacy_submatrix_names=True,
    )
    assert paths == [
        r"\draw[red] ($ (1-|A0x1-left) + (0.3,-0.05) $) -- ($ (2-|A0x1-left) + (0.3,-0.05) $) -- ($ (2-|5) + (0.2,-0.05) $) -- ($ (3-|5) + (0.2,-0.05) $) -- ($ (3-|8) + (0.2,-0.05) $);"
    ]
    _assert_no_cell_anchor_path(paths[0])
    _assert_manhattan_path(paths[0])
