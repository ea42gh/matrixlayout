from matrixlayout.ge_grid import grid_block_padding
from matrixlayout.ge_render_grid import build_ge_grid_render_parts


def _parts(matrices, **kwargs):
    grid, cell_cache, block_heights, block_widths, _pad_left, _pad_top = grid_block_padding(
        matrices,
        block_align=kwargs.pop("block_align", None),
        block_valign=kwargs.pop("block_valign", None),
    )
    return build_ge_grid_render_parts(
        grid=grid,
        cell_cache=cell_cache,
        block_heights=block_heights,
        block_widths=block_widths,
        n_rhs=kwargs.pop("n_rhs", 0),
        formatter=kwargs.pop("formatter", str),
        outer_hspace_mm=kwargs.pop("outer_hspace_mm", 6),
        block_vspace_mm=kwargs.pop("block_vspace_mm", 1),
        cell_align=kwargs.pop("cell_align", "r"),
        block_align=kwargs.pop("block_align_render", None),
        block_valign=kwargs.pop("block_valign_render", None),
        format_nrhs=kwargs.pop("format_nrhs", True),
        label_rows=kwargs.pop("label_rows", None),
        label_cols=kwargs.pop("label_cols", None),
        label_gap_mm=kwargs.pop("label_gap_mm", 0.8),
        variable_labels=kwargs.pop("variable_labels", None),
        decorator_map=kwargs.pop("decorator_map", None),
        strict=kwargs.pop("strict", False),
        legacy_format=kwargs.pop("legacy_format", False),
        legacy_submatrix_names=kwargs.pop("legacy_submatrix_names", False),
        user_submatrix_locs=kwargs.pop("user_submatrix_locs", None),
    )


def test_ge_render_parts_basic_grid_nrhs_names_and_spans():
    matrices = [
        [None, [[1, 2, 3], [4, 5, 6]]],
        [[[1, 0], [0, 1]], [[1, 0, 0], [0, 1, 0]]],
    ]

    parts = _parts(matrices, n_rhs=1)

    assert parts.mat_format == r"rr@{\hspace{6mm}}rr|r"
    assert r"\NotEmpty & \NotEmpty & 1 & 2 & 3 \\" in parts.mat_rep
    assert parts.submatrix_locs == [
        ("name=A0", "1-3", "2-5"),
        ("name=E1", "3-1", "4-2"),
        ("name=A1", "3-3", "4-5"),
    ]
    assert parts.name_map == {(0, 1): "A0", (1, 0): "E1", (1, 1): "A1"}


def test_ge_render_parts_labels_and_label_gap():
    parts = _parts(
        [[[1, 0, 2], [0, 1, -1]]],
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["x_1", "$x_2$", "b"]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [["r1"], ["r2"]]}],
    )

    assert parts.mat_format == "rrrr"
    assert r"\text{x\_1} & x_2 & \text{b} \\\noalign{\vskip0.8mm}" in parts.mat_rep
    assert r"\text{r1}\hspace{0.8mm} & 1 & 0 & 2 \\" in parts.mat_rep
    assert parts.submatrix_locs == [("name=M00", "2-2", "3-4")]


def test_ge_render_parts_list_nrhs_legacy_format_and_user_submatrix_locs():
    parts = _parts(
        [[[1, 2, 3, 4]]],
        n_rhs=[1, 1],
        legacy_format=True,
        cell_align="c",
        user_submatrix_locs=[("name=extra", "9-9", "10-10")],
    )

    assert parts.mat_format == r"@{\hspace{6mm}}ccIcIc"
    assert parts.submatrix_locs == [
        ("name=M00", "1-1", "1-4"),
        ("name=extra", "9-9", "10-10"),
    ]


def test_ge_render_parts_list_nrhs_current_format_without_legacy_separator():
    parts = _parts(
        [[[1, 2, 3, 4, 5]]],
        n_rhs=[1, 2],
        cell_align="c",
    )

    assert parts.mat_format == "cc|c|cc"


def test_ge_render_parts_ignores_invalid_nrhs_partition_width():
    parts = _parts(
        [[[1, 2]]],
        n_rhs=2,
    )

    assert parts.mat_format == "rr"


def test_ge_render_parts_legacy_names_and_block_alignment():
    matrices = [
        [[[1]], [[1, 2], [3, 4]]],
    ]
    parts = _parts(
        matrices,
        block_align="right",
        block_valign="bottom",
        block_align_render="right",
        block_valign_render="bottom",
        legacy_submatrix_names=True,
    )

    assert parts.submatrix_locs == [
        ("name=A0x0", "2-1", "2-1"),
        ("name=A0x1", "1-2", "2-3"),
    ]
    assert parts.name_map == {(0, 0): "A0x0", (0, 1): "A0x1"}


def test_ge_render_parts_center_alignment_offsets_submatrix_span_and_body():
    matrices = [
        [[[1]]],
        [[[1, 2, 3]]],
    ]
    parts = _parts(
        matrices,
        block_align="center",
        block_align_render="center",
    )

    assert r"\NotEmpty & 1 & \NotEmpty \\" in parts.mat_rep
    assert r"1 & 2 & 3 \\" in parts.mat_rep
    assert parts.submatrix_locs == [
        ("name=M00", "1-2", "1-2"),
        ("name=M01", "2-1", "2-3"),
    ]


def test_ge_render_parts_three_column_submatrix_names_are_column_indexed():
    parts = _parts(
        [
            [[[1]], [[2]], [[3]]],
        ],
    )

    assert parts.submatrix_locs == [
        ("name=M00", "1-1", "1-1"),
        ("name=M10", "1-2", "1-2"),
        ("name=M20", "1-3", "1-3"),
    ]
    assert parts.name_map == {(0, 0): "M00", (0, 1): "M10", (0, 2): "M20"}


def test_ge_render_parts_decorator_map_applies_entry_formatter_and_decorator():
    def dec(i, j, value, tex):
        return f"D({i},{j},{value},{tex})"

    parts = _parts(
        [[[1, 2]]],
        decorator_map={(0, 0): [(dec, {(0, 1)}, lambda value: f"f{value}")]},
    )

    assert "1 & D(0,1,2,f2)" in parts.mat_rep
