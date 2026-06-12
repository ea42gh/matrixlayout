from matrixlayout.specs import GEGridSpec
from matrixlayout.ge import (
    _merge_grid_spec_inputs,
    _merge_label_specs,
    _build_label_maps,
    latexify,
    render_ge_tex,
)
from matrixlayout.ge_spec_merge import merge_scalar_default
from matrixlayout.ge_spec_merge import coerce_grid_spec, coerce_layout_spec, merge_scalar
from matrixlayout.ge_labels import build_label_maps, grid_label_layouts, merge_label_specs


def test_merge_grid_spec_inputs_prefers_explicit_and_defaults():
    spec = GEGridSpec(
        matrices=[[None, [[9]]]],
        n_rhs=0,
        outer_hspace_mm=9,
    )
    (
        matrices,
        _nrhs,
        _formatter,
        outer_hspace_mm,
        _block_vspace_mm,
        _cell_align,
        _block_align,
        _block_valign,
        _extension,
        _fig_scale,
        _format_nrhs,
        _decorators,
        _decorations,
        _strict,
        _label_rows,
        _label_cols,
        _label_gap_mm,
        _kwargs,
    ) = _merge_grid_spec_inputs(
        grid_spec=spec,
        matrices=[[None, [[1]]]],
        n_rhs=0,
        formatter=latexify,
        outer_hspace_mm=6,
        block_vspace_mm=1,
        cell_align="r",
        block_align=None,
        block_valign=None,
        document_preamble="",
        fig_scale=None,
        format_nrhs=True,
        decorators=None,
        decorations=None,
        strict=False,
        label_rows=None,
        label_cols=None,
        label_gap_mm=0.8,
        kwargs={},
    )
    assert matrices == [[None, [[1]]]]
    assert outer_hspace_mm == 9


def test_ge_merge_scalar_default_lets_spec_override_renderer_default():
    assert merge_scalar_default("n_rhs", None, 1, 0) == 1


def test_ge_merge_scalar_default_preserves_non_default_explicit_over_spec_default():
    assert merge_scalar_default("format_nrhs", False, True, True) is False


def test_ge_merge_scalar_base_cases_and_conflict():
    assert merge_scalar("x", "explicit", None) == "explicit"
    assert merge_scalar("x", None, "spec") == "spec"
    assert merge_scalar("x", "same", "same") == "same"
    try:
        merge_scalar("x", "explicit", "spec")
    except ValueError as exc:
        assert "Conflicting values for x" in str(exc)
    else:
        raise AssertionError("expected merge conflict")


def test_ge_coerce_spec_helpers_accept_none_objects_and_dicts():
    grid_spec = GEGridSpec(matrices=[[None]])

    assert coerce_grid_spec(None) is None
    assert coerce_grid_spec(grid_spec) is grid_spec
    assert coerce_grid_spec({"matrices": [[None]], "strict": False}).matrices == [[None]]
    assert coerce_layout_spec(None) is None


def test_ge_coerce_spec_helpers_reject_invalid_types():
    for helper in (coerce_grid_spec, coerce_layout_spec):
        try:
            helper("bad")
        except TypeError as exc:
            assert "must be" in str(exc)
        else:
            raise AssertionError("expected invalid spec type to raise")


def test_render_ge_tex_spec_nrhs_and_format_nrhs_override_defaults():
    spec = GEGridSpec(matrices=[[[1, 2, 3]]], n_rhs=1, format_nrhs=False)

    tex = render_ge_tex(spec=spec)

    assert r"\begin{NiceArray}[vlines-in-sub-matrix = I]{rrr}" in tex
    assert r"{rr|r}" not in tex


def test_render_ge_tex_spec_strict_is_not_overridden_by_default_false():
    spec = GEGridSpec(
        matrices=[[[1]]],
        decorators=[{"grid": (0, 0), "entries": [(9, 9)], "decorator": lambda tex: tex}],
        strict=True,
    )

    try:
        render_ge_tex(spec=spec)
    except ValueError as exc:
        assert "decorator selector did not match" in str(exc)
    else:
        raise AssertionError("expected spec strict=True to be honored")


def test_merge_label_specs_merges_annotations_with_explicit_rows():
    annotations = [{"grid": (0, 1), "labels": [["spec"]], "side": "above"}]
    label_rows = [{"grid": (0, 1), "labels": [["explicit"]], "side": "above"}]
    label_rows_out, label_cols_out, _decorations = _merge_label_specs(
        annotations=annotations,
        label_rows=label_rows,
        label_cols=None,
        decorations=None,
    )
    assert label_rows_out is not None
    assert "explicit" in str(label_rows_out)
    assert "spec" in str(label_rows_out)


def test_merge_label_specs_uses_annotations_when_no_explicit():
    annotations = [{"grid": (0, 0), "labels": [["spec"]], "side": "above"}]
    label_rows_out, label_cols_out, _decorations = _merge_label_specs(
        annotations=annotations,
        label_rows=None,
        label_cols=None,
        decorations=None,
    )
    assert label_rows_out is not None
    assert "spec" in str(label_rows_out)
    assert label_cols_out is None


