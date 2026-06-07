from types import SimpleNamespace

import pytest

from matrixlayout.ge_decorations import normalize_index_list, normalize_range, parse_ge_decorations


def as_2d_list(mat):
    rows = [list(row) for row in mat]
    return rows, len(rows), len(rows[0]) if rows else 0


def grid_line_specs(matrices, *, targets, hlines, vlines, block_align=None, block_valign=None):
    return [("lines", str(targets), f"h={hlines};v={vlines};a={block_align};va={block_valign}")]


def grid_highlight_specs(matrices, *, blocks, block_align=None, block_valign=None):
    return [
        f"highlight {block['grid']} rows={block.get('rows')} cols={block.get('cols')} color={block.get('color')}"
        for block in blocks
    ]


def grid_submatrix_spans(matrices, *, block_align=None, block_valign=None):
    return [
        SimpleNamespace(block_row=0, block_col=0, row_start=10, col_start=20),
        SimpleNamespace(block_row=0, block_col=1, row_start=30, col_start=40),
    ]


def parse(decorations, matrices=None):
    return parse_ge_decorations(
        matrices if matrices is not None else [[[[1, 2], [3, 4]]]],
        decorations,
        as_2d_list=as_2d_list,
        grid_line_specs=grid_line_specs,
        grid_highlight_specs=grid_highlight_specs,
        grid_submatrix_spans=grid_submatrix_spans,
        block_align="c",
        block_valign="m",
    )


def test_normalize_index_list_variants_and_empty_shapes():
    assert normalize_index_list(None, 3) == [0, 1, 2]
    assert normalize_index_list(slice(None, 2), 4) == [0, 1]
    assert normalize_index_list("2:0", 4) == [0, 1, 2]
    assert normalize_index_list(":1", 4) == [0, 1]
    assert normalize_index_list("2:", 4) == [2, 3]
    assert normalize_index_list((3, 1), 5) == [1, 2, 3]
    assert normalize_index_list([2, 2, -1, 99, 0], 3) == [0, 2]
    assert normalize_index_list(1, 3) == [1]
    assert normalize_index_list(3, 3) == []
    assert normalize_index_list(None, 0) == []


def test_normalize_index_list_rejects_invalid_selector():
    with pytest.raises(ValueError, match="rows/cols"):
        normalize_index_list(object(), 3)


def test_normalize_range_empty_and_reversed():
    assert normalize_range([], 3) == (1, 0)
    assert normalize_range((2, 0), 4) == (0, 2)


def test_parse_requires_dict_decorations_and_grid_for_multi_block():
    with pytest.raises(ValueError, match="dict specs"):
        parse(["bad"])

    with pytest.raises(ValueError, match=r"grid=\(row,col\)"):
        parse([{"background": "yellow"}], matrices=[[[1]], [[2]]])

    with pytest.raises(ValueError, match=r"grid=\(row,col\)"):
        parse([{"grid": (0,), "background": "yellow"}])


def test_parse_callout_copies_supported_fields():
    _, _, callouts, codebefore = parse(
        [
            {
                "label": "rank 2",
                "side": "right",
                "angle_deg": -35,
                "length_mm": 8,
                "color": "blue",
                "tip": "Stealth",
                "label_shift_x_mm": 1,
            }
        ]
    )

    assert codebefore == []
    assert callouts == [
        {
            "grid": (0, 0),
            "label": "rank 2",
            "side": "right",
            "angle_deg": -35,
            "length_mm": 8,
            "color": "blue",
            "tip": "Stealth",
            "label_shift_x_mm": 1,
        }
    ]


def test_parse_line_specs_coerces_submatrix_bounds_and_all():
    _, sub_locs, _, _ = parse(
        [
            {"hlines": True, "vlines": "bounds", "submatrix": ("0:1", "0:1")},
            {"hlines": "all", "rows": "0:1", "vlines": "submatrix", "cols": "0:0"},
        ]
    )

    assert len(sub_locs) == 2
    assert "h=2;v=None" in sub_locs[0][2]
    assert "h=[1];v=1" in sub_locs[1][2]


def test_parse_callout_rejects_removed_angle_length_aliases():
    with pytest.raises(TypeError, match="Use angle_deg= and length_mm="):
        parse([{"label": "rank 2", "side": "right", "angle": -35, "length": 8}])


def test_parse_outline_generates_fit_code_for_selected_submatrix():
    _, _, _, codebefore = parse(
        [
            {
                "outline": True,
                "submatrix": ("0:1", "0:0"),
                "color": "red",
                "line_width_pt": 1.5,
                "padding_pt": 2,
            }
        ]
    )

    assert len(codebefore) == 1
    assert "draw=red" in codebefore[0]
    assert "line width=1.5pt" in codebefore[0]
    assert "fit=(10-20-medium) (11-20-medium)" in codebefore[0]


def test_parse_outline_ignores_missing_or_empty_spans():
    _, _, _, codebefore = parse(
        [
            {"grid": (9, 9), "outline": True},
            {"outline": True, "rows": [], "cols": []},
        ]
    )

    assert codebefore == []


def test_parse_background_entries_become_single_cell_highlights():
    _, _, _, codebefore = parse(
        [{"background": "green!15", "entries": [(0, 0), (9, 9)], "padding_pt": 1}]
    )

    assert codebefore == ["highlight (0, 0) rows=(0, 0) cols=(0, 0) color=green!15"]


def test_parse_background_submatrix_rows_and_cols_override():
    _, _, _, codebefore = parse(
        [
            {"background": "yellow", "submatrix": ("0:1", "0:1")},
            {"background": "blue", "rows": [0], "cols": [1]},
        ]
    )

    assert "rows=0:1 cols=0:1 color=yellow" in codebefore[0]
    assert "rows=[0] cols=[1] color=blue" in codebefore[1]


def test_parse_callable_decorator_expands_rows_cols_when_entries_missing():
    def deco(value):
        return value

    dec_specs, _, _, _ = parse([{"decorator": deco, "rows": [0], "cols": [1]}])

    assert dec_specs == [{"grid": (0, 0), "entries": [(0, 1)], "decorator": deco}]


def test_parse_callable_decorator_rejects_noncallable():
    with pytest.raises(ValueError, match="decorator must be callable"):
        parse([{"decorator": "not callable", "entries": [(0, 0)]}])


def test_parse_style_decoration_builds_decorator_for_selected_entries():
    dec_specs, _, _, _ = parse([{"box": "red", "color": "blue", "bold": True, "entries": [(0, 0)]}])

    assert len(dec_specs) == 1
    assert dec_specs[0]["grid"] == (0, 0)
    assert dec_specs[0]["entries"] == [(0, 0)]
    assert callable(dec_specs[0]["decorator"])
    rendered = dec_specs[0]["decorator"]("x")
    assert "\\mathbf{x}" in rendered
    assert "blue" in rendered
    assert "red" in rendered


def test_parse_ignores_decoration_without_action():
    assert parse([{"entries": [(0, 0)]}]) == ([], [], [], [])
