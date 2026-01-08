def test_qr_grid_tex_smoke():
    from matrixlayout.qr import qr_grid_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    tex = qr_grid_tex(matrices=matrices, preamble="")
    assert "\\begin{NiceArray}" in tex
    assert "\\SubMatrix" in tex
    assert "QR0x2" in tex
