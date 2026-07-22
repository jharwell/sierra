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

# 3rd party packages
import numpy as np

# Project packages
import sierra.core.plugin as pm
from sierra.core import types, utils, batchroot, exproot, config, graphs
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs import gconfig


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
        "cols": loaded["cols"],
        "bins": loaded.get("bins", None),
        "kind": loaded["kind"],
        "legend": loaded.get("legend", loaded["cols"]),
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
                category_cfg = tp.cast(
                    types.YAMLDict, self.controller_config[category]
                )
                controllers = tp.cast(
                    list[types.YAMLDict], category_cfg["controllers"]
                )
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

        return [
            tp.cast(list[types.YAMLDict], self.graphs_config[k]) for k in enabled
        ]


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

            kind.func(
                pathset=graph_pathset,
                input_stem=str(graph["src_stem"]),
                output_stem=str(graph.get("dest_stem", graph["src_stem"])),
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
