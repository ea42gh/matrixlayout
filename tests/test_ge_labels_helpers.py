from matrixlayout.ge_labels import append_variable_labels
from matrixlayout.ge_labels import blank_label_specs
from matrixlayout.ge_labels import build_label_maps
from matrixlayout.ge_labels import compute_label_extras
from matrixlayout.ge_labels import embed_col_labels
from matrixlayout.ge_labels import embed_row_labels
from matrixlayout.ge_labels import escape_label_text_segment
from matrixlayout.ge_labels import grid_label_layouts
from matrixlayout.ge_labels import annotation_label_specs
from matrixlayout.ge_labels import merge_label_specs
from matrixlayout.ge_labels import normalize_label_cols
from matrixlayout.ge_labels import normalize_label_rows
from matrixlayout.ge_labels import split_label_dollar_segments


def test_label_text_escaping_and_dollar_segments():
    assert escape_label_text_segment(r"a_b & c%") == r"a\_b \& c\%"
    assert split_label_dollar_segments("row $i$ col $j$") == r"\text{row }i\text{ col }j"
    assert split_label_dollar_segments("no math") is None
    assert split_label_dollar_segments("bad $math") is None


def test_grid_label_layouts_filters_invalid_sides():
    rows, cols = grid_label_layouts(
        [
            "bad",
            {"grid": (0,), "labels": ["skip"]},
            {"grid": (0, 0), "side": "above", "labels": [[("name", "x"), {"text": "y"}]]},
            {"grid": (0, 1), "side": "below", "labels": [["b1", "b2"]]},
            {"grid": (1, 0), "side": "left", "labels": "row"},
            {"grid": (1, 1), "side": "right", "labels": [["r1"], ["r2"]]},
            {"grid": (2, 0), "side": "top", "labels": ["skip"]},
            {"grid": (2, 1), "side": "bottom", "labels": ["skip"]},
            {"grid": (2, 2), "side": "diagonal", "labels": ["skip"]},
        ]
    )

    assert rows == [
        {"grid": (0, 0), "side": "above", "labels": [["x", "y"]]},
        {"grid": (0, 1), "side": "below", "labels": [["b1", "b2"]]},
    ]
    assert cols == [
        {"grid": (1, 0), "side": "left", "labels": [["row"]]},
        {"grid": (1, 1), "side": "right", "labels": [["r1"], ["r2"]]},
    ]


def test_annotation_label_specs_uses_labels_and_filters_invalid():
    label_specs = annotation_label_specs(
        [
            {"grid": (0, 0), "side": "above", "labels": [["r"]], "extra": 1},
            {"grid": (0, 1), "side": "left", "labels": [["c"]]},
            {"grid": (1, 0), "side": "below", "labels": [["b"]]},
            {"grid": (1, 3), "side": "bottom", "labels": [["skip"]]},
            {"grid": (1, 1), "side": "above", "rows": [["skip"]]},
            {"grid": (1, 2), "side": "left", "cols": [["skip"]]},
            {"grid": (1,), "labels": ["skip"]},
            {"grid": (2, 0)},
        ]
    )

    assert label_specs == [
        {"grid": (0, 0), "side": "above", "extra": 1, "labels": [["r"]]},
        {"grid": (0, 1), "side": "left", "labels": [["c"]]},
        {"grid": (1, 0), "side": "below", "labels": [["b"]]},
    ]


def test_blank_label_specs_replaces_list_values_only():
    specs = [
        {"rows": [["x", "y"], "z"]},
        {"rows": "unchanged"},
    ]

    out = blank_label_specs(specs, "rows")

    assert out[0]["rows"] == [[{"text": r"\NotEmpty"}, {"text": r"\NotEmpty"}], [{"text": r"\NotEmpty"}]]
    assert out[1]["rows"] == "unchanged"
    assert specs[0]["rows"][0][0] == "x"


