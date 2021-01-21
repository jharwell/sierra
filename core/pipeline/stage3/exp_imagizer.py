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
from core.graphs.heatmap import Heatmap
import core.utils
import core.config


class BatchedExpImagizer:
    """
    Generate the images for each experiment in the specified batch directory.
    """

    def __call__(self, main_config: dict, HM_config: dict, batch_exp_root: str) -> None:
        """
        Arguments:
            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        experiments = [d for d in os.listdir(batch_exp_root)
                       if main_config['sierra']['collate_csv_leaf'] not in d]

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in experiments:
            exp_root = os.path.join(batch_exp_root, exp)
            avg_root = os.path.join(exp_root, main_config['sierra']['avg_output_leaf'])
            for m in os.listdir(avg_root):
                metrics_path = os.path.join(avg_root, m)
                if os.path.isdir(metrics_path):
                    imagize_output_root = os.path.join(batch_exp_root,
                                                       exp,
                                                       main_config['sierra']['project_frames_leaf'],
                                                       m)
                    imagize_opts = {
                        'csv_dir_root': avg_root,
                        'csv_dir': m,
                        'output_root': imagize_output_root
                    }

                    core.utils.dir_create_checked(imagize_output_root, exist_ok=True)
                    q.put(imagize_opts)

        for _ in range(0, mp.cpu_count()):
            p = mp.Process(target=BatchedExpImagizer.__thread_worker,
                           args=(q, HM_config))
            p.start()

        q.join()

    @staticmethod
    def __thread_worker(q: mp.Queue, HM_config: dict) -> None:
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
        path = os.path.join(imagize_opts['csv_dir_root'], imagize_opts['csv_dir'])

        self.logger.info("Imagizing .csvs in %s...", path)

        for csv in os.listdir(path):
            # For each category of heatmaps we are generating
            match = None
            for category in HM_config:
                # For each graph in each category
                for graph in HM_config[category]['graphs']:
                    if graph['src_stem'] == imagize_opts['csv_dir']:
                        match = graph

            if match is not None:
                stem, _ = os.path.splitext(csv)
                Heatmap(input_fpath=os.path.join(path, csv),
                        output_fpath=os.path.join(imagize_opts['output_root'],
                                                  stem + core.config.kImageExt),
                        title=match['title'],
                        xlabel='X',
                        ylabel='Y').generate()

            else:
                self.logger.error("No match for graph with src_stem=%s found",
                                  imagize_opts['csv_dir'])
                raise NotImplementedError
