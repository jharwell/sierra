# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for creating image files from ``.mean`` files for experiments.

See :ref:`usage/rendering` for usage documentation.

"""

# Core packages
import multiprocessing as mp
import logging
import pathlib
import typing as tp

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, batchroot, graphs


_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    HM_config: types.YAMLDict,
    criteria: bc.IConcreteBatchCriteria,
) -> None:
    """
    Generate images for each :term:`Experiment` in the :term:`Batch Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-serial``.
    """
    exp_to_imagize = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria
    )

    parallelism = cmdopts["processing_parallelism"]

    tasks = []
    for exp in exp_to_imagize:
        exp_stat_root = pathset.stat_root / exp.name
        exp_imagize_root = pathset.imagize_root / exp.name

        tasks.extend(
            _build_tasklist_for_exp(
                exp_stat_root, exp_imagize_root, HM_config, cmdopts["storage"]
            )
        )

    # 2025-06-06 [JRH]: This works around what is apparently a nasty memory leak
    # in hv caused by the hv.save() function for which the usual methods of
    # clearing memory/figures do not work.  The maxtasksperchild argument kills
    # all the child threads periodically, which fixes the leak problem, for now.
    _logger.debug("Starting %s workers, method=%s", parallelism, mp.get_start_method())
    with mp.Pool(processes=parallelism, maxtasksperchild=1) as pool:
        processed = [pool.starmap_async(_worker, tasks)]
        _logger.debug("Waiting for workers to finish")

        for p in processed:
            p.get()

        pool.close()
        pool.join()

    _logger.debug("All workers finished")


def _build_tasklist_for_exp(
    exp_stat_root: pathlib.Path,
    exp_imagize_root: pathlib.Path,
    HM_config: types.YAMLDict,
    storage: str,
) -> tp.List[tp.Tuple[dict, types.YAMLDict]]:
    """Add all files from experiment to multiprocessing queue for processing.

    Enqueueing for processing is done at the file-level rather than
    per-experiment, so that for systems with more CPUs than experiments you
    still get maximum throughput.
    """
    res = []
    for category in HM_config:
        # For each graph in each category
        for graph in HM_config[category]:
            candidate = exp_stat_root / dict(graph)["src_stem"]

            if not candidate.is_dir():
                _logger.debug(
                    "Configured imagize source <batch stat root>/%s does not exist",
                    (candidate.relative_to(exp_stat_root)),
                )
                continue

            imagize_output_root = exp_imagize_root / candidate.relative_to(
                exp_stat_root
            )
            utils.dir_create_checked(imagize_output_root, exist_ok=True)

            for fpath in candidate.iterdir():
                assert (
                    fpath.is_file()
                ), f"Imagize directory {candidate} must only contain files!"

                res.append(
                    (
                        {
                            "input_path": fpath,
                            "graph_stem": candidate.relative_to(exp_stat_root),
                            "imagize_output_root": imagize_output_root,
                            "batch_root": exp_stat_root.parent.parent,
                            "storage": storage,
                        },
                        HM_config,
                    )
                )

    return res


def _worker(imagize_opts: dict, HM_config: types.YAMLDict) -> None:
    _proc_single_exp(HM_config, imagize_opts)


def _proc_single_exp(HM_config: types.YAMLDict, imagize_opts: dict) -> None:
    """Create images from the averaged ``.mean`` files from a single experiment.

    If no ``.mean`` files suitable for averaging are found, nothing is done. See
    :ref:`usage/rendering` for per-engine descriptions of what
    "suitable" means.

    Arguments:

        HM_config: Parsed YAML configuration for heatmaps.

        imagize_opts: Dictionary of imagizing options.
    """

    # For each category of heatmaps we are generating
    match = None
    for category in HM_config:
        # For each graph in each category
        for graph in HM_config[category]:
            if dict(graph)["src_stem"] == str(imagize_opts["graph_stem"]):
                match = graph

    if match is not None:
        graph_pathset = graphs.PathSet(
            input_root=imagize_opts["input_path"].parent,
            output_root=imagize_opts["imagize_output_root"],
            model_root=None,
            batchroot=imagize_opts["batch_root"],
        )

        # 2025-06-05 [JRH]: We always write stage {3,4} output data files as
        # .csv because that is currently SIERRA's 'native' format; this may
        # change in the future.
        #
        # Input paths are of the form <dir>/<dir>_<NUMBER>.{extension}
        graphs.heatmap(
            paths=graph_pathset,
            input_stem=imagize_opts["input_path"].stem,
            output_stem=imagize_opts["input_path"].stem,
            title=dict(match)["title"],
            medium="storage.csv",
            xlabel="X",
            ylabel="Y",
            colnames=(
                graph.get("x", "x"),
                graph.get("y", "y"),
                graph.get("z", "z"),
            ),
        )

    else:
        _logger.warning(
            "No match for graph with src_stem='%s' found in configuration",
            imagize_opts["graph_stem"],
        )


__all__ = [
    "proc_batch_exp",
]
