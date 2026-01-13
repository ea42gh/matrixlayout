from matrixlayout.ge import grid_tex
from matrixlayout.formatting import make_decorator


def test_grid_tex_decorators_apply():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [
        {
            "grid": (0, 1),
            "entries": [(0, 1)],
            "decorator": make_decorator(text_color="red", bf=True),
        }
    ]

    tex = grid_tex(matrices=matrices, decorators=decorators, formatter=str)
    assert r"\color{red}{\mathbf{2}}" in tex


def test_grid_tex_decorators_resolve_matrix_name():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [
        {
            "matrix_name": "A0",
            "entries": [(0, 0)],
            "decorator": make_decorator(boxed=True),
        }
    ]

    tex = grid_tex(matrices=matrices, decorators=decorators, formatter=str)
    assert r"\boxed{1}" in tex


def test_grid_tex_decorators_strict_raises_on_empty():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [{"grid": (0, 1), "entries": [(9, 9)], "decorator": make_decorator(boxed=True)}]

    try:
        grid_tex(matrices=matrices, decorators=decorators, formatter=str, strict=True)
    except ValueError:
        return
    raise AssertionError("strict decorator selection should raise")


def test_resolve_ge_grid_name():
    from matrixlayout.ge import resolve_ge_grid_name

    matrices = [[None, [[1, 2], [3, 4]]]]
    assert resolve_ge_grid_name("A0", matrices=matrices) == (0, 1)
    assert resolve_ge_grid_name("A0x1", matrices=matrices) == (0, 1)


def test_grid_tex_respects_explicit_matrices_over_spec():
    from matrixlayout.ge import grid_tex

    spec = {"matrices": [[None, [[9]]]]}
    tex = grid_tex(matrices=[[None, [[1]]]], spec=spec, formatter=lambda x: f"v{x}")
    assert "v1" in tex
    assert "v9" not in tex
