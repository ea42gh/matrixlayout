from unittest.mock import patch

import pytest

from matrixlayout.ge import (
    grid_label_layouts,
    render_ge_svg,
    grid_submatrix_spans,
    render_ge_tex_specs,
    render_ge_tex,
)


def _parse_coord(coord: str) -> tuple[int, int, str]:
    body = coord[1:-1]
    pos, anchor = body.rsplit(".", 1)
    row_str, col_str = pos.split("-", 1)
    return int(row_str), int(col_str), anchor


def test_render_ge_tex_specs_default_offsets():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
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


def test_render_ge_tex_specs_multiline_default_line_gap():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "below", "labels": [["a", "b"], ["c", "d"]]},
        ],
    )
    assert any("yshift=-4.5mm" in s[2] for s in specs)
    assert not any("yshift=-8.0mm" in s[2] for s in specs)


def test_render_ge_tex_specs_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "right", "labels": ["row $i$", "$x_1$", "plain"]},
        ],
    )
    texts = [s[1] for s in specs]
    assert any(t == "$\\text{row }i$" for t in texts)
    assert any(t == "$x_1$" for t in texts)
    assert any(t == "plain" for t in texts)


def test_render_ge_tex_specs_label_value_variants_and_alias_sides():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "top", "labels": [{"text": "top"}, ("ignored", "pair")]},
            {"grid": (0, 0), "side": "bottom", "labels": [["b1", "b2"], ["c1", "c2"]], "line_gap_mm": 6},
            {"grid": (0, 0), "side": "left", "labels": [["L1", "L2"], ["M1", "M2"]], "line_gap_mm": 2},
        ],
    )

    assert ("(1-1.center)", "top", "anchor=center") in specs
    assert ("(1-2.center)", "pair", "anchor=center") in specs
    assert any(coord == "(2-1.center)" and text == "b1" for coord, text, _ in specs)
    assert any("yshift=-6.0mm" in opts for _, _, opts in specs)
    assert any(text == "M1" and "xshift=-2.0mm" in opts for _, text, opts in specs)


def test_render_ge_tex_specs_ignores_bad_label_row_metadata():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
        matrices,
        [{"grid": (0, 0), "side": "above", "labels": [["x", "y"]]}],
        label_rows=[
            object(),
            {"grid": (0,), "side": "above", "labels": [["bad"]]},
            {"grid": (0, 0), "side": "left", "labels": [["bad"]]},
        ],
    )

    assert specs == [
        ("(1-1.center)", "x", "anchor=center"),
        ("(1-2.center)", "y", "anchor=center"),
    ]


def test_render_ge_tex_label_rows_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    tex = render_ge_tex(
        matrices=matrices,
        formatter=str,
        label_rows=[
            {"grid": (0, 0), "side": "below", "labels": [["row $i$", "$x_1$"]]},
        ],
    )
    assert "\\text{row }i" in tex
    assert "x_1" in tex


def test_render_ge_tex_label_rows_escape_plain_text_specials():
    tex = render_ge_tex(
        matrices=[[[1, 0, 2], [0, 1, -1]]],
        formatter=str,
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["x_1", "x^2", "a&b"]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [["r_1"], ["r^2"]]}],
    )

    assert r"\text{x\_1}" in tex
    assert r"\text{x\textasciicircum{}2}" in tex
    assert r"\text{a\&b}" in tex
    assert r"\text{r\_1}\hspace{0.8mm}" in tex
    assert r"\text{r\textasciicircum{}2}\hspace{0.8mm}" in tex


def test_render_ge_tex_specs_escape_plain_text_specials_in_mixed_labels():
    specs = render_ge_tex_specs(
        [[[1, 2], [3, 4]]],
        [{"grid": (0, 0), "side": "right", "labels": ["row_name $i$", "x_1"]}],
    )
    texts = [s[1] for s in specs]

    assert r"$\text{row\_name }i$" in texts
    assert "x\\_1" in texts


def test_render_ge_tex_label_cols_singletons_attach_to_matrix_rows():
    tex = render_ge_tex(
        matrices=[[[1, 0, 2], [0, 1, -1]]],
        formatter=str,
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["x1", "x2", "b"]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [["r1"], ["r2"]]}],
    )

    assert r"\text{r1}\hspace{0.8mm} & 1 & 0 & 2" in tex
    assert r"\text{r2}\hspace{0.8mm} & 0 & 1 & -1" in tex
    assert r"\text{r1}\hspace{0.8mm} & \text{r2}\hspace{0.8mm} & 1" not in tex


