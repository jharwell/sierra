# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for creating image files from ``.mean`` files for experiments.

See :ref:`ln-sierra-usage-rendering` for usage documentation.

"""

# Core packages
import multiprocessing as mp
import queue
import logging
import pathlib

# 3rd party packages
import psutil

# Project packages
from sierra.core.graphs.heatmap import Heatmap
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, config, utils, batchroot


_logger = logging.getLogger(__name__)


def proc_batch_exp(main_config: types.YAMLDict,
                   cmdopts: types.Cmdopts,
                   pathset: batchroot.PathSet,
                   HM_config: types.YAMLDict,
                   criteria: bc.IConcreteBatchCriteria) -> None:
    """
    Generate images for each :term:`Experiment` in the :term:`Batch Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-serial``.
    """
    exp_to_imagize = utils.exp_range_calc(cmdopts["exp_range"],
                                          pathset.output_root,
                                          criteria)

    m = mp.Manager()
    q = m.Queue()

    if cmdopts['processing_serial']:
        parallelism = 1
    else:
        parallelism = psutil.cpu_count()

    for exp in exp_to_imagize:
        exp_stat_root = pathset.stat_root / exp.name
        exp_imagize_root = pathset.imagize_root / exp.name
        _enqueue_exp_for_proc(exp_stat_root, exp_imagize_root, q)

    _logger.debug("Starting %s workers, method=%s",
                  parallelism,
                  mp.get_start_method())

    with mp.Pool(processes=parallelism) as pool:
        processed = [pool.apply_async(_worker,
                                      (q, HM_config)) for i in range(parallelism)]
        _logger.debug("Waiting for workers to finish")

        for p in processed:
            p.get()

        pool.close()
        pool.join()

    _logger.debug("All threads finished")


def _enqueue_exp_for_proc(exp_stat_root: pathlib.Path,
                          exp_imagize_root: pathlib.Path,
                          q: queue.Queue) -> None:
    """Add experiment to multiprocessing queue for processing."""
    for candidate in exp_stat_root.iterdir():
        if candidate.is_dir():
            imagize_output_root = exp_imagize_root / candidate.name
            imagize_opts = {
                'input_root': exp_stat_root,
                'graph_stem': candidate.name,
                'output_root': imagize_output_root
            }

            utils.dir_create_checked(imagize_output_root, exist_ok=True)
            q.put(imagize_opts)


def _worker(q: mp.Queue, HM_config: types.YAMLDict) -> None:
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            imagize_opts = q.get(True, 3)
            _proc_single_exp(HM_config, imagize_opts)
            q.task_done()
        except queue.Empty:
            break


def _proc_single_exp(HM_config: types.YAMLDict,
                     imagize_opts: dict) -> None:
    """Create images from the averaged ``.mean`` files from a single experiment.

    If no ``.mean`` files suitable for averaging are found, nothing is done. See
    :ref:`ln-sierra-usage-rendering` for per-platform descriptions of what
    "suitable" means.

    Arguments:

        HM_config: Parsed YAML configuration for heatmaps.

        imagize_opts: Dictionary of imagizing options.
    """

    path = imagize_opts['input_root'] / imagize_opts['graph_stem']

    _logger.info("Imagizing CSVs in experiment dir %s...", str(path))

    for csv in path.iterdir():
        # For each category of heatmaps we are generating
        match = None
        for category in HM_config:
            # For each graph in each category
            for graph in HM_config[category]['graphs']:
                if graph['src_stem'] == imagize_opts['graph_stem']:
                    match = graph

        if match is not None:
            ipath = csv.with_suffix(config.kStats['mean'].exts['mean'])
            opath = imagize_opts['output_root'] / (csv.name + config.kImageExt)
            Heatmap(input_fpath=ipath,
                    output_fpath=opath,
                    title=match['title'],
                    xlabel='X',
                    ylabel='Y').generate()

        else:
            _logger.warning(("No match for graph with src_stem='%s' "
                             "found in configuration"),
                            imagize_opts['graph_stem'])


__api__ = [
    'proc_batch_exp',
]
