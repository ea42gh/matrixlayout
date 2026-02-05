def test_render_qr_tex_smoke():
    from matrixlayout.qr import render_qr_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    tex = render_qr_tex(matrices=matrices, preamble="")
    assert "\\begin{NiceArray}" in tex


def test_render_qr_tex_filters_callouts_for_minimal_grid():
    from matrixlayout.qr import render_qr_tex

    matrices = [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]]]
    tex = render_qr_tex(matrices=matrices, preamble="")
    assert "\\begin{NiceArray}" in tex
    assert "\\SubMatrix" in tex
    assert "v_1" in tex


def test_qr_callout_rules_apply_to_qt_and_r():
    from matrixlayout.qr import _qr_default_name_specs, _qr_name_specs_to_callouts

    callouts = _qr_name_specs_to_callouts(
        _qr_default_name_specs(),
        color="blue",
        angle_deg=-35.0,
        length_mm=6.0,
        label_shift_rules=[
            (r"\mathbf{Q^T = S W^T}", -1.0),
            (r"\mathbf{R = S W^T A}", -2.0),
        ],
        length_rules=[(r"\mathbf{Q^T = S W^T}", 8.0)],
    )

    by_label = {c["label"]: c for c in callouts}
    qt = by_label[r"\mathbf{Q^T = S W^T}"]
    r_label = by_label[r"\mathbf{R = S W^T A}"]

    assert qt["angle_deg"] == 40.0
    assert qt["label_shift_y_mm"] == -1.0
    assert qt["length_mm"] == 8.0

    assert r_label["angle_deg"] == 40.0
    assert r_label["label_shift_y_mm"] == -2.0
    assert r_label["length_mm"] == 6.0
