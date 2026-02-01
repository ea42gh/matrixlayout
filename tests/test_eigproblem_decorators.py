def test_render_eig_tex_decorates_lambda_matrix():
    from matrixlayout.eigproblem import render_eig_tex

    spec = {
        "lambda": [2],
        "ma": [1],
        "evecs": [[[1]]],
    }

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = render_eig_tex(
        spec,
        case="S",
        formatter=str,
        decorators=[{"matrix": "lambda", "entries": [(0, 0)], "decorator": dec}],
        preamble="",
    )

    assert r"\boxed{2}" in tex


def test_render_eig_tex_decorates_eigenbasis_vector_entry():
    from matrixlayout.eigproblem import render_eig_tex

    spec = {
        "lambda": [2],
        "ma": [1],
        "evecs": [[[1, 5]]],
    }

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = render_eig_tex(
        spec,
        case="S",
        formatter=str,
        decorators=[{"target": "eigenbasis", "entries": [(0, 0, 1)], "decorator": dec}],
        preamble="",
    )

    assert r"\boxed{5}" in tex


def test_render_eig_tex_decorates_evecs_row_alias():
    from matrixlayout.eigproblem import render_eig_tex

    spec = {
        "lambda": [2],
        "ma": [1],
        "evecs": [[[1, 7]]],
    }

    def dec(tex: str) -> str:
        return rf"\boxed{{{tex}}}"

    tex = render_eig_tex(
        spec,
        case="S",
        formatter=str,
        decorators=[{"target": "evecs_row", "entries": [(0, 0, 1)], "decorator": dec}],
        preamble="",
    )

    assert r"\boxed{7}" in tex
