#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
Generate graphs within a single :term:`Experiment`.
"""

# Core packages
import copy
import typing as tp
import logging
import json
import pathlib
import functools

# 3rd party packages
import numpy as np
import polars as pl

# Project packages
import sierra.core.plugin as pm
from sierra.core import types, utils, batchroot, exproot, config, graphs, storage
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs import gconfig
from sierra.core.yaml import sources as srcspec


_logger = logging.getLogger(__name__)


class _GraphKind(tp.NamedTuple):
    """How to turn one validated graph definition into a rendered graph.

    Attributes:
        cli_flag: The ``cmdopts`` key of the ``--project-no-XX`` flag which
                  suppresses this kind of graph.

        label: Human-readable plural name, used in progress logging.

        func: The :mod:`sierra.core.graphs` entry point which renders it.

        medium: The storage medium the graph reads from.

        kwargs_fn: Maps a validated graph definition (plus cmdopts and the
                per-experiment pathset) onto the keyword arguments for `func`.

        wants_model_root: Whether this graph type can overlay model
                          predictions. Only linegraphs currently can.
    """

    cli_flag: str
    label: str
    func: tp.Callable[..., bool]
    medium: str
    kwargs_fn: tp.Callable[..., dict[str, tp.Any]]
    wants_model_root: bool = False


def _heatmap_kwargs(
    loaded: types.YAMLDict, cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> dict[str, tp.Any]:
    return {
        "title": loaded["title"],
        "xlabel": loaded["xlabel"],
        "ylabel": loaded["ylabel"],
        "zlabel": loaded["zlabel"],
        "colnames": (loaded["x"], loaded["y"], loaded["z"]),
    }


def _stacked_line_kwargs(
    loaded: types.YAMLDict, cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> dict[str, tp.Any]:
    return {
        "title": loaded["title"],
        "xlabel": loaded["xlabel"],
        "ylabel": loaded["ylabel"],
        "cols": loaded.get("cols", None),
        "legend": loaded.get("legend", loaded.get("cols", None)),
        "points": loaded["points"],
        "logyscale": loaded.get("logy", cmdopts["plot_log_yscale"]),
        "stats": cmdopts.get("dist_stats", "none"),
        "xticks": _xticks(cmdopts, pathset),
    }


def _confusion_matrix_kwargs(
    loaded: types.YAMLDict, cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> dict[str, tp.Any]:
    return {
        "title": loaded["title"],
        "truth_col": loaded["truth_col"],
        "predicted_col": loaded["predicted_col"],
        "xlabels_rotate": loaded["xlabels_rotate"],
    }


def _histogram_kwargs(
    loaded: types.YAMLDict, cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> dict[str, tp.Any]:
    return {
        "title": loaded["title"],
        "xlabel": loaded["xlabel"],
        "ylabel": loaded["ylabel"],
        "cols": loaded.get("cols", None),
        "bins": loaded.get("bins", None),
        "kind": loaded["kind"],
        "legend": loaded.get("legend", loaded.get("cols", None)),
    }


def _network_kwargs(
    loaded: types.YAMLDict, cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> dict[str, tp.Any]:
    return {
        "title": loaded["title"],
        "layout": loaded["layout"],
        "node_color_attr": loaded.get("node_color_attr", None),
        "node_size_attr": loaded.get("node_size_attr", None),
        "edge_color_attr": loaded.get("edge_color_attr", None),
        "edge_weight_attr": loaded.get("edge_weight_attr", None),
        "edge_label_attr": loaded.get("edge_label_attr", None),
    }


#: Maps the ``type`` of a graph onto everything needed to render it. Adding a
#: graph type is a single entry here plus a schema in
#: :mod:`sierra.core.graphs.schema`; there is no separate ``_generate_*()``
#: function to write and no new branch in :meth:`_ExpGraphGenerator.__call__`.
KINDS = {
    "stacked_line": _GraphKind(
        cli_flag="project_no_LN",
        label="Linegraphs",
        func=graphs.stacked_line,
        medium="storage.csv",
        kwargs_fn=_stacked_line_kwargs,
        wants_model_root=True,
    ),
    "heatmap": _GraphKind(
        cli_flag="project_no_HM",
        label="Heatmaps",
        func=graphs.heatmap,
        medium="storage.csv",
        kwargs_fn=_heatmap_kwargs,
    ),
    "confusion_matrix": _GraphKind(
        cli_flag="project_no_CM",
        label="Confusion matrices",
        func=graphs.confusion_matrix,
        medium="storage.csv",
        kwargs_fn=_confusion_matrix_kwargs,
    ),
    "histogram": _GraphKind(
        cli_flag="project_no_HG",
        label="Histograms",
        func=graphs.histogram,
        medium="storage.csv",
        kwargs_fn=_histogram_kwargs,
    ),
    "network": _GraphKind(
        cli_flag="project_no_NW",
        label="Networks",
        func=graphs.network,
        medium="storage.grapml",
        kwargs_fn=_network_kwargs,
    ),
}


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Generate intra-experiment graphs for a :term:`Batch Experiment`.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration


        criteria:  The :term:`Batch Criteria` used for the batch
                   experiment.
    """
    info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)
    assert info.exp_names is not None
    exp_to_gen = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, info.exp_names
    )

    if not exp_to_gen:
        return

    graphs_config = gconfig.load(cmdopts)
    intra_config = gconfig.section(graphs_config, "intra-exp")

    if intra_config is None:
        return

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")
    controller_config = loader.load_config(cmdopts, config.PROJECT_YAML.controllers)

    generator = _ExpGraphGenerator(
        main_config, controller_config, intra_config, cmdopts
    )
    for exp in exp_to_gen:
        exproots = exproot.PathSet(pathset, exp.name)

        if exproots.stat_root.is_dir():
            generator(exproots)
        else:
            _logger.warning(
                "Skipping experiment '%s': %s does not exist, or isn't a directory",
                exp,
                exproots.stat_root,
            )


