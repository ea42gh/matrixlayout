import pytest

from matrixlayout.eigproblem_decorations import apply_matrix_decorators
from matrixlayout.eigproblem_decorations import apply_vector_decorators
from matrixlayout.eigproblem_decorations import collect_vector_decorator_specs


def _box(tex: str) -> str:
    return rf"\boxed{{{tex}}}"


def test_collect_vector_decorator_specs_expands_entry_range():
    vec_groups = [
        [[1, 2, 3]],
        [[4, 5, 6]],
    ]
    specs = collect_vector_decorator_specs(
        vec_groups,
        [{"target": "eigenbasis", "entries": [((0, 0, 1), (0, 0, 2))], "decorator": _box}],
        "eigenbasis",
    )

    assert len(specs) == 1
    assert specs[0][1] == {(0, 0, 1), (0, 0, 2)}


def test_apply_vector_decorators_tracks_applied_counts():
    dec_specs = [(_box, {(0, 0, 1)})]
    applied_counts = [0]

    cell = apply_vector_decorators(
        "2",
        value=2,
        group_index=0,
        vector_index=0,
        entry_index=1,
        dec_specs=dec_specs,
        applied_counts=applied_counts,
    )

    assert cell == r"\boxed{2}"
    assert applied_counts == [1]


def test_apply_matrix_decorators_matches_matrix_alias():
    mat_tex = [["1", "0"], ["0", "2"]]
    mat_raw = [[1, 0], [0, 2]]

    out = apply_matrix_decorators(
        mat_tex,
        mat_raw,
        [{"target": "lambda_matrix", "entries": [(1, 1)], "decorator": _box}],
        ["lambda", "lambda_matrix"],
        str,
        strict=True,
    )

    assert out[1][1] == r"\boxed{2}"


def test_apply_matrix_decorators_strict_raises_for_missed_selector():
    with pytest.raises(ValueError, match="decorator selector did not match"):
        apply_matrix_decorators(
            [["1"]],
            [[1]],
            [{"matrix": "lambda", "entries": [(4, 4)], "decorator": _box}],
            ["lambda"],
            str,
            strict=True,
        )
