# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for creating image files from ``.mean`` files for experiments.

See :ref:`plugins/proc/imagize` for usage documentation.

"""

# Core packages
import multiprocessing as mp
import typing as tp
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, batchroot, graphs, config
from sierra.core.pipeline.stage3 import gather
from sierra.plugins.proc.statistics import plugin as statistics
import sierra.core.plugin as pm

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Generate images for each :term:`Experiment` in the :term:`Batch Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-parallelism``.
    """
    config_path = pathlib.Path(cmdopts["project_config_root"]) / pathlib.Path(
        config.PROJECT_YAML.graphs
    )
    if utils.path_exists(config_path):
        _logger.info("Loading imagizing config for project=%s", cmdopts["project"])
        imagize_config = yaml.load(utils.utf8open(config_path), yaml.FullLoader)[
            "imagize"
        ]
    else:
        _logger.warning("%s does not exist--cannot imagize", config_path)
        return

    if not cmdopts["imagize_no_stats"]:
        statistics.proc_batch_exp(
            main_config, cmdopts, pathset, criteria, ImagizeInputGatherer
        )

    exp_to_imagize = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    parallelism = cmdopts["processing_parallelism"]

    tasks = []
    for exp in exp_to_imagize:
        exp_stat_root = pathset.stat_root / exp.name
        exp_imagize_root = pathset.imagize_root / exp.name
        exp_output_root = pathset.output_root / exp.name

        tasks.extend(
            _build_tasklist_for_exp(
                exp_stat_root,
                exp_imagize_root,
                exp_output_root,
                imagize_config,
                cmdopts["storage"],
            )
        )

    # 2025-06-06 [JRH]: This works around what is apparently a nasty memory leak
    # in hv caused by the hv.save() function for which the usual methods of
    # clearing memory/figures do not work.  The maxtasksperchild argument +
    # chunksize kills all the child threads periodically, which fixes the leak
    # problem, for now.
    _logger.debug("Starting %s workers, method=%s", parallelism, mp.get_start_method())
    with mp.Pool(processes=parallelism, maxtasksperchild=1) as pool:
        processed = pool.starmap_async(_worker, tasks, chunksize=10)

        _logger.debug("Waiting for workers to finish")
        processed.get()

    _logger.debug("All workers finished")


def _build_tasklist_for_exp(
    exp_stat_root: pathlib.Path,
    exp_imagize_root: pathlib.Path,
    exp_output_root: pathlib.Path,
    imagize_config: types.YAMLDict,
    storage: str,
) -> list[tuple[types.YAMLDict, dict]]:
    """Add all files from experiment to multiprocessing queue for processing.

    Enqueueing for processing is done at the file-level rather than
    per-experiment, so that for systems with more CPUs than experiments you
    still get maximum throughput.
    """
    res = []

    # There are two types of graphs currently supported:
    #
    # - Heatmaps, built from statistical data.
    #
    # - Network graphs, built from per-run data. We COULD average GraphML files,
    #   but doing so in a general way is tricky at best, and brittle at worst.
    for graph in imagize_config:
        if dict(graph)["type"] == "heatmap":
            res.extend(
                _build_task_for_heatmap(
                    graph, imagize_config, storage, exp_stat_root, exp_imagize_root
                )
            )

        elif dict(graph)["type"] == "network":
            res.extend(
                _build_task_for_network(
                    graph,
                    imagize_config,
                    storage,
                    exp_output_root,
                    exp_imagize_root,
                )
            )
        else:
            raise ValueError("Only {heatmap,network} output graphs supported.")

    return res


def _build_task_for_heatmap(
    graph: types.YAMLDict,
    imagize_config: types.YAMLDict,
    storage: str,
    exp_stat_root: pathlib.Path,
    exp_imagize_root: pathlib.Path,
) -> list[tuple[types.YAMLDict, dict]]:
    candidate = exp_stat_root / dict(graph)["src_stem"]
    res = []  # type: list[tuple[types.YAMLDict, dict]]

    if not candidate.is_dir():
        _logger.debug(
            "Configured imagize source <batch stat root>/%s does not exist",
            (candidate.relative_to(exp_stat_root)),
        )
        return res

    imagize_output_root = exp_imagize_root / candidate.relative_to(exp_stat_root)
    utils.dir_create_checked(imagize_output_root, exist_ok=True)

    for fpath in candidate.iterdir():
        assert (
            fpath.is_file()
        ), f"Imagize directory {candidate} must only contain files!"

        res.append(
            (
                imagize_config,
                {
                    "input_path": fpath,
                    "graph_stem": candidate.relative_to(exp_stat_root),
                    "imagize_output_root": imagize_output_root,
                    "batch_root": exp_stat_root.parent.parent,
                    "storage": storage,
                },
            )
        )
    return res


