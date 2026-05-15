from matrixlayout.qr import (
    QRGridLayout,
    _as_grid,
    _cumsum,
    _make_decorator,
    _mat_entry,
    _mat_shape,
    _set_extra,
    resolve_qr_grid_name,
)


class ShapeOnly:
    shape = ("2", "3")


class BadShape:
    shape = object()


class TupleIndexMatrix:
    shape = (2, 2)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            i, j = key
            return f"T{i}{j}"
        raise TypeError


def test_qr_private_grid_and_shape_helpers():
    assert _as_grid(None) == []
    assert _as_grid([[1, 2], 3]) == [[1, 2], [3]]
    assert _as_grid("A") == [[None, "A"]]

    assert _mat_shape(None) == (0, 0)
    assert _mat_shape(ShapeOnly()) == (2, 3)
    assert _mat_shape(BadShape()) == (0, 0)
    assert _mat_shape([[1, 2], [3, 4]]) == (2, 2)
    assert _mat_shape([1, 2]) == (0, 0)

    assert _mat_entry(TupleIndexMatrix(), 1, 0) == "T10"
    assert _mat_entry([[1, 2], [3, 4]], 1, 1) == 4
    assert _mat_entry(None, 0, 0) == ""


def test_qr_private_spacing_helpers():
    assert _set_extra(None, 2) == [0, 0, 0]
    assert _set_extra(3, 2) == [0, 0, 3]
    assert _set_extra([1, 2, 3], 2) == [1, 2, 3]
    assert _cumsum([1, 2, 3]) == [1, 3, 6]


def test_qr_make_decorator_composes_all_options():
    decorate = _make_decorator(
        text_color="red",
        bg_color="yellow",
        text_bg="blue!10",
        boxed=True,
        box_color="green",
        bf=True,
        move_right=True,
        delim="|",
    )

    rendered = decorate("x")
    assert r"\mathrlap" in rendered
    assert r"\Block[draw=red,fill=blue!10]" in rendered
    assert r"\colorbox{yellow}" in rendered
    assert r"\colorboxed{green}" in rendered
    assert r"\boxed" in rendered
    assert r"\mathbf{x}" in rendered
    assert rendered.startswith("{|")
    assert rendered.endswith("|}")


def test_qr_grid_layout_positions_entries_and_formats():
    layout = QRGridLayout(
        [
            [None, [[1, 2], [3, 4]]],
            [[[5], [6], [7]], [[8]]],
        ],
        extra_rows=[1, 2, 1],
        extra_cols=[1, 1, 2],
    )

    assert layout.nGridRows == 2
    assert layout.nGridCols == 2
    assert layout.mat_row_height == [2, 3]
    assert layout.mat_col_width == [1, 2]
    assert layout.tex_shape == (9, 7)

    assert layout._top_left_bottom_right(0, 1) == ((1, 3), (2, 4), (2, 2))
    assert layout._top_left_bottom_right(1, 0) == ((5, 1), (7, 1), (3, 1))
    assert layout._top_left_bottom_right(1, 1) == ((7, 4), (7, 4), (1, 1))

    layout.array_format_string_list(partitions={1: [1]}, spacer_string="|", p_str=":", last_col_format="L")
    assert layout.format == "r|r|r|r:r|rL"

    layout.array_of_tex_entries(formatter=lambda x: f"<{x}>")
    assert layout.a_tex[1][3] == "<1>"
    assert layout.a_tex[2][4] == "<4>"
    assert layout.a_tex[5][1] == "<5>"
    assert layout.a_tex[7][4] == "<8>"

    layout.decorate_tex_entries(0, 1, lambda s: f"[{s}]", entries=[(0, 0)])
    assert layout.a_tex[1][3] == "[<1>]"
    layout.decorate_tex_entries(9, 9, lambda s: f"!{s}!")

    layout.add_row_above(0, 1, ["a", "b"], formatter=str)
    assert layout.a_tex[0][3:5] == ["a", "b"]
    layout.add_col_left(1, 0, ["r1", "r2"], formatter=str, offset=1)
    assert layout.a_tex[5][0] == "r1"
    assert layout.a_tex[6][0] == "r2"


def test_qr_grid_layout_submatrix_locs_names_and_tex_repr():
    layout = QRGridLayout(
        [
            [None, [[1, 2], [3, 4]]],
            [[[5], [6]], [[7, 8]]],
        ],
        extra_rows=1,
        extra_cols=1,
    )
    layout.array_of_tex_entries(formatter=str)
    layout.nm_submatrix_locs(
        name="Q",
        color="purple",
        line_specs=[((0, 1), [1], 1), ((1, 0), 1, [1])],
        name_specs=[
            ((0, 1), "a", "top"),
            ((0, 1), "al", "top-left"),
            ((0, 1), "ar", "top-right"),
            ((1, 0), "b", "bottom"),
            ((1, 0), "bl", "bottom-left"),
            ((1, 0), "br", "bottom-right"),
            ((1, 1), "unknown", "ignored"),
        ],
    )

    assert ["name=Q0x1,hlines={1},vlines=1", "{1-2}{2-3}"] in layout.locs
    assert ["name=Q1x0,hlines=1,vlines={1}", "{3-1}{4-1}"] in layout.locs
    assert len(layout.array_names) == 6
    assert all("purple" in item for item in layout.array_names)

    layout.tex_repr(blockseps=" <gap> ")
    assert layout.tex_list
    assert any("<gap>" in line for line in layout.tex_list)


def test_qr_grid_layout_matrix_format_partitions():
    assert QRGridLayout.matrix_array_format(3) == "rrr"
    assert QRGridLayout.matrix_array_format(4, p_str="|", vpartitions=[1, 3]) == "r|rr|r"


def test_qr_grid_layout_decorate_all_entries():
    layout = QRGridLayout([[[[1, 2], [3, 4]]]])
    layout.array_of_tex_entries(formatter=str)
    layout.decorate_tex_entries(0, 0, lambda s: f"({s})")
    assert layout.a_tex == [["(1)", "(2)"], ["(3)", "(4)"]]


def test_qr_grid_layout_add_row_without_extra_rows_uses_python_negative_indexing():
    layout = QRGridLayout([[[[1]]]], extra_rows=0, extra_cols=0)
    layout.array_of_tex_entries(formatter=str)

    layout.add_row_above(0, 0, ["x"])
    assert layout.a_tex == [["x"]]


def test_resolve_qr_grid_name_rejects_non_strings_and_parses_fallback():
    matrices = [[None, [[1]]]]

    assert resolve_qr_grid_name(None, matrices=matrices) is None
    assert resolve_qr_grid_name("QR0x1", matrices=matrices) == (0, 1)
    assert resolve_qr_grid_name("A12x34", matrices=matrices) == (12, 34)
    assert resolve_qr_grid_name("not-a-grid-name", matrices=matrices) is None
