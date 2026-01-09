def test_qr_grid_tex_decorators_apply():
    from matrixlayout.qr import qr_grid_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = qr_grid_tex(
        matrices=matrices,
        formater=str,
        preamble="",
        decorators=[{"grid": (0, 2), "entries": [(0, 0)], "decorator": dec}],
    )

    assert r"\boxed{1}" in tex
