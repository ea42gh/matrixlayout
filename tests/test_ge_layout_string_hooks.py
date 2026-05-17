import pytest


from matrixlayout.ge import tex


def test_ge_tex_layout_merges_document_and_body_preamble_strings():
    tex_out = tex(
        mat_rep="1",
        mat_format="c",
        document_preamble="%EXPL-DOC\n",
        body_preamble="%EXPL-BODY\n",
        layout={
            "document_preamble": "%SPEC-DOC\n",
            "body_preamble": "%SPEC-BODY\n",
        },
        outer_delims=False,
    )

    # Document preamble appears before \begin{document}.
    assert "%SPEC-DOC" in tex_out
    assert "%EXPL-DOC" in tex_out
    assert tex_out.index("%SPEC-DOC") < tex_out.index("%EXPL-DOC")

    # Body preamble appears after \begin{document}.
    assert "%SPEC-BODY" in tex_out
    assert "%EXPL-BODY" in tex_out
    assert tex_out.index("%SPEC-BODY") < tex_out.index("%EXPL-BODY")


def test_ge_tex_accepts_canonical_hook_names():
    tex_out = tex(
        mat_rep="1",
        mat_format="c",
        document_preamble="%EXPL-DOC\n",
        body_preamble="%EXPL-BODY\n",
        layout={
            "document_preamble": "%SPEC-DOC\n",
            "body_preamble": "%SPEC-BODY\n",
        },
        outer_delims=False,
    )

    assert "%SPEC-DOC" in tex_out
    assert "%EXPL-DOC" in tex_out
    assert tex_out.index("%SPEC-DOC") < tex_out.index("%EXPL-DOC")
    assert "%SPEC-BODY" in tex_out
    assert "%EXPL-BODY" in tex_out
    assert tex_out.index("%SPEC-BODY") < tex_out.index("%EXPL-BODY")


def test_ge_tex_rejects_removed_hook_aliases():
    with pytest.raises(TypeError, match="unexpected keyword argument 'extension'"):
        tex(mat_rep="1", mat_format="c", extension="%old")
    with pytest.raises(TypeError, match="unexpected keyword argument 'preamble'"):
        tex(mat_rep="1", mat_format="c", preamble="%old")


def test_ge_tex_layout_preamble_is_validated_after_merge():
    # The GE template injects `body_preamble` into the document body. Guardrails
    # must apply even when the value comes from the layout spec.
    with pytest.raises(ValueError):
        tex(
            mat_rep="1",
            mat_format="c",
            layout={"body_preamble": r"\\geometry{margin=0pt}"},
        )
