def test_render_qr_tex_decorators_apply():
    from matrixlayout.qr import render_qr_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = render_qr_tex(
        matrices=matrices,
        formatter=str,
        body_preamble="",
        decorators=[{"grid": (0, 2), "entries": [(0, 0)], "decorator": dec}],
    )

    assert r"\boxed{1}" in tex


def test_render_qr_tex_decorators_use_grid():
    from matrixlayout.qr import render_qr_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = render_qr_tex(
        matrices=matrices,
        formatter=str,
        body_preamble="",
        decorators=[{"grid": (0, 2), "entries": [(0, 0)], "decorator": dec}],
    )

    assert r"\boxed{1}" in tex


def test_render_qr_tex_decorators_strict_raises_on_empty():
    from matrixlayout.qr import render_qr_tex

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    try:
        render_qr_tex(
            matrices=matrices,
            formatter=str,
            body_preamble="",
            decorators=[{"grid": (0, 2), "entries": [(9, 9)], "decorator": dec}],
            strict=True,
        )
    except ValueError:
        return
    raise AssertionError("strict decorator selection should raise")


def test_resolve_qr_grid_name():
    from matrixlayout.qr import resolve_qr_grid_name

    matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
    ]

    assert resolve_qr_grid_name("QR0x2", matrices=matrices) == (0, 2)


def test_qr_grid_bundle_is_importable_and_returns_spans():
    from matrixlayout.qr import qr_grid_bundle
    from matrixlayout.specs import QRGridBundle

    matrices = [[None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]]]

    bundle = qr_grid_bundle(matrices=matrices, array_names=False)

    assert isinstance(bundle, QRGridBundle)
    assert bundle.tex
    assert bundle.submatrix_spans
