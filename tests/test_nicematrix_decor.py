from matrixlayout.nicematrix_decor import render_delim_callout


def test_render_delim_callout_math_mode_wraps_label():
    tex = render_delim_callout({"name": "A0", "label": r"\mathbf{A}", "math_mode": True})
    assert "{$\\mathbf{A}$}" in tex

    tex_no_math = render_delim_callout({"name": "A0", "label": "Label", "math_mode": False})
    assert "{$Label$}" not in tex_no_math
