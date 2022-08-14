# Copyright 2019 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

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
from sierra.core import types, config, utils


class BatchExpParallelImagizer:
    """Generate images for each :term:`Experiment` in the :term:`Batch Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-serial``.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self,
                 HM_config: types.YAMLDict,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_imagize = utils.exp_range_calc(self.cmdopts,
                                              self.cmdopts['batch_output_root'],
                                              criteria)

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_imagize:
            leaf = exp.name
            exp_stat_root = pathlib.Path(self.cmdopts['batch_stat_root']) / leaf
            exp_imagize_root = pathlib.Path(
                self.cmdopts['batch_imagize_root']) / leaf
            self._enqueue_for_exp(exp_stat_root, exp_imagize_root, q)

        if self.cmdopts['processing_serial']:
            parallelism = 1
        else:
            parallelism = psutil.cpu_count()

        for _ in range(0, parallelism):
            p = mp.Process(target=BatchExpParallelImagizer._thread_worker,
                           args=(q, HM_config))
            p.start()

        q.join()

    def _enqueue_for_exp(self,
                         exp_stat_root: pathlib.Path,
                         exp_imagize_root: pathlib.Path,
                         q: mp.JoinableQueue) -> None:
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

    @staticmethod
    def _thread_worker(q: mp.Queue, HM_config: types.YAMLDict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                imagize_opts = q.get(True, 3)
                ExpImagizer()(HM_config, imagize_opts)
                q.task_done()
            except queue.Empty:
                break


class ExpImagizer:
    """Create images from the averaged ``.mean`` files from an experiment.

    If no ``.mean`` files suitable for averaging are found, nothing is done. See
    :ref:`ln-sierra-usage-rendering` for per-platform descriptions of what
    "suitable" means.

    Arguments:

        HM_config: Parsed YAML configuration for heatmaps.

        imagize_opts: Dictionary of imagizing options.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 HM_config: types.YAMLDict,
                 imagize_opts: dict) -> None:
        path = imagize_opts['input_root'] / imagize_opts['graph_stem']

        self.logger.info("Imagizing CSVs in %s...", str(path))

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
                self.logger.warning("No match for graph with src_stem=%s found",
                                    imagize_opts['graph_stem'])


__api__ = [
    'BatchExpParallelImagizer',
    'ExpImagizer'
]
