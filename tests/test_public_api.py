import pytest


def test_top_level_all_excludes_generic_ge_aliases():
    import matrixlayout

    assert "tex" not in matrixlayout.__all__
    assert "svg" not in matrixlayout.__all__
    assert "render_ge_tex" in matrixlayout.__all__
    assert "render_ge_svg" in matrixlayout.__all__


def test_top_level_tex_alias_is_not_available():
    import matrixlayout

    with pytest.raises(AttributeError):
        matrixlayout.tex


def test_top_level_svg_alias_is_not_available():
    import matrixlayout

    with pytest.raises(AttributeError):
        matrixlayout.svg


def test_top_level_star_import_omits_generic_ge_aliases():
    namespace = {}
    exec("from matrixlayout import *", namespace)

    assert "tex" not in namespace
    assert "svg" not in namespace
    assert namespace["render_ge_tex"]
    assert namespace["render_ge_svg"]
