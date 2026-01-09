from matrixlayout.ge import ge_grid_tex
from matrixlayout.formatting import make_decorator


def test_ge_grid_tex_decorators_apply():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [
        {
            "grid": (0, 1),
            "entries": [(0, 1)],
            "decorator": make_decorator(text_color="red", bf=True),
        }
    ]

    tex = ge_grid_tex(matrices=matrices, decorators=decorators, formater=str)
    assert r"\color{red}{\mathbf{2}}" in tex


def test_ge_grid_tex_decorators_resolve_matrix_name():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [
        {
            "matrix_name": "A0",
            "entries": [(0, 0)],
            "decorator": make_decorator(boxed=True),
        }
    ]

    tex = ge_grid_tex(matrices=matrices, decorators=decorators, formater=str)
    assert r"\boxed{1}" in tex


def test_ge_grid_tex_decorators_strict_raises_on_empty():
    matrices = [[None, [[1, 2], [3, 4]]]]
    decorators = [{"grid": (0, 1), "entries": [(9, 9)], "decorator": make_decorator(boxed=True)}]

    try:
        ge_grid_tex(matrices=matrices, decorators=decorators, formater=str, strict=True)
    except ValueError:
        return
    raise AssertionError("strict decorator selection should raise")
