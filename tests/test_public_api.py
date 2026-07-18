import pytest


def test_top_level_all_excludes_generic_ge_aliases():
    import matrixlayout

    assert "tex" not in matrixlayout.__all__
    assert "svg" not in matrixlayout.__all__
    assert "render_ge_tex" in matrixlayout.__all__
    assert "render_ge_svg" in matrixlayout.__all__
    assert "grid_bundle" in matrixlayout.__all__
    assert "GEGridBundle" in matrixlayout.__all__
    assert "qr_grid_bundle" in matrixlayout.__all__
    assert "QRGridBundle" in matrixlayout.__all__


def test_top_level_tex_alias_is_not_available():
    import matrixlayout

    name = "tex"
    with pytest.raises(AttributeError):
        getattr(matrixlayout, name)


def test_top_level_svg_alias_is_not_available():
    import matrixlayout

    name = "svg"
    with pytest.raises(AttributeError):
        getattr(matrixlayout, name)


def test_top_level_star_import_omits_generic_ge_aliases():
    namespace = {}
    exec("from matrixlayout import *", namespace)

    assert "tex" not in namespace
    assert "svg" not in namespace
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
