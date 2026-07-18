import pytest


def test_ge_template_geometry_has_large_canvas():
    """GE template should provide a large canvas so callouts are not clipped.

    This is a template-level regression guard: if the page is too small or has
    zero margins, delimiter-attached callouts can extend to negative x/y and be
    clipped by LaTeX before tight-cropping.
    """

    from matrixlayout.ge import _tex

    tex_out = _tex(mat_rep="1", mat_format="r")

    # The template should specify both width and height, plus non-zero margins.
    assert "paperwidth=90in" in tex_out
    assert "paperheight=90in" in tex_out
    assert "left=50mm" in tex_out
    assert "right=50mm" in tex_out
    assert "top=50mm" in tex_out
    assert "bottom=50mm" in tex_out

    # Arrow callouts rely on arrows.meta for Stealth arrowheads.
    assert "arrows.meta" in tex_out

    # Template should provide anchor shorthands for user-supplied TikZ (e.g. node[west]).
    assert "west/.style={anchor=west}" in tex_out
    assert "east/.style={anchor=east}" in tex_out


def test_render_ge_tex_renders_delim_callouts_as_draw_commands():
    """Callouts must render as valid TikZ inside the template's tikzpicture."""

    from matrixlayout.ge import render_ge_tex
    from matrixlayout.nicematrix_decor import infer_ge_matrix_callouts

    # Two-layer GE stack: first has no E-block; second has E and A.
    matrices = [
        [None, [[1, 2, 5], [3, 4, 6]]],
        [[[1, 0], [0, 1]], [[1, 2, 5], [0, 2, 3]]],
    ]

    callouts = infer_ge_matrix_callouts(
        matrices,
        angle_deg=35,
        length_mm=12,
        anchor="top",
        color="blue",
    )

    tex = render_ge_tex(matrices=matrices, n_rhs=1, callouts=callouts)

    # Callouts are inserted into the tikzpicture.
    assert "\\begin{tikzpicture}" in tex
    assert "\\draw[" in tex

    # Attachment points should target SubMatrix delimiter nodes.
    assert "(A0-right.north)" in tex
    assert "(A1-right.north)" in tex
    assert "(E1-left.north)" in tex

    # Label nodes must use explicit anchors (TikZ does not accept bare 'west/east').
    assert "node[anchor=west]" in tex
    assert "node[anchor=east]" in tex

    # Default arrowhead uses arrows.meta's Stealth.
    assert "Stealth" in tex

    # Ensure we did not reintroduce explicit delimiter overrides in SubMatrix.
    assert "_{(" not in tex
    assert "_{ (" not in tex


def test_render_ge_tex_strict_callouts_reject_unknown_submatrix_name():
    """Strict mode should fail fast when a callout references an unknown name."""

    from matrixlayout.ge import render_ge_tex

    matrices = [[None, [[1, 2], [3, 4]]]]

    with pytest.raises(ValueError):
        render_ge_tex(
            matrices=matrices,
            callouts=[{"name": "NO_SUCH_NAME", "label": "X", "side": "right"}],
        )


def test_render_ge_tex_threads_document_preamble_and_fig_scale():
    """render_ge_tex/tex should expose document_preamble+fig_scale end-to-end."""

    from matrixlayout.ge import render_ge_tex

    matrices = [[None, [[1, 2], [3, 4]]]]

    tex = render_ge_tex(
        matrices=matrices,
        n_rhs=0,
        document_preamble=r"\usepackage{newtxtext,newtxmath}",
        fig_scale=0.75,
    )

    # document_preamble must appear in the pre-document area.
    assert r"\usepackage{newtxtext,newtxmath}" in tex

    # fig_scale should wrap the figure.
    assert r"\scalebox{0.75}" in tex


def test_render_ge_tex_left_column_labels_align_with_distinct_rows():
    """Left labels should occupy their matching matrix rows, not collapse into row one."""

    from matrixlayout.ge import render_ge_tex

    tex = render_ge_tex(
        matrices=[[[1, 0], [0, 1], [0, 0]]],
        label_rows=[{"grid": (0, 0), "side": "above", "labels": [["x1", "x2"]]}],
        label_cols=[{"grid": (0, 0), "side": "left", "labels": [["p1"], ["p2"], [""]]}],
        create_medium_nodes=True,
    )

    assert r"\NotEmpty & \text{x1} & \text{x2}" in tex
    assert r"\text{p1}\hspace{0.8mm} & 1 & 0" in tex
    assert r"\text{p2}\hspace{0.8mm} & 0 & 1" in tex
    assert r"\text{p1}\hspace{0.8mm} & \text{p2}" not in tex

