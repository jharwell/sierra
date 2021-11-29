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
Classes for rendering frames (1) captured by by the ``--platform`` during
stage 2, (2) generated during stage 3 of SIERRA.

"""

# Core packages
import os
import subprocess
import typing as tp
import multiprocessing as mp
import queue
import copy
import shutil
import logging  # type: tp.Any

# 3rd party packages

# Project packages
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
from sierra.core import types
from sierra.core import config


class BatchExpParallelVideoRenderer:
    """
    Render the video for each experiment in the specified batch directory in
    sequence.
    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Arguments:
            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        exp_to_render = sierra.core.utils.exp_range_calc(self.cmdopts,
                                                         self.cmdopts['batch_output_root'],
                                                         criteria)

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_render:
            _, leaf = os.path.split(exp)

            if self.cmdopts['project_rendering']:

                exp_imagize_root = os.path.join(
                    self.cmdopts['batch_imagize_root'], leaf)

                # Project render targets are in
                # <averaged_output_root>/<metric_dir_name>, for all directories
                # in <averaged_output_root>.
                for d in os.listdir(exp_imagize_root):
                    candidate = os.path.join(exp_imagize_root, d)
                    if os.path.isdir(candidate):
                        opts = {
                            'input_dir': candidate,
                            'output_dir': os.path.join(self.cmdopts['batch_video_root'],
                                                       leaf),
                            'ofile_leaf': d + config.kRenderFormat,
                            'cmd_opts': self.cmdopts['render_cmd_opts']
                        }

                        sierra.core.utils.dir_create_checked(
                            opts['output_dir'], True)
                        q.put(opts)

            if self.cmdopts['platform_vc']:
                # Render targets are in
                # <batch_output_root>/<exp>/<sim>/<frames_leaf>, for all
                # runs in a given experiment (which can be a lot!).
                for sim in self._filter_sim_dirs(os.listdir(exp),
                                                 self.main_config):
                    opts = {
                        'ofile_leaf': sim + sierra.core.config.kRenderFormat,
                        'input_dir': os.path.join(exp,
                                                  sim,
                                                  config.kARGoS['frames_leaf']),
                        'output_dir': os.path.join(self.cmdopts['batch_video_root'],
                                                   leaf),
                        'cmd_opts': self.cmdopts['render_cmd_opts']
                    }
                    sierra.core.utils.dir_create_checked(
                        opts['output_dir'], exist_ok=True)
                    q.put(copy.deepcopy(opts))

        # Render videos in parallel--waaayyyy faster
        if self.cmdopts['serial_processing']:
            parallelism = 1
        else:
            parallelism = mp.cpu_count()

        for i in range(0, parallelism):
            p = mp.Process(target=BatchExpParallelVideoRenderer._thread_worker,
                           args=(q, self.main_config))
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(q: mp.Queue, main_config: dict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                render_opts = q.get(True, 3)
                ExpVideoRenderer()(main_config, render_opts)
                q.task_done()
            except queue.Empty:
                break

    @staticmethod
    def _filter_sim_dirs(sim_dirs: tp.List[str],
                         main_config: dict) -> tp.List[str]:
        return [s for s in sim_dirs if s not in ['videos']]


class ExpVideoRenderer:
    """
    Render all frames (.png/.jpg/etc files) in a specified input directory to a
    video file via ffmpeg, output according to configuration.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration.
        render_opts: Dictionary of render options.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        assert shutil.which('ffmpeg') is not None, "ffmpeg not found"

    def __call__(self, main_config: dict, render_opts: tp.Dict[str, str]) -> None:
        self.logger.info("Rendering images in %s,ofile_leaf=%s...",
                         render_opts['input_dir'],
                         render_opts['ofile_leaf'])
        opts = render_opts['cmd_opts'].split(' ')

        cmd = ["ffmpeg",
               "-y",
               "-pattern_type",
               "glob",
               "-i",
               "'" + os.path.join(render_opts['input_dir'], "*" + config.kImageExt) + "'"]
        cmd.extend(opts)
        cmd.extend([os.path.join(render_opts['output_dir'],
                                 render_opts['ofile_leaf'])])

        p = subprocess.Popen(' '.join(cmd),
                             shell=True,
                             stderr=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL)
        p.wait()


__api__ = ['BatchExpParallelVideoRenderer', 'ExpVideoRenderer']
