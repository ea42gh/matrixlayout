import pytest


from matrixlayout.ge import tex


def test_ge_tex_layout_merges_extension_and_preamble_strings():
    tex_out = tex(
        mat_rep="1",
        mat_format="c",
        extension="%EXPL-EXT\n",
        preamble="%EXPL-PRE\n",
        layout={
            "extension": "%SPEC-EXT\n",
            "preamble": "%SPEC-PRE\n",
        },
        outer_delims=False,
    )

    # Extension appears before \begin{document}.
    assert "%SPEC-EXT" in tex_out
    assert "%EXPL-EXT" in tex_out
    assert tex_out.index("%SPEC-EXT") < tex_out.index("%EXPL-EXT")

    # Preamble (body hook) appears after \begin{document}.
    assert "%SPEC-PRE" in tex_out
    assert "%EXPL-PRE" in tex_out
    assert tex_out.index("%SPEC-PRE") < tex_out.index("%EXPL-PRE")


def test_ge_tex_layout_preamble_is_validated_after_merge():
    # The GE template injects `preamble` into the document body. Guardrails
    # must apply even when the value comes from the layout spec.
    with pytest.raises(ValueError):
        tex(
            mat_rep="1",
            mat_format="c",
            layout={"preamble": r"\\geometry{margin=0pt}"},
        )
