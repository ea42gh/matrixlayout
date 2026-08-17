# mypy: disable-error-code="truthy-function,var-annotated"

def test_top_level_exports_expected_names():
    import matrixlayout

    expected = {
        "DelimCallout",
        "DelimCalloutDict",
        "GEGridBundle",
        "GEGridSpec",
        "QRGridBundle",
        "QRGridSpec",
        "__build__",
        "__version__",
        "backsubst_svg",
        "backsubst_tex",
        "decorate_tex_entries",
        "decorations_help",
        "decorator_bf",
        "decorator_bg",
        "decorator_box",
        "decorator_color",
        "get_environment",
        "grid_bundle",
        "grid_highlight_specs",
        "grid_label_layouts",
        "grid_line_specs",
        "infer_ge_matrix_callouts",
        "latexify",
        "make_decorator",
        "qr_grid_bundle",
        "render_delim_callout",
        "render_delim_callouts",
        "render_eig_svg",
        "render_eig_tex",
        "render_ge_svg",
        "render_ge_tex",
        "render_ge_tex_specs",
        "render_qr_svg",
        "render_qr_tex",
        "resolve_ge_grid_name",
        "resolve_qr_grid_name",
        "sel_all",
        "sel_box",
        "sel_col",
        "sel_cols",
        "sel_entry",
        "sel_row",
        "sel_rows",
        "sel_vec",
        "sel_vec_range",
        "show_svg",
        "validate_callouts",
        "validate_ge_spec",
        "validate_qr_spec",
    }
    assert set(matrixlayout.__all__) == expected


def test_top_level_star_import_exports_public_api():
    namespace = {}
    exec("from matrixlayout import *", namespace)

    assert namespace["render_ge_tex"]
    assert namespace["render_ge_svg"]
    assert namespace["grid_bundle"]
    assert namespace["GEGridBundle"]
    assert namespace["qr_grid_bundle"]
    assert namespace["QRGridBundle"]


def test_top_level_grid_bundle_api_is_symmetric():
    import matrixlayout

    ge_bundle = matrixlayout.grid_bundle([[1]])
    assert isinstance(ge_bundle, matrixlayout.GEGridBundle)
    assert ge_bundle.submatrix_spans

    qr_bundle = matrixlayout.qr_grid_bundle([[1]])
    assert isinstance(qr_bundle, matrixlayout.QRGridBundle)
    assert qr_bundle.submatrix_spans


def test_ge_module_generic_tex_svg_aliases_are_not_available():
    import matrixlayout.ge as ge

    assert not hasattr(ge, "tex")
    assert not hasattr(ge, "svg")
    assert ge.render_ge_tex
    assert ge.render_ge_svg
