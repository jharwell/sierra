# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""
Tier-3 (value) regression tests for ``sierra.core.graphs``: blessed-image
comparison via pytest-mpl.

Engine-agnostic by design -- graph rendering depends only on the on-disk
``.mean`` + stat siblings, not on any pipeline/engine -- so this suite calls
``generate()`` directly against deterministic fixtures rather than running a
full SIERRA pipeline. It is invoked as its own nox session

Bless goldens:   pytest tests/ --mpl-generate-path=tests/goldens/graphs
Compare:         pytest tests/ --mpl
Smoke (no img):  pytest tests/            (asserts generate() ok + PNG written)

Presence/guard tests (missing input, wrong file count) are plain assertions
with no image, and run in every mode.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest
import networkx as nx

# Project packages
from sierra.core import graphs
from tests.regression.graphs import generate, conftest

# Absolute so generate mode (relative to CWD) and compare mode resolve to the
# SAME directory
BASELINE = str((pathlib.Path(__file__).parent / ".." / "goldens" / "graphs").resolve())
TOL = 8.0


def mpl(baseline):
    """Marker for single (non-parametrized) tests: fixes the golden filename.

    Parametrized tests use the bare ``@mpl_image_compare(baseline_dir=...)``
    marker instead and let pytest-mpl derive per-variant filenames from the
    test id.
    """
    return pytest.mark.mpl_image_compare(
        baseline_dir=BASELINE,
        filename=f"{baseline}.png",
        tolerance=TOL,
    )


def _run(pathset, generator, **kwargs):
    kwargs.setdefault("backend", "matplotlib")
    kwargs.setdefault("medium", conftest.CSV_MEDIUM)
    assert generator(pathset, **kwargs) is True
    return conftest.png_to_figure(conftest.produced_png(pathset))


# ===========================================================================
# summary_line
# ===========================================================================
_STATS = [
    ("mean", "none"),
    ("mean", "conf95"),
    ("mean", "bw"),
    ("median", "none"),
    ("median", "iqr"),
]


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("center,spread", _STATS)
@pytest.mark.parametrize("logy", [False, True], ids=["lin", "logy"])
def test_summary_line_stats(make_pathset, center, spread, logy):
    ps = make_pathset()
    generate.summary_data(ps.input_root, "summary", ncols=3, with_stats=True)
    return _run(
        ps,
        graphs.summary_line,
        input_stem="summary",
        output_stem="summary",
        title="Scaling study",
        xlabel="experiment",
        ylabel="value",
        legend=["throughput", "cost", "error"],
        xticks=list(range(generate.N_EXP)),
        stats_center=center,
        stats_spread=spread,
        logyscale=logy,
    )


@mpl("summary_line-text_large")
def test_summary_line_text_size(make_pathset):
    large_text = True
    ps = make_pathset()
    generate.summary_data(ps.input_root, "summary", ncols=2, with_stats=False)
    return _run(
        ps,
        graphs.summary_line,
        input_stem="summary",
        output_stem="summary",
        title="Scaling",
        xlabel="x",
        ylabel="y",
        legend=["throughput", "cost"],
        xticks=list(range(generate.N_EXP)),
        stats_center="mean",
        stats_spread="none",
        large_text=large_text,
    )


@mpl("summary_line-xticklabels")
def test_summary_line_xticklabels(make_pathset):
    ps = make_pathset()
    generate.summary_data(ps.input_root, "summary", ncols=1, with_stats=False)
    return _run(
        ps,
        graphs.summary_line,
        input_stem="summary",
        output_stem="summary",
        title="Categorical x",
        xlabel="config",
        ylabel="throughput",
        legend=["throughput"],
        xticks=list(range(generate.N_EXP)),
        xticklabels=[f"c{i}" for i in range(generate.N_EXP)],
        stats_center="mean",
        stats_spread="none",
    )