def test_normalize_label_rows_and_cols_shapes():
    assert normalize_label_rows(None) == []
    assert normalize_label_rows(["x", "y"]) == [["x", "y"]]
    assert normalize_label_rows(["x", ["y", "z"]]) == [["x"], ["y", "z"]]
    assert normalize_label_rows("x") == [["x"]]

    assert normalize_label_cols(None) == []
    assert normalize_label_cols(["x", "y"]) == [["x", "y"]]
    assert normalize_label_cols([["x"], ["y"]]) == [["x", "y"]]
    assert normalize_label_cols(["x", ["y", "z"]]) == [["x"], ["y", "z"]]
    assert normalize_label_cols("x") == [["x"]]


def test_merge_label_specs_replaces_blank_rows_and_cols_then_appends_extras():
    label_rows, label_cols, decorations = merge_label_specs(
        annotations=[
            {"grid": (0, 0), "side": "above", "labels": [["spec1"], ["spec2"]]},
            {"grid": (0, 0), "side": "left", "labels": [["col1"], ["col2"]]},
        ],
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [[{"text": r"\NotEmpty"}]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [[{"text": r"\NotEmpty"}]]}],
        decorations=[{"grid": (0, 0), "background": "yellow"}],
    )

    assert label_rows == [{"grid": (0, 0), "side": "above", "labels": [["spec1"], ["spec2"]]}]
    assert label_cols == [{"grid": (0, 0), "side": "left", "labels": [["col1"], ["col2"]]}]
    assert decorations == [{"grid": (0, 0), "background": "yellow"}]


def test_merge_label_specs_handles_no_annotations_or_unmatched_annotations():
    assert merge_label_specs(annotations=[], label_rows=None, label_cols=None, decorations=None) == (None, None, None)
    assert merge_label_specs(
        annotations=["bad", {"grid": (0, 0), "label": "callout"}],
        label_rows=None,
        label_cols=None,
        decorations=None,
    ) == (None, None, None)


def test_append_variable_labels_and_build_label_maps_defaults_and_non_strict_ignores():
    variable = [{"grid": (0, 0), "labels": [["x", "y"]]}, "bad"]
    assert append_variable_labels(None, variable) == [{"grid": (0, 0), "labels": [["x", "y"]], "side": "below"}]

    rows_map, cols_map, overlay = build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=[{"labels": ["top"]}, {"grid": (2, 0), "labels": ["skip"]}, {"grid": (0, 0), "side": "bad", "labels": ["skip"]}, "bad"],
        label_cols=[{"labels": [["left"]]}, {"grid": (2, 0), "labels": [["skip"]]}, {"grid": (0, 0), "side": "bad", "labels": [["skip"]]}, "bad"],
        variable_labels=variable,
        strict=False,
    )

    assert rows_map[(0, 0, "above")] == [["top"]]
    assert rows_map[(0, 0, "below")] == [["x", "y"]]
    assert cols_map[(0, 0, "left")] == [["left"]]
    assert overlay == []


def test_build_label_maps_collects_overlay_col_labels_without_embedding():
    rows_map, cols_map, overlay = build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=None,
        label_cols=[
            {"grid": (0, 0), "side": "left", "labels": [["overlay"]], "overlay": True},
            {"grid": (0, 0), "side": "right", "labels": [["normal"]]},
        ],
        allow_overlay=True,
    )

    assert rows_map == {}
    assert cols_map == {(0, 0, "right"): [["normal"]]}
    assert overlay == [{"grid": (0, 0), "side": "left", "labels": [["overlay"]], "overlay": True}]


def test_build_label_maps_prefers_canonical_labels_payload():
    rows_map, cols_map, _overlay = build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["new"]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [["new"]]}],
    )

    assert rows_map[(0, 0, "above")] == [["new"]]
    assert cols_map[(0, 0, "left")] == [["new"]]


def test_build_label_maps_strict_rejects_label_cols_variants():
    for label_cols, message in [
        ([["x"]], "dict"),
        ([{"grid": (2, 0), "labels": [["x"]]}], "out of range"),
        ([{"grid": (0, 0), "side": "above", "labels": [["x"]]}], "side"),
        ([{"grid": "bad", "labels": [["x"]]}], "grid"),
    ]:
        try:
            build_label_maps(
                n_block_rows=1,
                n_block_cols=1,
                label_rows=None,
                label_cols=label_cols,
                strict=True,
            )
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError("expected strict label_cols validation to raise")


