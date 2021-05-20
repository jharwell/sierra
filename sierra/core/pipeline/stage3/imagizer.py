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

"""
Classes for creating image files from averaged ``.csv`` files for experiments.
"""

# Core packages
import os
import logging
import typing as tp
import multiprocessing as mp
import queue

# 3rd party packages

# Project packages
from sierra.core.graphs.heatmap import Heatmap
import sierra.core.utils
import sierra.core.config
import sierra.core.variables.batch_criteria as bc


class BatchExpParallelImagizer:
    """
    Generate the images for each experiment in the specified batch directory.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, tp.Any]) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, HM_config: dict, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Arguments:
            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        exp_to_imagize = sierra.core.utils.exp_range_calc(self.cmdopts,
                                                   self.cmdopts['batch_output_root'],
                                                   criteria)

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_imagize:
            _, leaf = os.path.split(exp)

            exp_stat_root = os.path.join(self.cmdopts['batch_stat_root'], leaf)
            exp_imagize_root = os.path.join(self.cmdopts['batch_imagize_root'], leaf)

            for item in os.listdir(exp_stat_root):
                candidate_path = os.path.join(exp_stat_root, item)

                if os.path.isdir(candidate_path):
                    imagize_output_root = os.path.join(exp_imagize_root, item)
                    imagize_opts = {
                        'input_root': exp_stat_root,
                        'graph_stem': item,
                        'output_root': imagize_output_root
                    }

                    sierra.core.utils.dir_create_checked(imagize_output_root, exist_ok=True)
                    q.put(imagize_opts)

        if self.cmdopts['serial_processing']:
            parallelism = 1
        else:
            parallelism = mp.cpu_count()

        for _ in range(0, parallelism):
            p = mp.Process(target=BatchExpParallelImagizer._thread_worker,
                           args=(q, HM_config))
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(q: mp.Queue, HM_config: dict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                imagize_opts = q.get(True, 3)
                ExpImagizer()(HM_config, imagize_opts)
                q.task_done()
            except queue.Empty:
                break


class ExpImagizer:
    """
    Create images from the averaged ``.csv`` files from an experiment. If no metrics suitable for
    averaging are found, nothing is done.

    Arguments:
        HM_config: Parsed YAML configuration for heatmaps.
        imagize_opts: Dictionary of imagizing options.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self, HM_config: dict, imagize_opts: tp.Dict[str, str]) -> None:
        path = os.path.join(imagize_opts['input_root'], imagize_opts['graph_stem'])

        self.logger.info("Imagizing .csvs in %s...", path)

        for csv in os.listdir(path):
            # For each category of heatmaps we are generating
            match = None
            for category in HM_config:
                # For each graph in each category
                for graph in HM_config[category]['graphs']:
                    if graph['src_stem'] == imagize_opts['graph_stem']:
                        match = graph

            if match is not None:
                stem, _ = os.path.splitext(csv)
                Heatmap(input_fpath=os.path.join(path, stem + '.csv'),
                        output_fpath=os.path.join(imagize_opts['output_root'],
                                                  stem + sierra.core.config.kImageExt),
                        title=match['title'],
                        xlabel='X',
                        ylabel='Y').generate()

            else:
                self.logger.warning("No match for graph with src_stem=%s found",
                                    imagize_opts['graph_stem'])