def test_ge_label_module_helpers_match_public_aliases():
    annotations = [{"grid": (0, 0), "labels": [["x", "y"]], "side": "above"}]
    rows, cols = grid_label_layouts(annotations)
    assert rows == [{"grid": (0, 0), "side": "above", "labels": [["x", "y"]]}]
    assert cols == []

    direct_rows, direct_cols, direct_decorations = merge_label_specs(
        annotations=annotations,
        label_rows=None,
        label_cols=None,
        decorations=None,
    )
    compat_rows, compat_cols, compat_decorations = _merge_label_specs(
        annotations=annotations,
        label_rows=None,
        label_cols=None,
        decorations=None,
    )
    assert (direct_rows, direct_cols, direct_decorations) == (compat_rows, compat_cols, compat_decorations)

    direct_maps = build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=direct_rows,
        label_cols=direct_cols,
    )
    compat_maps = _build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=compat_rows,
        label_cols=compat_cols,
    )
    assert direct_maps == compat_maps


def test_merge_grid_spec_inputs_passes_spec_labels_when_no_explicit():
    spec = GEGridSpec(
        matrices=[[None, [[1]]]],
        n_rhs=0,
        outer_hspace_mm=6,
        label_rows=[{"grid": (0, 0), "labels": [["row"]], "side": "above"}],
        label_cols=[{"grid": (0, 0), "labels": [["col"]], "side": "left"}],
    )
    (
        _matrices,
        _nrhs,
        _formatter,
        _outer_hspace_mm,
        _block_vspace_mm,
        _cell_align,
        _block_align,
        _block_valign,
        _extension,
        _fig_scale,
        _format_nrhs,
        _decorators,
        _decorations,
        _strict,
        label_rows,
        label_cols,
        _label_gap_mm,
        _kwargs,
    ) = _merge_grid_spec_inputs(
        grid_spec=spec,
        matrices=[[None, [[1]]]],
        n_rhs=0,
        formatter=latexify,
        outer_hspace_mm=6,
        block_vspace_mm=1,
        cell_align="r",
        block_align=None,
        block_valign=None,
        document_preamble="",
        fig_scale=None,
        format_nrhs=True,
        decorators=None,
        decorations=None,
        strict=False,
        label_rows=None,
        label_cols=None,
        label_gap_mm=0.8,
        kwargs={},
    )
    assert label_rows is not None
    assert "row" in str(label_rows)
    assert label_cols is not None
    assert "col" in str(label_cols)


def test_build_label_maps_tracks_overlay_and_label_rows():
    label_cols = [
        {"grid": (0, 1), "labels": [["left"]], "side": "left"},
        {"grid": (0, 1), "labels": [["overlay"]], "side": "right", "overlay": True},
    ]
    label_rows_map, label_cols_map, overlay = _build_label_maps(
        n_block_rows=1,
        n_block_cols=2,
        label_rows=[{"grid": (0, 1), "labels": [["var"]], "side": "below"}],
        label_cols=label_cols,
        allow_overlay=True,
    )
    assert (0, 1, "below") in label_rows_map
    assert label_rows_map[(0, 1, "below")][0][0] == "var"
    assert (0, 1, "left") in label_cols_map
    assert overlay and overlay[0]["overlay"] is True


def test_build_label_maps_strict_rejects_bad_grid():
    try:
        _build_label_maps(
            n_block_rows=1,
            n_block_cols=1,
            label_rows=[{"grid": (2, 0), "labels": [["x"]], "side": "above"}],
            label_cols=None,
            allow_overlay=False,
            strict=True,
        )
    except ValueError as err:
        assert "out of range" in str(err)
    else:
        raise AssertionError("Expected ValueError for out-of-range grid")


def test_build_label_maps_strict_rejects_bad_side():
    try:
        _build_label_maps(
            n_block_rows=1,
            n_block_cols=1,
            label_rows=[{"grid": (0, 0), "labels": [["x"]], "side": "diagonal"}],
            label_cols=None,
            allow_overlay=False,
            strict=True,
        )
    except ValueError as err:
        assert "side" in str(err)
    else:
        raise AssertionError("Expected ValueError for invalid side")


def test_build_label_maps_strict_rejects_nondict():
    try:
        _build_label_maps(
            n_block_rows=1,
            n_block_cols=1,
            label_rows=[["x"]],
            label_cols=None,
            allow_overlay=False,
            strict=True,
        )
    except ValueError as err:
        assert "dict" in str(err)
    else:
        raise AssertionError("Expected ValueError for non-dict label spec")


def test_build_label_maps_overlay_excludes_label_cols():
    label_cols = [
        {"grid": (0, 0), "labels": [["x"]], "side": "left"},
        {"grid": (0, 0), "labels": [["y"]], "side": "right", "overlay": True},
    ]
    label_rows_map, label_cols_map, overlay = _build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=None,
        label_cols=label_cols,
        allow_overlay=True,
    )
    assert (0, 0, "left") in label_cols_map
    assert (0, 0, "right") not in label_cols_map
    assert overlay and overlay[0]["overlay"] is True