def test_compute_label_extras_counts_maximums():
    extras = compute_label_extras(
        n_block_rows=2,
        n_block_cols=2,
        label_rows_map={(0, 0, "above"): [["a"], ["b"]], (1, 1, "below"): [["c"]]},
        label_cols_map={(0, 0, "left"): [["l"]], (1, 1, "right"): [["r1"], ["r2"]]},
    )

    assert extras == ([2, 0], [0, 1], [1, 0], [0, 2])


def test_embed_row_labels_moves_labels_into_empty_neighbor_blocks():
    label_rows_map = {
        (1, 0, "above"): [["a1"], ["a2"]],
        (1, 1, "below"): [["b1"]],
    }
    cell_cache = [
        [([], 2, 0), ([[1]], 1, 1)],
        [([[2]], 1, 1), ([[3]], 1, 1)],
        [([[4]], 1, 1), ([], 1, 0)],
    ]

    embedded = embed_row_labels(
        n_block_rows=3,
        n_block_cols=2,
        label_rows_map=label_rows_map,
        block_heights=[2, 1, 1],
        block_pad_left=[[0, 0], [1, 0], [0, 0]],
        cell_cache=cell_cache,
    )

    assert embedded[(0, 0)] == [(1, 1, ["a2"], 1), (0, 1, ["a1"], 1)]
    assert embedded[(2, 1)] == [(0, 0, ["b1"], 1)]
    assert label_rows_map == {}


def test_embed_row_labels_keeps_edge_labels_when_no_neighbor_block_exists():
    label_rows_map = {
        (0, 0, "above"): [["top"]],
        (1, 0, "below"): [["bottom"]],
    }
    cell_cache = [
        [([[1]], 1, 1)],
        [([[2]], 1, 1)],
    ]

    embedded = embed_row_labels(
        n_block_rows=2,
        n_block_cols=1,
        label_rows_map=label_rows_map,
        block_heights=[1, 1],
        block_pad_left=[[0], [0]],
        cell_cache=cell_cache,
    )

    assert embedded == {}
    assert label_rows_map == {
        (0, 0, "above"): [["top"]],
        (1, 0, "below"): [["bottom"]],
    }


def test_embed_col_labels_moves_labels_into_empty_neighbor_blocks_and_keeps_shared_labels():
    label_cols_map = {
        (0, 1, "left"): [["l1"], ["l2"]],
        (1, 1, "left"): [["keep"]],
        (1, 0, "right"): [["r1"]],
    }
    cell_cache = [
        [([], 0, 2), ([[1]], 1, 1)],
        [([[2]], 1, 1), ([[3]], 1, 1), ([], 0, 1)],
    ]

    embedded = embed_col_labels(
        n_block_rows=2,
        n_block_cols=3,
        label_cols_map=label_cols_map,
        block_widths=[2, 1, 1],
        block_pad_top=[[0, 1], [0, 0, 0]],
        cell_cache=cell_cache,
    )

    assert (0, 0) not in embedded
    assert label_cols_map[(0, 1, "left")] == [["l1"], ["l2"]]
    assert label_cols_map[(1, 1, "left")] == [["keep"]]
    assert embedded[(1, 2)] == [(0, 0, ["r1"], "right")]
    assert (1, 0, "right") not in label_cols_map


def test_embed_col_labels_keeps_edge_labels_when_no_neighbor_block_exists():
    label_cols_map = {
        (0, 0, "left"): [["left"]],
        (0, 1, "right"): [["right"]],
    }
    cell_cache = [
        [([[1]], 1, 1), ([[2]], 1, 1)],
    ]

    embedded = embed_col_labels(
        n_block_rows=1,
        n_block_cols=2,
        label_cols_map=label_cols_map,
        block_widths=[1, 1],
        block_pad_top=[[0, 0]],
        cell_cache=cell_cache,
    )

    assert embedded == {}
    assert label_cols_map == {
        (0, 0, "left"): [["left"]],
        (0, 1, "right"): [["right"]],
    }
