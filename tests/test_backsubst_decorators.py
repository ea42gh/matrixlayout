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