@mpl("summary_line-model")
def test_summary_line_with_model(make_pathset):
    ps = make_pathset()
    generate.summary_data(
        ps.input_root, "summary", ncols=2, with_stats=True, with_model=True
    )
    generate.summary_data(
        ps.model_root, "summary", ncols=2, with_stats=False, with_model=True
    )
    return _run(
        ps,
        graphs.summary_line,
        input_stem="summary",
        output_stem="summary",
        title="With model",
        xlabel="x",
        ylabel="y",
        legend=["throughput", "cost"],
        xticks=list(range(generate.N_EXP)),
        stats_center="mean",
        stats_spread="conf95",
    )


def test_summary_line_missing_input(make_pathset):
    ps = make_pathset()
    assert (
        graphs.summary_line(
            ps,
            input_stem="does_not_exist",
            output_stem="x",
            medium=conftest.CSV_MEDIUM,
            backend="matplotlib",
            title="t",
            xlabel="x",
            ylabel="y",
            legend=[],
            xticks=[],
            stats_center="mean",
            stats_spread="none",
        )
        is False
    )


# ===========================================================================
# stacked_line
# ===========================================================================
@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("center,spread", _STATS)
def test_stacked_line_stats(make_pathset, center, spread):
    ps = make_pathset()
    generate.timeseries_data(ps.input_root, "trace", with_stats=True)
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="Signal trace",
        xlabel="clock",
        ylabel="amplitude",
        stats_center=center,
        stats_spread=spread,
        legend=["reference", "measured", "drift", "baseline", "raw"],
    )


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("points", [False, True], ids=["nopts", "pts"])
def test_stacked_line_points(make_pathset, points):
    ps = make_pathset()
    generate.timeseries_data(ps.input_root, "trace", with_stats=False)
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="Signal trace",
        xlabel="clock",
        ylabel="amplitude",
        stats_center="mean",
        stats_spread="none",
        points=points,
        legend=["reference", "measured", "drift", "baseline", "raw"],
    )


@mpl("stacked_line-logy")
def test_stacked_line_logy(make_pathset):
    ps = make_pathset()
    generate.timeseries_data(ps.input_root, "trace", with_stats=False, positive=True)
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="Signal trace (log y)",
        xlabel="clock",
        ylabel="amplitude",
        stats_center="mean",
        stats_spread="none",
        logyscale=True,
        legend=["reference", "measured", "drift", "baseline", "raw"],
    )


@mpl("stacked_line-cols")
def test_stacked_line_col_subset(make_pathset):
    ps = make_pathset()
    generate.timeseries_data(
        ps.input_root, "trace", with_stats=False, cols=["reference", "measured"]
    )
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="Two channels",
        xlabel="clock",
        ylabel="amplitude",
        stats_center="mean",
        stats_spread="none",
        cols=["reference", "measured"],
        legend=["reference", "measured"],
    )


@mpl("stacked_line-xticklabels")
def test_stacked_line_xticklabels(make_pathset):
    ps = make_pathset()
    generate.timeseries_data(
        ps.input_root, "trace", with_stats=False, cols=["reference"]
    )
    n = generate.N_TICKS
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="Custom ticks",
        xlabel="phase",
        ylabel="amplitude",
        stats_center="mean",
        stats_spread="none",
        xticks=[float(i) for i in range(n)],
        xticklabels=[f"t{i}" for i in range(n)],
        legend=["reference"],
    )


@mpl("stacked_line-model")
def test_stacked_line_with_model(make_pathset):
    ps = make_pathset()
    generate.timeseries_data(
        ps.input_root,
        "trace",
        with_stats=False,
        cols=["reference", "measured"],
        with_model=True,
    )
    generate.timeseries_data(
        ps.model_root,
        "trace",
        with_stats=False,
        cols=["reference", "measured"],
        with_model=True,
    )
    return _run(
        ps,
        graphs.stacked_line,
        input_stem="trace",
        output_stem="trace",
        title="With model",
        xlabel="clock",
        ylabel="amplitude",
        stats_center="mean",
        stats_spread="none",
        legend=["reference", "measured"],
    )