def _build_task_for_network(
    graph: types.YAMLDict,
    imagize_config: types.YAMLDict,
    storage: str,
    exp_output_root: pathlib.Path,
    exp_imagize_root: pathlib.Path,
) -> list[tuple[types.YAMLDict, dict]]:

    res = []
    for run_output_root in exp_output_root.iterdir():
        candidate = run_output_root / dict(graph)["src_stem"]
        if not candidate.is_dir():
            _logger.debug(
                "Configured imagize source <output root>/%s does not exist",
                (candidate.relative_to(exp_output_root)),
            )
            continue
        imagize_output_root = exp_imagize_root / candidate.relative_to(exp_output_root)
        utils.dir_create_checked(imagize_output_root, exist_ok=True)
        for fpath in candidate.iterdir():
            assert (
                fpath.is_file()
            ), f"Imagize directory {candidate} must only contain files!"

            res.append(
                (
                    imagize_config,
                    {
                        "input_path": fpath,
                        "graph_stem": dict(graph)["src_stem"],
                        "imagize_output_root": imagize_output_root,
                        "batch_root": exp_output_root.parent.parent,
                        "storage": storage,
                    },
                )
            )
    return res


def _worker(imagize_config: types.YAMLDict, imagize_opts: dict) -> None:

    _proc_single_exp(imagize_config, imagize_opts)


def _proc_single_exp(imagize_config: types.YAMLDict, imagize_opts: dict) -> None:
    """Create images from the averaged ``.mean`` files from a single experiment.

    If no ``.mean`` files suitable for averaging are found, nothing is done. See
    :ref:`plugins/proc/imagize` for per-engine descriptions of what
    "suitable" means.

    Arguments:

        imagize_config: Parsed YAML configuration for heatmaps.

        imagize_opts: Dictionary of imagizing options.
    """

    match = None
    for graph in imagize_config:
        if dict(graph)["src_stem"] == str(imagize_opts["graph_stem"]):
            match = graph

    if match is not None:
        graph_pathset = graphs.PathSet(
            input_root=imagize_opts["input_path"].parent,
            output_root=imagize_opts["imagize_output_root"],
            model_root=None,
            batchroot=imagize_opts["batch_root"],
        )

        # All input paths are of the form <dir>/<dir>_<NUMBER>.{extension}
        if dict(graph)["type"] == "heatmap":
            graphs.heatmap(
                pathset=graph_pathset,
                input_stem=imagize_opts["input_path"].stem,
                output_stem=imagize_opts["input_path"].stem,
                title=dict(match)["title"],
                medium=imagize_opts["storage"],
                xlabel="X",
                ylabel="Y",
                colnames=(
                    match.get("x", "x"),
                    match.get("y", "y"),
                    match.get("z", "z"),
                ),
                backend="matplotlib",
            )
        elif dict(graph)["type"] == "network":
            graphs.network(
                pathset=graph_pathset,
                layout=graph.get("layout", "spring"),
                input_stem=imagize_opts["input_path"].stem,
                output_stem=imagize_opts["input_path"].stem,
                title=dict(match)["title"],
                medium=imagize_opts["storage"],
                node_color_attr=graph.get("node_color_attr", None),
                node_size_attr=graph.get("node_size_attr", None),
                edge_color_attr=graph.get("edge_color_attr", None),
                edge_weight_attr=graph.get("edge_weight_attr", None),
                edge_label_attr=graph.get("edge_label_attr", None),
                backend="matplotlib",
            )

    else:
        _logger.warning(
            "No match for graph with src_stem='%s' found in configuration",
            imagize_opts["graph_stem"],
        )


class ImagizeInputGatherer(gather.BaseGatherer):
    """Gather :term:`Raw Output Data` files from all runs for imagizing.

    The configured output directory for each run is searched recursively for
    directories containing files to gather.  To be eligible for gathering and
    later processing, files must:

        - Be in a directory with the same name as the file, sans extension.

        - Be non-empty

        - Have a suffix which supported by the selected ``--storage`` plugin.

    Recursive nesting of files *within* a directory containing files to imagize
    is not supported--why would you do this anyway?
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        gather_opts: types.SimpleDict,
        processq: mp.Queue,
    ) -> None:
        super().__init__(main_config, gather_opts, processq)
        self.logger = logging.getLogger(__name__)

        self.config_path = (
            pathlib.Path(gather_opts["project_config_root"])
            / config.PROJECT_YAML.graphs
        )

        self.imagize_config = yaml.load(
            utils.utf8open(self.config_path), yaml.FullLoader
        )["imagize"]

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[gather.GatherSpec]:
        to_gather = []
        proj_output_root = run_output_root / str(self.run_metrics_leaf)
        plugin = pm.pipeline.get_plugin_module(self.gather_opts["storage"])

        for item in proj_output_root.rglob("*"):
            if not item.is_dir():
                continue

            for imagizable in item.iterdir():
                if (
                    not any(plugin.supports_input(s) for s in imagizable.suffixes)
                    and imagizable.stat().st_size > 0
                ):
                    continue

                if not any(
                    g["src_stem"] in str(imagizable) for g in self.imagize_config
                ):
                    continue

                if item.name in imagizable.name:
                    to_gather.append(
                        gather.GatherSpec(
                            exp_name=exp_name,
                            item_stem_path=imagizable.relative_to(proj_output_root),
                            collate_col=None,
                        )
                    )

        return to_gather


__all__ = [
    "proc_batch_exp",
]
