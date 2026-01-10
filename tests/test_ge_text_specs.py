from matrixlayout.ge import ge_grid_text_specs, ge_grid_tex


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
