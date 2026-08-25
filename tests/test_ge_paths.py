# mypy: disable-error-code=arg-type

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


def test_specs_docs_describe_rowechelon_staircase_policy():
    text = __import__("pathlib").Path("docs/specs.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "vertical segments follow the left edge of pivot columns" in normalized
    assert "horizontal segments follow the bottom edge of pivot rows" in normalized
    assert "NiceMatrix projected rule coordinates" in normalized

def test_rowechelon_path_structured_spec_applies_path_offsets():
    matrices = [[None, [[1, 2, 4, 1], [0, "k", 8, "h"], [0, 0, 0, 0]]]]
    paths = rowechelon_paths_from_specs(
        matrices,
        [
            {
                "grid": (0, 1),
                "pivots": [(0, 0), (1, 1)],
                "case": "vh",
                "color": "red",
                "path_offsets": (0.2, -0.05),
            }
        ],
        submatrix_name_style="grid",
    )
    assert paths == [
        r"\draw[red] ($ (1-|A0x1-left) + (0.3,-0.05) $) -- ($ (2-|A0x1-left) + (0.3,-0.05) $) -- ($ (2-|5) + (0.2,-0.05) $) -- ($ (3-|5) + (0.2,-0.05) $) -- ($ (3-|8) + (0.2,-0.05) $);"
    ]
    _assert_no_cell_anchor_path(paths[0])
    _assert_manhattan_path(paths[0])
