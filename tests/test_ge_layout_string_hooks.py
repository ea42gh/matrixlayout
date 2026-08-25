# mypy: disable-error-code=call-arg

import pytest


from matrixlayout.ge import _tex, render_ge_tex


def test_render_ge_tex_rejects_singular_label_in_annotations():
    with pytest.raises(TypeError, match=r"annotations\[0\].*callouts"):
        render_ge_tex(matrices=[[[1]]], annotations=[{"grid": (0, 0), "label": "A", "side": "right"}])


def test_ge_tex_layout_preamble_is_validated_after_merge():
    # The GE template injects `body_preamble` into the document body. Guardrails
    # must apply even when the value comes from the layout spec.
    with pytest.raises(ValueError):
        _tex(
            mat_rep="1",
            mat_format="c",
            layout={"body_preamble": r"\\geometry{margin=0pt}"},
        )