class _ExpGraphGenerator:
    """Generates graphs from :term:`Processed Output Data` files.

    Which graphs are generated is controlled by YAML configuration files parsed
    in stage 4.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.

        main_config: Parsed dictionary of main YAML configuration

        controller_config: Parsed dictionary of controller YAML
                           configuration.

        graphs_config: Parsed and validated dictionary of intra-experiment
                       graph configuration.

        logger: The handle to the logger for this class. If you extend this
               class, you should save/restore this variable in tandem with
               overriding it in order to get logging messages have unique logger
               names between this class and your derived class, in order to
               reduce confusion.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        controller_config: tp.Optional[types.YAMLDict],
        graphs_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
    ) -> None:
        # Copy because we are modifying it and don't want to mess up the
        # arguments for graphs that are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.graphs_config = graphs_config
        self.controller_config = controller_config
        self.logger = logging.getLogger(__name__)

    def __call__(self, pathset: exproot.PathSet) -> None:
        """Generate all enabled intra-experiment graphs for one experiment.

        Each graph type in :data:`KINDS` is generated in turn, unless
        suppressed by its ``--project-no-XX`` cmdline flag.
        """
        utils.dir_create_checked(pathset.graph_root, exist_ok=True)

        targets = self._calc_targets()

        for gtype, kind in KINDS.items():
            if self.cmdopts[kind.cli_flag]:
                continue

            _generate(self.cmdopts, pathset, targets, gtype, kind)

    def _calc_targets(self) -> list[list[types.YAMLDict]]:
        """Calculate what intra-experiment graphs should be generated.

        Uses YAML configuration for controller and intra-experiment graphs.
        Returns a list of graph categories to generate.  The enabled graphs
        exist in their respective YAML configuration *and* are enabled by the
        YAML configuration for the selected controller.

        Filtering by graph *type* happens in :func:`_generate`, so a single
        list serves all graph types.
        """
        keys: list[str] = []
        if self.controller_config:
            for category in list(self.controller_config.keys()):
                if category not in self.cmdopts["controller"]:
                    continue
                category_cfg = tp.cast(types.YAMLDict, self.controller_config[category])
                controllers = tp.cast(list[types.YAMLDict], category_cfg["controllers"])
                for controller in controllers:
                    if controller["name"] not in self.cmdopts["controller"]:
                        continue

                    # valid to specify no graphs, and only to inherit graphs
                    keys = tp.cast(list[str], controller.get("graphs", []))
                    if "graphs_inherit" in controller:
                        inherits = tp.cast(
                            list[list[str]], controller["graphs_inherit"]
                        )
                        for inherit in inherits:
                            keys.extend(inherit)  # optional

        else:
            keys = list(self.graphs_config)
            self.logger.warning(
                "Missing controller graph config--generating all enabled "
                "intra-experiment graphs for all controllers: %s",
                keys,
            )

        # Get keys for enabled graphs, and strip out all configured graphs
        # which are not enabled.
        enabled = [k for k in self.graphs_config if k in keys]
        self.logger.debug("Enabled graph categories: %s", enabled)

        return [tp.cast(list[types.YAMLDict], self.graphs_config[k]) for k in enabled]


def _stat_exts(cmdopts: types.Cmdopts) -> list[str]:
    """Get the statistic file extensions an intra-exp graph reads for one stem.

    Mirrors the collation path: the mean is always present, with dispersion
    (conf95) and/or box-and-whisker (bw) extensions added per ``--dist-stats``.
    An intra-exp graph reads one file per extension (mean line plus error
    bands), so a multi-source graph must join per extension.
    """
    exts = dict(config.STATS["mean"].exts)

    dist = cmdopts.get("dist_stats", "none")
    if dist in ("conf95", "all"):
        exts.update(config.STATS["conf95"].exts)
    if dist in ("bw", "all"):
        exts.update(config.STATS["bw"].exts)

    return list(exts.values())


def _materialize_sources(
    graph: dict,
    input_root: "pathlib.Path",
    medium: str,
    cmdopts: types.Cmdopts,
) -> str:
    """Join a multi-source graph's inputs into one derived file *family*.

    An intra-exp graph reads a *family* of statistic files per stem (``.mean``
    plus, per ``--dist-stats``, dispersion/box-whisker extensions) to draw the
    line and its error bands. So for each such extension, the selected+renamed
    columns from every source are read from ``<file><ext>``, concatenated
    horizontally on a shared row axis, and written to ``<derived_stem><ext>``.
    The derived stem is returned for the plotter, which then reads the whole
    family exactly as it would for a single ``src``.

    Sources have already been validated by gconfig (no duplicate columns within
    a source, no unresolved cross-source collisions).
    """
    # normalize once; the (file, col_map) pairs are ext-independent.
    pairs = []  # type: list[tuple[str, srcspec.ColMap]]
    for s in graph["sources"]:
        result = srcspec.normalize_source(s, "sources", [])
        # gconfig already validated these, so normalization cannot fail here.
        assert result is not None
        pairs.append(result)

    for ext in _stat_exts(cmdopts):
        n_rows = None  # type: tp.Optional[int]
        frames = []  # type: list[pl.DataFrame]

        for file, col_map in pairs:
            ipath = input_root / (file + ext)
            if not utils.path_exists(ipath):
                # A source missing this statistic entirely: skip the whole
                # extension rather than emit a partial join. (The mean is always
                # written; optional dispersion stats may legitimately be
                # absent.)
                _logger.trace(
                    "Skipping materializing %s stats for multi-source graph %s: %s does not exist",
                    ext,
                    graph["dest"],
                    ipath,
                )
                frames = []
                break

            df = storage.df_read(ipath, medium)

            if n_rows is None:
                n_rows = df.height
            elif df.height != n_rows:
                _logger.warning(
                    (
                        "Skipping materializing %s stats for multi-source graph "
                        "'%s': source '%s%s' has %s rows, "
                        "expected %s (all sources must share a row axis)"
                    ),
                    ext,
                    graph["dest"],
                    file,
                    ext,
                    df.height,
                    n_rows,
                )
                continue

            # Select only the configured columns that this statistic file
            # actually has. Dispersion stats (stddev/min/max) may cover a subset
            # of the columns the mean does; this mirrors the single-'src'
            # path, where the plotter uses whatever columns each stat file holds
            # rather than requiring every column in every file.
            present = [(src, out) for src, out in col_map if src in df.columns]
            if not present:
                _logger.trace(
                    "Skipping materializing %s stats for multi-source graph %s: not all columns in %s does exist",
                    ext,
                    graph["dest"],
                    ipath,
                )
                continue

            frames.append(df.select([pl.col(src).alias(out) for src, out in present]))

        if not frames:
            continue

        # Equal-height horizontal join. The row-axis guard above already
        # guarantees every frame has the same height, so a plain column-wise
        # stack is correct; hstack (unlike concat(how="horizontal"), which is
        # deprecated for unequal heights and would null-pad) keeps that strict
        # semantics and adds no null padding.
        joined = functools.reduce(lambda a, b: a.hstack(b), frames)
        storage.df_write(joined, input_root / (graph["dest"] + ext), medium)
        _logger.trace(
            "Materialized sources for %s to %s",
            graph["dest"],
            input_root / (graph["dest"] + ext),
        )
    return graph["dest"]


def _generate(
    cmdopts: types.Cmdopts,
    pathset: exproot.PathSet,
    targets: list[list[types.YAMLDict]],
    gtype: str,
    kind: _GraphKind,
) -> None:
    """Render every graph of one type from :term:`Processed Output Data` files.

    Config has already been validated by :mod:`gconfig`, so the definitions
    reaching here are known-conformant and can be indexed directly.
    """
    _logger.info(
        "%s from <batch_root>/%s",
        kind.label,
        pathset.stat_root.relative_to(pathset.parent),
    )

    for category in targets:
        for graph in category:
            if graph["type"] != gtype:
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))

            graph_pathset = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=pathset.model_root if kind.wants_model_root else None,
            )

            # A graph names its input either with a single 'src' or with
            # 'sources' (columns drawn from several files, joined). For the
            # latter, materialize the joined frame into a single derived file
            # here, so the plotter -- which reads one file by stem -- is
            # unchanged. gconfig has already enforced exactly-one and that a
            # multi-source graph carries an explicit dest.
            if "sources" in graph:
                input_stem = _materialize_sources(
                    graph, graph_pathset.input_root, kind.medium, cmdopts
                )
                output_stem = str(graph["dest"])
            else:
                input_stem = str(graph["src"])
                output_stem = str(graph.get("dest", graph["src"]))

            kind.func(
                pathset=graph_pathset,
                input_stem=input_stem,
                output_stem=output_stem,
                medium=kind.medium,
                backend=str(graph.get("backend", cmdopts["graphs_backend"])),
                large_text=cmdopts["plot_large_text"],
                **kind.kwargs_fn(graph, cmdopts, pathset),
            )


def _xticks(
    cmdopts: types.Cmdopts, pathset: exproot.PathSet
) -> tp.Optional[np.ndarray]:
    """Compute X tick values for intra-experiment linegraphs.

    Engines which can report their experiment setup give us a real time axis;
    those which can't fall back to row indices (signalled by ``None``).
    """
    module = pm.pipeline.get_plugin_module(cmdopts["engine"])

    if not hasattr(module, "expsetup_from_def"):
        return None

    module2 = pm.pipeline.get_plugin_module(cmdopts["expdef"])
    pkl_def = module2.unpickle(pathset.input_root / config.PICKLE_LEAF)

    info = module.expsetup_from_def(pkl_def)

    return np.linspace(
        0,
        info["duration"],
        int(
            info["duration"]
            * info["n_ticks_per_sec"]
            * cmdopts["exp_n_datapoints_factor"]
        ),
    )


__all__ = [
    "KINDS",
    "_ExpGraphGenerator",
    "proc_batch_exp",
]
