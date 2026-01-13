from unittest.mock import patch

from matrixlayout.ge import (
    grid_label_layouts,
    grid_svg,
    grid_submatrix_spans,
    grid_tex_specs,
    grid_tex,
)


def _parse_coord(coord: str) -> tuple[int, int, str]:
    body = coord[1:-1]
    pos, anchor = body.rsplit(".", 1)
    row_str, col_str = pos.split("-", 1)
    return int(row_str), int(col_str), anchor


def test_grid_tex_specs_default_offsets():
    matrices = [[[1, 2], [3, 4]]]
    specs = grid_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "above", "labels": ["a", "b"]},
            {"grid": (0, 0), "side": "below", "labels": ["a", "b"]},
        ],
    )
    above = [s for s in specs if "anchor=center" in s[2]]
    below = [s for s in specs if "anchor=center" in s[2]]
    assert above
    assert below
    assert all("yshift" not in s[2] for s in above)
    assert all("yshift" not in s[2] for s in below)


def test_grid_tex_specs_multiline_default_line_gap():
    matrices = [[[1, 2], [3, 4]]]
    specs = grid_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "below", "labels": [["a", "b"], ["c", "d"]]},
        ],
    )
    assert any("yshift=-4.5mm" in s[2] for s in specs)
    assert not any("yshift=-8.0mm" in s[2] for s in specs)


def test_grid_tex_specs_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    specs = grid_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "right", "labels": ["row $i$", "$x_1$", "plain"]},
        ],
    )
    texts = [s[1] for s in specs]
    assert any(t == "$\\text{row }i$" for t in texts)
    assert any(t == "$x_1$" for t in texts)
    assert any(t == "plain" for t in texts)


def test_grid_tex_label_rows_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    tex = grid_tex(
        matrices=matrices,
        formatter=str,
        label_rows=[
            {"grid": (0, 0), "side": "below", "rows": [["row $i$", "$x_1$"]]},
        ],
    )
    assert "\\text{row }i" in tex
    assert "x_1" in tex


def test_grid_tex_specs_accounts_for_label_rows():
    matrices = [[[1, 2], [3, 4]]]
    specs = grid_tex_specs(
        matrices,
        [{"grid": (0, 0), "side": "left", "labels": ["a", "b"]}],
        label_rows=[{"grid": (0, 0), "side": "above", "rows": ["x", "y"]}],
    )
    coords = [s[0] for s in specs]
    assert "(2-1.center)" in coords
    assert "(3-1.center)" in coords


def test_ge_grid_label_layouts_basic():
    rows, cols = grid_label_layouts(
        [
            {"grid": (0, 0), "side": "above", "labels": ["head", "tail"]},
            {"grid": (1, 1), "side": "left", "labels": [["a"], ["b"]]},
        ],
    )
    assert rows == [{"grid": (0, 0), "side": "above", "rows": [["head", "tail"]]}]
    assert cols == [{"grid": (1, 1), "side": "left", "cols": [["a"], ["b"]]}]


def test_grid_tex_specs_axis_consistency():
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[1, 2], [0, 2]]],
    ]
    targets = [
        {"grid": (0, 1), "side": "left", "labels": ["a", "b"]},
        {"grid": (1, 1), "side": "right", "labels": ["c", "d"]},
        {"grid": (1, 0), "side": "above", "labels": ["e", "f"]},
        {"grid": (1, 0), "side": "below", "labels": ["g", "h"]},
    ]
    spans = grid_submatrix_spans(matrices)
    span_map = {(span.block_row, span.block_col): span for span in spans}
    for target in targets:
        side = target["side"]
        grid = tuple(target["grid"])
        span = span_map[grid]
        specs = grid_tex_specs(matrices, [target])
        parsed = [_parse_coord(coord) for coord, *_ in specs]
        assert parsed
        if side in ("left", "right"):
            expected_col = span.col_end if side == "right" else max(span.col_start - 1, 1)
            assert all(col == expected_col for _, col, _ in parsed)
        else:
            expected_row = span.row_start if side == "above" else span.row_end
            assert all(row == expected_row for row, _, _ in parsed)


def test_grid_tex_specs_offset_alignment():
    matrices = [[[1, 2], [3, 4]]]
    specs = grid_tex_specs(
        matrices,
        [
            {
                "grid": (0, 0),
                "side": "left",
                "labels": ["l"],
                "offset_mm": 1.0,
                "xshift_mm": 0.25,
            },
            {
                "grid": (0, 0),
                "side": "right",
                "labels": ["r"],
                "offset_mm": 0.5,
                "xshift_mm": 0.25,
            },
        ],
    )
    opts = [opts for _, _, opts in specs if "anchor=center" in opts]
    assert opts
    assert any("xshift=1.25mm" in opt for opt in opts)
    assert any("xshift=0.75mm" in opt for opt in opts)


def test_grid_svg_label_targets_overlay():
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[1, 2], [0, 2]]],
    ]
    targets = [
        {"grid": (0, 1), "side": "left", "labels": ["$w_1^T$", "$w_2^T$"]},
    ]
    with patch("matrixlayout.ge.grid_tex") as mock_tex, patch("matrixlayout.ge._render_svg") as mock_svg:
        mock_tex.return_value = "TEX"
        mock_svg.return_value = "SVG"
        grid_svg(matrices=matrices, specs=targets)
        assert mock_tex.call_args.kwargs.get("specs") == targets


def test_grid_svg_label_targets_add_blank_rows():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "above", "labels": ["head", "tail"]},
    ]
    tex = grid_tex(matrices=matrices, formatter=str, specs=targets)
    assert "\\text{head}" in tex
    assert "\\text{tail}" in tex


def test_grid_svg_label_targets_preserve_label_rows():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "above", "labels": ["head"]},
    ]
    existing_rows = [{"grid": (0, 0), "side": "above", "rows": [["X"]]}]
    tex = grid_tex(matrices=matrices, formatter=str, label_rows=existing_rows, specs=targets)
    assert "\\text{X}" in tex
    assert "\\text{head}" in tex


def test_grid_svg_label_targets_do_not_add_label_cols():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "left", "labels": ["a", "b"]},
    ]
    tex = grid_tex(matrices=matrices, formatter=str, specs=targets)
    assert "\\text{a}" in tex
    assert "\\text{b}" in tex
