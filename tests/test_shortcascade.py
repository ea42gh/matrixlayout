import pytest

from matrixlayout.shortcascade import mk_shortcascade_lines, normalize_backsub_trace
from matrixlayout.backsubst import backsubst_tex


def test_mk_shortcascade_lines_nested_structure():
    trace = {
        "base": r"x_3 = \\alpha_1, x_5 = \\alpha_2",
        "steps": [
            (r"x_4 = 2 + 2 x_5", r"x_4 = 2 + 2 \\alpha_2"),
            (r"x_2 = 1 + x_3 - x_4", r"x_2 = -1+\\alpha_1-2\\alpha_2"),
            (
                r"x_1 = 4 - x_2 - x_3 - 2 x_4 -2 x_5",
                r"x_1 = 1-\\alpha_1+2\\alpha_2",
            ),
        ],
    }

    lines = mk_shortcascade_lines(trace)

    # One opening and closing per step.
    assert lines.count(r"{\ShortCascade%") == 3
    assert lines.count(r"}%") == 3

    # Base assignment is boxed and appears before the first equation.
    base_idx = next(i for i, s in enumerate(lines) if "\\boxed" in s and "x_3" in s)
    first_raw_idx = next(i for i, s in enumerate(lines) if "x_4" in s and "=" in s)
    assert base_idx < first_raw_idx

    # Order is preserved.
    joined = "\n".join(lines)
    assert joined.index("x_4") < joined.index("x_2") < joined.index("x_1")


def test_backsubst_tex_accepts_cascade_trace():
    trace = {
        "base": [("x_3", r"\\alpha_1"), ("x_5", r"\\alpha_2")],
        "steps": [(r"x_4 = 2 + 2 x_5", r"x_4 = 2 + 2 \\alpha_2")],
    }

    tex = backsubst_tex(
        cascade_trace=trace,
        show_system=False,
        show_solution=False,
    )

    assert r"\ShortCascade" in tex
    assert r"\boxed" in tex
    assert "x_4" in tex


def test_mk_shortcascade_lines_empty_trace_returns_no_lines():
    assert mk_shortcascade_lines({"base": "", "steps": []}) == []


def test_mk_shortcascade_lines_base_only_is_boxed():
    assert mk_shortcascade_lines({"base": "t = 1", "steps": []}) == [r"{$\boxed{ t = 1 }$}%"]


def test_normalize_backsub_trace_accepts_two_sequence_and_lhs_rhs_steps():
    base, steps = normalize_backsub_trace(
        (
            [("x", "s"), "y = t"],
            [{"lhs": "x + y", "rhs": "s + t"}],
        )
    )

    assert base == "x = s, y = t"
    assert steps == [("x + y", "s + t")]


def test_normalize_backsub_trace_none_steps_and_missing_base():
    assert normalize_backsub_trace({"steps": None}) == ("", [])


def test_normalize_backsub_trace_rejects_invalid_trace_shape():
    with pytest.raises(TypeError, match="trace must be"):
        normalize_backsub_trace(["base only"])


def test_normalize_backsub_trace_rejects_nonsequence_steps():
    with pytest.raises(TypeError, match=r"trace\['steps'\] must be a sequence"):
        normalize_backsub_trace({"base": "x = t", "steps": object()})


def test_normalize_backsub_trace_rejects_invalid_step_shape():
    with pytest.raises(TypeError, match="Each step must"):
        normalize_backsub_trace({"base": "x = t", "steps": ["bad step"]})
