import pytest

from matrixlayout.ge import (
    _extract_submatrix_names,
    _figure_scale_wrappers,
    _merge_layout_fields,
    _merge_layout_string_hooks,
    _render_matrix_callouts,
    _submatrix_spans_with_outer_delims,
    tex,
)
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
from matrixlayout.specs import GELayoutSpec, PivotBox, RowEchelonPath, SubMatrixLoc, TextAt


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


def test_ge_layout_string_hook_helper_merges_spec_first():
    document_preamble, body_preamble = _merge_layout_string_hooks(
        spec=GELayoutSpec(document_preamble="spec-doc", body_preamble="spec-body"),
        document_preamble="explicit-doc",
        body_preamble="explicit-body",
    )

    assert document_preamble == "spec-doc\nexplicit-doc"
    assert body_preamble == "spec-body\nexplicit-body"
    assert _merge_layout_string_hooks(spec=None, document_preamble="d", body_preamble="b") == ("d", "b")


def test_ge_layout_field_helper_merges_layout_values_and_callouts():
    result = _merge_layout_fields(
        spec=GELayoutSpec(
            nice_options="spec-opt",
            landscape=True,
            create_cell_nodes=False,
            create_extra_nodes=True,
            create_medium_nodes=True,
            outer_delims=True,
            outer_delims_name="SpecName",
            outer_delims_span=(2, 3),
            codebefore=["spec-code"],
            submatrix_locs=[("name=S", "1-1", "1-1")],
            submatrix_names=["S"],
            pivot_locs=[("spec-pivot", "draw")],
            txt_with_locs=[("1-1", "spec-text", "")],
            rowechelon_paths=["spec-path"],
            callouts=[{"name": "S", "label": "spec"}],
            matrix_labels=[{"name": "S", "label": "matrix"}],
        ),
        nice_options=None,
        landscape=None,
        create_cell_nodes=None,
        create_extra_nodes=None,
        create_medium_nodes=None,
        outer_delims=None,
        outer_delims_name=None,
        outer_delims_span=None,
        codebefore=["explicit-code"],
        submatrix_locs=None,
        submatrix_names=None,
        pivot_locs=None,
        txt_with_locs=None,
        rowechelon_paths=None,
        callouts=[{"name": "S", "label": "explicit"}],
        matrix_labels=[{"name": "S", "label": "kw-label"}],
    )

    (
        nice_options,
        landscape,
        create_cell_nodes,
        create_extra_nodes,
        create_medium_nodes,
        outer_delims,
        outer_delims_name,
        outer_delims_span,
        codebefore,
        submatrix_locs,
        submatrix_names,
        pivot_locs,
        txt_with_locs,
        rowechelon_paths,
        callouts,
    ) = result

    assert nice_options == "spec-opt"
    assert landscape is True
    assert create_cell_nodes is False
    assert create_extra_nodes is True
    assert create_medium_nodes is True
    assert outer_delims is True
    assert outer_delims_name == "SpecName"
    assert outer_delims_span == (2, 3)
    assert codebefore == ["explicit-code", "spec-code"]
    assert submatrix_locs == [("name=S", "1-1", "1-1")]
    assert submatrix_names == ["S"]
    assert pivot_locs == [("spec-pivot", "draw")]
    assert txt_with_locs == [("1-1", "spec-text", "")]
    assert rowechelon_paths == ["spec-path"]
    assert callouts == [
        {"name": "S", "label": "explicit"},
        {"name": "S", "label": "spec"},
        {"name": "S", "label": "matrix"},
        {"name": "S", "label": "kw-label"},
    ]


def test_ge_layout_field_helper_passes_through_without_layout():
    result = _merge_layout_fields(
        spec=None,
        nice_options="opt",
        landscape=False,
        create_cell_nodes=True,
        create_extra_nodes=False,
        create_medium_nodes=False,
        outer_delims=False,
        outer_delims_name="Outer",
        outer_delims_span=(1, 1),
        codebefore=["code"],
        submatrix_locs=[("name=A", "1-1", "1-1")],
        submatrix_names=["A"],
        pivot_locs=[("p", "")],
        txt_with_locs=[("1-1", "t", "")],
        rowechelon_paths=["path"],
        callouts=[{"name": "A", "label": "A"}],
        matrix_labels=[{"name": "A", "label": "ignored"}],
    )

    assert result[0] == "opt"
    assert result[8] == ["code"]
    assert result[-1] == [{"name": "A", "label": "A"}]


def test_ge_figure_scale_wrapper_helper_variants():
    assert _figure_scale_wrappers(None) == ("", "")
    assert _figure_scale_wrappers(1.0) == ("", "")
    assert _figure_scale_wrappers(1.2) == (r"\scalebox{1.2}{%", "}")
    assert _figure_scale_wrappers(r"\resizebox{0.5\textwidth}{!}{%") == (r"\resizebox{0.5\textwidth}{!}{%", "")
    assert _figure_scale_wrappers("   ") == ("", "")


def test_ge_submatrix_span_helper_adds_or_preserves_outer_delimiters():
    assert _submatrix_spans_with_outer_delims(
        submatrix_locs=None,
        outer_delims=True,
        outer_delims_name="Outer",
        outer_delims_span=None,
        mat_rep_norm=r"1 & 2 \\ 3 & 4",
    ) == [("name=Outer", "{1-1}{2-2}")]

    explicit = [("name=A", "1-1", "1-1")]
    assert _submatrix_spans_with_outer_delims(
        submatrix_locs=explicit,
        outer_delims=True,
        outer_delims_name="Outer",
        outer_delims_span=(9, 9),
        mat_rep_norm="",
    ) == [("name=A", "{1-1}{1-1}")]


def test_ge_submatrix_name_extraction_helper_skips_empty_options():
    assert _extract_submatrix_names([(), ("", "{1-1}{1-1}"), ("draw", "{1-1}{1-1}"), ("name=A, draw", "{1-1}{1-1}")]) == [
        "A"
    ]


def test_ge_render_matrix_callouts_helper_merges_labels_and_wraps_errors():
    assert _render_matrix_callouts(callouts=None, matrix_labels=None, sub_spans=[], callout_name_map=None) == []

    rendered = _render_matrix_callouts(
        callouts=[{"name": "A", "label": "A", "side": "right"}],
        matrix_labels=[{"name": "B", "label": "B", "side": "left"}],
        sub_spans=[("name=A", "{1-1}{1-1}"), ("name=B", "{1-1}{1-1}")],
        callout_name_map=None,
    )
    assert len(rendered) == 2
    assert "A-right" in rendered[0]
    assert "B-left" in rendered[1]

    with pytest.raises(ValueError, match="Failed to render callouts"):
        _render_matrix_callouts(
            callouts=[{"name": "missing", "label": "X"}],
            matrix_labels=None,
            sub_spans=[("name=A", "{1-1}{1-1}")],
            callout_name_map=None,
        )
