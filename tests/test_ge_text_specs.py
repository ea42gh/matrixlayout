from unittest.mock import patch

from matrixlayout.ge import (
    ge_grid_label_layouts,
    ge_grid_svg,
    ge_grid_text_specs,
    ge_grid_tex,
)


def test_ge_grid_text_specs_default_offsets():
    matrices = [[[1, 2], [3, 4]]]
    specs = ge_grid_text_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "above", "labels": ["a", "b"]},
            {"grid": (0, 0), "side": "below", "labels": ["a", "b"]},
        ],
    )
    above = [s for s in specs if "yshift=3.0mm" in s[2]]
    below = [s for s in specs if "yshift=-3.5mm" in s[2]]
    assert above
    assert below


def test_ge_grid_text_specs_multiline_default_line_gap():
    matrices = [[[1, 2], [3, 4]]]
    specs = ge_grid_text_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "below", "labels": [["a", "b"], ["c", "d"]]},
        ],
    )
    assert any("yshift=-3.5mm" in s[2] for s in specs)
    assert any("yshift=-8.0mm" in s[2] for s in specs)


def test_ge_grid_text_specs_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    specs = ge_grid_text_specs(
        matrices,
        [
            {"grid": (0, 0), "side": "right", "labels": ["row $i$", "$x_1$", "plain"]},
        ],
    )
    texts = [s[1] for s in specs]
    assert any(t == "$\\text{row }i$" for t in texts)
    assert any(t == "$x_1$" for t in texts)
    assert any(t == "plain" for t in texts)


def test_ge_grid_tex_label_rows_mixed_text_latex():
    matrices = [[[1, 2], [3, 4]]]
    tex = ge_grid_tex(
        matrices=matrices,
        formatter=str,
        label_rows=[
            {"grid": (0, 0), "side": "below", "rows": [["row $i$", "$x_1$"]]},
        ],
    )
    assert "\\text{row }i" in tex
    assert "x_1" in tex


def test_ge_grid_text_specs_accounts_for_label_rows():
    matrices = [[[1, 2], [3, 4]]]
    specs = ge_grid_text_specs(
        matrices,
        [{"grid": (0, 0), "side": "left", "labels": ["a", "b"]}],
        label_rows=[{"grid": (0, 0), "side": "above", "rows": ["x", "y"]}],
    )
    coords = [s[0] for s in specs]
    assert "(2-1.west)" in coords
    assert "(3-1.west)" in coords


def test_ge_grid_label_layouts_basic():
    rows, cols = ge_grid_label_layouts(
        [
            {"grid": (0, 0), "side": "above", "labels": ["head", "tail"]},
            {"grid": (1, 1), "side": "left", "labels": [["a"], ["b"]]},
        ],
    )
    assert rows == [{"grid": (0, 0), "side": "above", "rows": [["head", "tail"]]}]
    assert cols == [{"grid": (1, 1), "side": "left", "cols": [["a"], ["b"]]}]


def test_ge_grid_svg_label_targets_passes_label_rows():
    matrices = [
        [None, [[1, 2], [3, 4]]],
        [[[1, 0], [0, 1]], [[1, 2], [0, 2]]],
    ]
    targets = [
        {"grid": (0, 1), "side": "left", "labels": ["$w_1^T$", "$w_2^T$"]},
    ]
    with patch("matrixlayout.ge.ge_grid_tex") as mock_tex, patch("matrixlayout.ge._render_svg") as mock_svg:
        mock_tex.return_value = "TEX"
        mock_svg.return_value = "SVG"
        ge_grid_svg(matrices=matrices, label_targets=targets)
        kwargs = mock_tex.call_args.kwargs
        assert "label_rows" not in kwargs
        assert "label_cols" in kwargs
        label_cols = kwargs["label_cols"]
        assert label_cols and label_cols[0]["grid"] == (0, 1)
        assert label_cols[0]["side"] == "left"
        mock_svg.assert_called_once_with(
            "TEX",
            toolchain_name=None,
            crop=None,
            padding=None,
            frame=None,
            output_dir=None,
            output_stem="output",
        )

