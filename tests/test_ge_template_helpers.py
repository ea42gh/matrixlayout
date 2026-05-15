import pytest

from matrixlayout.ge import tex
from matrixlayout.ge_template import (
    append_nicematrix_option,
    coerce_pivot_locs,
    coerce_rowechelon_paths,
    coerce_submatrix_locs,
    coerce_txt_with_locs,
    coord_paren,
    coord_token,
    fit_span,
    fit_target,
    guess_shape_from_mat_rep,
    merge_callouts,
    merge_list,
    normalize_mat_format,
    normalize_mat_rep,
    normalize_pivot_locs,
    normalize_submatrix_locs,
    normalize_txt_with_locs,
    validate_body_preamble,
)
from matrixlayout.specs import PivotBox, RowEchelonPath, SubMatrixLoc, TextAt


def test_coordinate_and_fit_normalizers_accept_common_forms():
    assert coord_token((1, 2)) == "1-2"
    assert coord_token([3, 4]) == "3-4"
    assert coord_token("(5-6)") == "5-6"
    assert coord_paren("7-8") == "(7-8)"
    assert coord_paren("(9-10)") == "(9-10)"

    assert fit_target("{1-2}{3-4}") == "(1-2)(3-4)"
    assert fit_target(((1, 2), (3, 4))) == "(1-2)(3-4)"
    assert fit_target("(1-2)(3-4)") == "(1-2)(3-4)"

    assert fit_span("{1-2}{3-4}") == "(1-2)(3-4)"
    assert fit_span(((1, 2), (3, 4))) == "(1-2)(3-4)"
    assert fit_span("(1-2)(3-4)") == "(1-2)(3-4)"
    assert fit_span("unparsed") == "unparsed"


def test_matrix_body_normalizers_and_shape_guessing():
    assert normalize_mat_format("{rr|r}") == "rr|r"
    assert normalize_mat_format(" cc ") == "cc"
    assert normalize_mat_rep(None) == ""
    assert normalize_mat_rep("1 & 2 \\ 3 & 4") == "1 & 2 \\\\ 3 & 4"
    assert guess_shape_from_mat_rep("1 & 2 \\\\ 3 & 4") == (2, 2)
    assert guess_shape_from_mat_rep("") == (0, 0)


def test_template_option_and_merge_helpers():
    assert append_nicematrix_option(None, "create-extra-nodes") == "create-extra-nodes"
    assert append_nicematrix_option("", "create-extra-nodes") == "create-extra-nodes"
    assert append_nicematrix_option("foo", "bar") == "foo, bar"
    assert append_nicematrix_option("foo, bar", "bar") == "foo, bar"

    assert merge_list(None, None) is None
    assert merge_list(["explicit"], ["spec"]) == ["explicit", "spec"]
    assert merge_callouts(None, True) is True
    assert merge_callouts(False, None) is False
    assert merge_callouts(True, True) is True
    assert merge_callouts([1], [2]) == [1, 2]
    with pytest.raises(ValueError, match="Conflicting values"):
        merge_callouts(True, False)


def test_validate_body_preamble_rejects_preamble_directives():
    validate_body_preamble("")
    validate_body_preamble(r"\small")

    for preamble in [r"\documentclass{article}", r"\usepackage{amsmath}", r"\RequirePackage{xcolor}", r"\geometry{margin=1in}"]:
        with pytest.raises(ValueError, match="injected into the document body"):
            validate_body_preamble(preamble)


def test_normalize_submatrix_locs_all_supported_forms():
    assert normalize_submatrix_locs(None) == []
    assert normalize_submatrix_locs(
        [
            ("name=A", "{1-1}{2-2}"),
            ("name=B", "(3-3)(4-4)"),
            ("name=C", (5, 5), (6, 6)),
            ("name=D", ((7, 7), (8, 8))),
            ("name=E", "{9-9}{10-10}", "[", "]"),
            ("name=F", (11, 11), (12, 12), "(", ")"),
        ]
    ) == [
        ("name=A", "{1-1}{2-2}"),
        ("name=B", "{3-3}{4-4}"),
        ("name=C", "{5-5}{6-6}"),
        ("name=D", "{7-7}{8-8}"),
        ("name=E", "{9-9}{10-10}", "[", "]"),
        ("name=F", "{11-11}{12-12}", "(", ")"),
    ]


def test_normalize_submatrix_locs_rejects_bad_spans_and_arity():
    with pytest.raises(ValueError, match="Bad span"):
        normalize_submatrix_locs([("name=A", "{1-1}")])
    with pytest.raises(ValueError, match="2-, 3-, 4-, or 5-tuple"):
        normalize_submatrix_locs([("name=A", "1-1", "2-2", "(", ")", "extra")])


def test_normalize_submatrix_locs_delimited_coordinate_variants():
    assert normalize_submatrix_locs(
        [
            ("name=A", ((1, 2), (3, 4)), "[", "]"),
            ("name=B", "(5-6)", "(7-8)", r"\{", r"\}"),
        ]
    ) == [
        ("name=A", "{1-2}{3-4}", "[", "]"),
        ("name=B", "{5-6}{7-8}", r"\{", r"\}"),
    ]

    with pytest.raises(ValueError, match="Bad span"):
        normalize_submatrix_locs([("name=C", "(1-1)", "[", "]")])


def test_pivot_and_text_location_normalizers():
    assert normalize_pivot_locs(None) == []
    assert normalize_pivot_locs([("{1-1}{2-2}", "draw=red"), (((3, 3), (4, 4)), None)]) == [
        ("(1-1)(2-2)", "draw=red"),
        ("(3-3)(4-4)", ""),
    ]

    assert normalize_txt_with_locs(None) == []
    assert normalize_txt_with_locs([((1, 2), "label", None), ("(3-4)", 12, "blue")]) == [
        ("(1-2)", "label", ""),
        ("(3-4)", "12", "blue"),
    ]


def test_typed_spec_coercion_helpers():
    assert coerce_submatrix_locs(None) is None
    assert coerce_submatrix_locs(
        [
            SubMatrixLoc(opts="name=A", start="1-1", end="2-2"),
            {"opts": "name=B", "start": "3-3", "end": "4-4", "left_delim": "[", "right_delim": "]"},
            ("name=C", "5-5", "6-6"),
        ]
    ) == [
        ("name=A", "1-1", "2-2"),
        ("name=B", "{3-3}{4-4}", "[", "]"),
        ("name=C", "5-5", "6-6"),
    ]

    assert coerce_pivot_locs([PivotBox(fit_target="{1-1}{1-1}", style="draw=blue"), {"fit_target": "x", "style": "s"}]) == [
        ("{1-1}{1-1}", "draw=blue"),
        ("x", "s"),
    ]
    assert coerce_txt_with_locs([TextAt(coord="1-1", text="T", style="red"), {"coord": "2-2", "text": "U"}]) == [
        ("1-1", "T", "red"),
        ("2-2", "U", ""),
    ]
    assert coerce_rowechelon_paths([RowEchelonPath(tikz="\\draw A;"), {"tikz": "\\draw B;"}, 4]) == [
        "\\draw A;",
        "\\draw B;",
        "4",
    ]


def test_tex_outer_delims_infer_shape_from_normalized_body():
    rendered = tex(mat_rep="1 & 2 \\ 3 & 4", mat_format="rr", outer_delims=True)

    assert r"\SubMatrix({1-1}{2-2})[name=A0x0]" in rendered


def test_tex_outer_delims_requires_inferable_shape():
    with pytest.raises(ValueError, match="Could not infer outer_delims_span"):
        tex(mat_rep="", mat_format="r", outer_delims=True)