# ===========================================================================
# heatmap (numeric)
# ===========================================================================
@mpl("heatmap-basic")
def test_heatmap_basic(make_pathset):
    ps = make_pathset()
    generate.heatmap_numeric_data(ps.input_root, "field")
    return _run(
        ps,
        graphs.heatmap,
        input_stem="field",
        output_stem="field",
        title="Ripple field",
        stats_center="mean",
        xlabel="x",
        ylabel="y",
        zlabel="amplitude",
    )


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize(
    "transpose",
    [
        False,
        True,
    ],
    ids=["normal", "transpose"],
)
def test_heatmap_transpose(make_pathset, transpose):
    ps = make_pathset()
    generate.heatmap_numeric_data(ps.input_root, "field")
    return _run(
        ps,
        graphs.heatmap,
        input_stem="field",
        output_stem="field",
        title="Field",
        stats_center="mean",
        xlabel="x",
        ylabel="y",
        zlabel="z",
        transpose=transpose,
    )


@mpl("heatmap-ticklabels")
def test_heatmap_ticklabels(make_pathset):
    ps = make_pathset()
    generate.heatmap_numeric_data(ps.input_root, "field", nx=6, ny=5)
    return _run(
        ps,
        graphs.heatmap,
        input_stem="field",
        output_stem="field",
        title="Labeled",
        stats_center="mean",
        xlabel="x",
        ylabel="y",
        zlabel="z",
        xticklabels=[f"X{i}" for i in range(6)],
        yticklabels=[f"Y{i}" for i in range(5)],
        xticks=[float(i) for i in range(6)],
        yticks=[float(i) for i in range(5)],
    )


@mpl("heatmap-large_text")
def test_heatmap_large_text(make_pathset):
    ps = make_pathset()
    generate.heatmap_numeric_data(ps.input_root, "field")
    return _run(
        ps,
        graphs.heatmap,
        input_stem="field",
        output_stem="field",
        title="Big text",
        stats_center="mean",
        xlabel="x",
        ylabel="y",
        zlabel="z",
        large_text=True,
    )


# ===========================================================================
# confusion_matrix
# ===========================================================================
@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("rotate", [False, True], ids=["norot", "rot"])
def test_confusion_matrix(make_pathset, rotate):
    ps = make_pathset()
    generate.confusion_data(ps.input_root, "cm")
    return _run(
        ps,
        graphs.confusion_matrix,
        input_stem="cm",
        output_stem="cm",
        title="Classifier",
        stats_center="mean",
        truth_col="truth",
        predicted_col="predicted",
        xlabels_rotate=rotate,
    )


@mpl("confusion-large_text")
def test_confusion_matrix_large_text(make_pathset):
    ps = make_pathset()
    generate.confusion_data(ps.input_root, "cm")
    return _run(
        ps,
        graphs.confusion_matrix,
        input_stem="cm",
        output_stem="cm",
        title="Classifier",
        stats_center="mean",
        truth_col="truth",
        predicted_col="predicted",
        large_text=True,
    )


# ===========================================================================
# scatterplot
# ===========================================================================
@mpl("scatter-wide")
def test_scatter_wide(make_pathset):
    ps = make_pathset()
    generate.scatter_wide_data(ps.input_root, "dose", which="dose")
    return _run(
        ps,
        graphs.scatterplot,
        input_stem="dose",
        output_stem="dose",
        title="Dose-response",
        xlabel="dose",
        ylabel="response",
        stats_center="mean",
        xcol="dose",
        ycol="response",
    )


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("kind", ["linear", "quadratic", "cubic", "log", "exp"])
def test_scatter_wide_bestfit(make_pathset, kind):
    import polars as pl

    ps = make_pathset()
    generate.scatter_long_data(ps.input_root, "fit", nexp=1, kind=kind)
    pl.read_csv(ps.input_root / "fit.mean").select(["x", "y"]).write_csv(
        ps.input_root / "fit.mean"
    )
    return _run(
        ps,
        graphs.scatterplot,
        input_stem="fit",
        output_stem="fit",
        title=f"{kind} fit",
        xlabel="x",
        ylabel="y",
        stats_center="mean",
        xcol="x",
        ycol="y",
        show_best_fit=True,
        best_fit_kind=kind,
    )


