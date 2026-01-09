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
