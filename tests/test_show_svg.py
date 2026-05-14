import pytest


def test_show_svg_displays_without_returning_svg_text(monkeypatch):
    import types
    import matrixlayout

    displayed = []

    class FakeSVG:
        def __init__(self, svg):
            self.svg = svg

    fake_display = types.SimpleNamespace(
        SVG=FakeSVG,
        display=lambda obj: displayed.append(obj),
    )

    monkeypatch.setitem(__import__("sys").modules, "IPython.display", fake_display)

    result = matrixlayout.show_svg("<svg/>")

    assert result is None
    assert len(displayed) == 1
    assert isinstance(displayed[0], FakeSVG)
    assert displayed[0].svg == "<svg/>"


def test_show_svg_requires_ipython(monkeypatch):
    import matrixlayout

    monkeypatch.setitem(__import__("sys").modules, "IPython.display", None)
    with pytest.raises(ImportError):
        matrixlayout.show_svg("<svg/>")