@mpl("scatter-long_multi")
def test_scatter_long_multiseries(make_pathset):
    ps = make_pathset()
    generate.scatter_long_data(ps.input_root, "multi", nexp=3, kind="linear")
    return _run(
        ps,
        graphs.scatterplot,
        input_stem="multi",
        output_stem="multi",
        title="Per-experiment",
        xlabel="x",
        ylabel="y",
        stats_center="mean",
        legend=["exp0", "exp1", "exp2"],
    )


@mpl("scatter-long_bestfit")
def test_scatter_long_bestfit(make_pathset):
    ps = make_pathset()
    generate.scatter_long_data(ps.input_root, "multi", nexp=3, kind="linear")
    return _run(
        ps,
        graphs.scatterplot,
        input_stem="multi",
        output_stem="multi",
        title="Per-exp + fit",
        xlabel="x",
        ylabel="y",
        stats_center="mean",
        legend=["exp0", "exp1", "exp2"],
        show_best_fit=True,
        best_fit_kind="linear",
    )


# ===========================================================================
# histogram
# ===========================================================================
@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("kind", ["overlay", "steps", "facet"])
def test_histogram_kinds(make_pathset, kind):
    ps = make_pathset()
    generate.histogram_data(ps.input_root, "dist", family="beta")
    return _run(
        ps,
        graphs.histogram,
        input_stem="dist",
        output_stem="dist",
        title="Beta family",
        stats_center="mean",
        cols=None,
        kind=kind,
        xlabel="value",
        ylabel="count",
        legend=["u-shaped", "bell", "j-shaped", "uniform"],
    )


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("bins", ["10", "25", "50"])
def test_histogram_bins(make_pathset, bins):
    ps = make_pathset()
    generate.histogram_data(ps.input_root, "dist", family="mixed")
    return _run(
        ps,
        graphs.histogram,
        input_stem="dist",
        output_stem="dist",
        title="Binning",
        stats_center="mean",
        cols=["lognormal"],
        kind="overlay",
        bins=bins,
        xlabel="value",
        ylabel="count",
    )


@mpl("histogram-subset")
def test_histogram_col_subset(make_pathset):
    ps = make_pathset()
    generate.histogram_data(ps.input_root, "dist", family="beta")
    return _run(
        ps,
        graphs.histogram,
        input_stem="dist",
        output_stem="dist",
        title="Two cols",
        stats_center="mean",
        cols=["u_shaped", "bell"],
        kind="overlay",
        xlabel="value",
        ylabel="count",
        legend=["U", "bell"],
    )


# ===========================================================================
# network
# ===========================================================================
@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("layout", ["spring", "spectral", "spiral"])
def test_network_layouts_scalefree(make_pathset, layout):
    ps = make_pathset()
    generate.network_graphml(ps.input_root, "net", kind="scale_free")
    return _run(
        ps,
        graphs.network,
        input_stem="net",
        output_stem="net",
        title="Scale-free",
        layout=layout,
        medium=conftest.GRAPHML_MEDIUM,
    )


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE, tolerance=TOL)
@pytest.mark.parametrize("layout", ["bfs", "planar"])
def test_network_layouts_tree(make_pathset, layout):
    ps = make_pathset()
    generate.network_graphml(ps.input_root, "net", kind="tree", directed=True)
    return _run(
        ps,
        graphs.network,
        input_stem="net",
        output_stem="net",
        title="Tree",
        layout=layout,
        medium=conftest.GRAPHML_MEDIUM,
    )


@mpl("network-attrs")
def test_network_attrs(make_pathset):
    ps = make_pathset()
    generate.network_graphml(ps.input_root, "net", kind="scale_free")
    return _run(
        ps,
        graphs.network,
        input_stem="net",
        output_stem="net",
        title="Attr-styled",
        layout="spring",
        node_color_attr="group",
        node_size_attr="degree",
        edge_weight_attr="weight",
        medium=conftest.GRAPHML_MEDIUM,
    )


def test_network_missing_input(make_pathset):
    ps = make_pathset()
    assert (
        graphs.network(
            ps,
            input_stem="nope",
            output_stem="x",
            backend="matplotlib",
            title="t",
            layout="spring",
            medium=conftest.GRAPHML_MEDIUM,
        )
        is False
    )
