import pytest


def test_show_svg_requires_ipython(monkeypatch):
    import matrixlayout

    monkeypatch.setitem(__import__("sys").modules, "IPython.display", None)
    with pytest.raises(ImportError):
        matrixlayout.show_svg("<svg/>")
