def test_backsubst_tex_decorators_apply_to_cascade():
    from matrixlayout.backsubst import backsubst_tex

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = backsubst_tex(
        cascade_txt=["L1", "L2"],
        show_system=False,
        show_solution=False,
        decorators=[{"block": "cascade", "entries": [1], "decorator": dec}],
    )

    assert r"\boxed{L2}" in tex


def test_backsubst_tex_decorators_strict_raises_on_empty():
    from matrixlayout.backsubst import backsubst_tex

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    try:
        backsubst_tex(
            cascade_txt=["L1", "L2"],
            show_system=False,
            show_solution=False,
            decorators=[{"block": "cascade", "entries": [9], "decorator": dec}],
            strict=True,
        )
    except ValueError:
        return
    raise AssertionError("strict decorator selection should raise")


def test_backsubst_tex_decorators_strict_raises_on_targeted_empty_block():
    from matrixlayout.backsubst import backsubst_tex

    def dec(tex: str) -> str:
        return tex

    try:
        backsubst_tex(
            cascade_txt=["L1"],
            show_solution=False,
            decorators=[{"block": "system", "entries": [0], "decorator": dec}],
            strict=True,
        )
    except ValueError as err:
        assert "decorator selector did not match" in str(err)
        return
    raise AssertionError("strict decorator selection should raise for empty targeted block")
