from matrixlayout.specs import GEGridSpec
from matrixlayout.ge import (
    _merge_grid_spec_inputs,
    _merge_label_specs,
    _build_label_maps,
    latexify,
)


def test_merge_grid_spec_inputs_prefers_explicit_and_defaults():
    spec = GEGridSpec(
        matrices=[[None, [[9]]]],
        Nrhs=0,
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
        _variable_labels,
        _kwargs,
    ) = _merge_grid_spec_inputs(
        grid_spec=spec,
        matrices=[[None, [[1]]]],
        Nrhs=0,
        formatter=latexify,
        outer_hspace_mm=6,
        block_vspace_mm=1,
        cell_align="r",
        block_align=None,
        block_valign=None,
        extension="",
        fig_scale=None,
        format_nrhs=True,
        decorators=None,
        decorations=None,
        strict=False,
        label_rows=None,
        label_cols=None,
        label_gap_mm=0.8,
        variable_labels=None,
        kwargs={},
    )
    assert matrices == [[None, [[1]]]]
    assert outer_hspace_mm == 9


def test_merge_label_specs_preserves_explicit_rows():
    specs = [{"grid": (0, 1), "label": "spec", "side": "above"}]
    label_rows = [{"grid": (0, 1), "rows": [["explicit"]], "side": "above"}]
    label_rows_out, label_cols_out, _decorations = _merge_label_specs(
        specs=specs,
        label_rows=label_rows,
        label_cols=None,
        decorations=None,
    )
    assert label_rows_out is not None
    assert "explicit" in str(label_rows_out)
    assert "spec" not in str(label_rows_out)


def test_merge_label_specs_uses_specs_when_no_explicit():
    specs = [{"grid": (0, 0), "rows": [["spec"]], "side": "above"}]
    label_rows_out, label_cols_out, _decorations = _merge_label_specs(
        specs=specs,
        label_rows=None,
        label_cols=None,
        decorations=None,
    )
    assert label_rows_out is not None
    assert "spec" in str(label_rows_out)
    assert label_cols_out is None


def test_merge_grid_spec_inputs_passes_spec_labels_when_no_explicit():
    spec = GEGridSpec(
        matrices=[[None, [[1]]]],
        Nrhs=0,
        outer_hspace_mm=6,
        label_rows=[{"grid": (0, 0), "rows": [["row"]], "side": "above"}],
        label_cols=[{"grid": (0, 0), "cols": [["col"]], "side": "left"}],
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
        _variable_labels,
        _kwargs,
    ) = _merge_grid_spec_inputs(
        grid_spec=spec,
        matrices=[[None, [[1]]]],
        Nrhs=0,
        formatter=latexify,
        outer_hspace_mm=6,
        block_vspace_mm=1,
        cell_align="r",
        block_align=None,
        block_valign=None,
        extension="",
        fig_scale=None,
        format_nrhs=True,
        decorators=None,
        decorations=None,
        strict=False,
        label_rows=None,
        label_cols=None,
        label_gap_mm=0.8,
        variable_labels=None,
        kwargs={},
    )
    assert label_rows is not None
    assert "row" in str(label_rows)
    assert label_cols is not None
    assert "col" in str(label_cols)


def test_build_label_maps_tracks_overlay_and_variable_labels():
    label_cols = [
        {"grid": (0, 1), "cols": [["left"]], "side": "left"},
        {"grid": (0, 1), "cols": [["overlay"]], "side": "right", "overlay": True},
    ]
    variable_labels = [{"grid": (0, 1), "rows": [["var"]], "side": "below"}]
    label_rows_map, label_cols_map, overlay = _build_label_maps(
        n_block_rows=1,
        n_block_cols=2,
        label_rows=None,
        label_cols=label_cols,
        variable_labels=variable_labels,
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
            label_rows=[{"grid": (2, 0), "rows": [["x"]], "side": "above"}],
            label_cols=None,
            variable_labels=None,
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
            label_rows=[{"grid": (0, 0), "rows": [["x"]], "side": "top"}],
            label_cols=None,
            variable_labels=None,
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
            variable_labels=None,
            allow_overlay=False,
            strict=True,
        )
    except ValueError as err:
        assert "dict" in str(err)
    else:
        raise AssertionError("Expected ValueError for non-dict label spec")


def test_build_label_maps_overlay_excludes_label_cols():
    label_cols = [
        {"grid": (0, 0), "cols": [["x"]], "side": "left"},
        {"grid": (0, 0), "cols": [["y"]], "side": "right", "overlay": True},
    ]
    label_rows_map, label_cols_map, overlay = _build_label_maps(
        n_block_rows=1,
        n_block_cols=1,
        label_rows=None,
        label_cols=label_cols,
        variable_labels=None,
        allow_overlay=True,
    )
    assert (0, 0, "left") in label_cols_map
    assert (0, 0, "right") not in label_cols_map
    assert overlay and overlay[0]["overlay"] is True