def test_render_ge_tex_specs_accounts_for_label_rows():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
        matrices,
        [{"grid": (0, 0), "side": "left", "labels": ["a", "b"]}],
        label_rows=[{"grid": (0, 0), "side": "above", "labels": ["x", "y"]}],
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
    assert rows == [{"grid": (0, 0), "side": "above", "labels": [["head", "tail"]]}]
    assert cols == [{"grid": (1, 1), "side": "left", "labels": [["a"], ["b"]]}]


def test_render_ge_tex_specs_axis_consistency():
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
        specs = render_ge_tex_specs(matrices, [target])
        parsed = [_parse_coord(coord) for coord, *_ in specs]
        assert parsed
        if side in ("left", "right"):
            expected_col = span.col_end if side == "right" else max(span.col_start - 1, 1)
            assert all(col == expected_col for _, col, _ in parsed)
        else:
            expected_row = span.row_start if side == "above" else span.row_end
            assert all(row == expected_row for row, _, _ in parsed)


def test_render_ge_tex_specs_offset_alignment():
    matrices = [[[1, 2], [3, 4]]]
    specs = render_ge_tex_specs(
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


def test_render_ge_tex_specs_strict_rejects_bad_targets():
    matrices = [[[1, 2], [3, 4]]]

    with pytest.raises(ValueError, match="targets must be mappings"):
        render_ge_tex_specs(matrices, [object()], strict=True)

    with pytest.raises(ValueError, match="require grid"):
        render_ge_tex_specs(matrices, [{"labels": ["x"]}], strict=True)

    with pytest.raises(ValueError, match="outside"):
        render_ge_tex_specs(matrices, [{"grid": (9, 0), "labels": ["x"]}], strict=True)

    with pytest.raises(ValueError, match="side"):
        render_ge_tex_specs(matrices, [{"grid": (0, 0), "side": "diagonal", "labels": ["x"]}], strict=True)


def test_render_ge_tex_specs_default_still_ignores_bad_targets():
    matrices = [[[1, 2], [3, 4]]]

    assert render_ge_tex_specs(matrices, [object(), {"labels": ["x"]}, {"grid": (9, 0), "labels": ["x"]}]) == []


def test_render_ge_svg_label_targets_overlay():
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[1, 2], [0, 2]]],
    ]
    targets = [
        {"grid": (0, 1), "side": "left", "labels": ["$w_1^T$", "$w_2^T$"]},
    ]
    with patch("matrixlayout.ge.render_ge_tex") as mock_tex, patch("matrixlayout.ge._render_svg") as mock_svg:
        mock_tex.return_value = "TEX"
        mock_svg.return_value = "SVG"
        render_ge_svg(matrices=matrices, annotations=targets)
        assert mock_tex.call_args.kwargs.get("annotations") == targets


def test_render_ge_svg_accepts_annotations_alias():
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[1, 2], [0, 2]]],
    ]
    annotations = [
        {"grid": (0, 1), "side": "left", "labels": ["$w_1^T$", "$w_2^T$"]},
    ]
    with patch("matrixlayout.ge.render_ge_tex") as mock_tex, patch("matrixlayout.ge._render_svg") as mock_svg:
        mock_tex.return_value = "TEX"
        mock_svg.return_value = "SVG"
        render_ge_svg(matrices=matrices, annotations=annotations)
        assert mock_tex.call_args.kwargs.get("annotations") == annotations


def test_render_ge_svg_label_targets_add_blank_rows():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "above", "labels": ["head", "tail"]},
    ]
    tex = render_ge_tex(matrices=matrices, formatter=str, annotations=targets)
    assert "\\text{head}" in tex
    assert "\\text{tail}" in tex


def test_render_ge_svg_label_targets_preserve_label_rows():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "above", "labels": ["head"]},
    ]
    existing_rows = [{"grid": (0, 0), "side": "above", "labels": [["X"]]}]
    tex = render_ge_tex(matrices=matrices, formatter=str, label_rows=existing_rows, annotations=targets)
    assert "\\text{X}" in tex
    assert "\\text{head}" in tex


def test_render_ge_svg_label_targets_do_not_add_label_cols():
    matrices = [[[1, 2], [3, 4]]]
    targets = [
        {"grid": (0, 0), "side": "left", "labels": ["a", "b"]},
    ]
    tex = render_ge_tex(matrices=matrices, formatter=str, annotations=targets)
    assert "\\text{a}" in tex
    assert "\\text{b}" in tex
