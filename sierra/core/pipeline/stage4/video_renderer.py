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

"""Classes for rendering frames (images).

Frames can be:

- Captured by by the ``--platform`` during stage 2.

- Generated during stage 3 of SIERRA via imagizing.

"""

# Core packages
import subprocess
import typing as tp
import multiprocessing as mp
import queue
import copy
import shutil
import logging
import pathlib

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, config, utils


class BatchExpParallelVideoRenderer:
    """Render the video for each experiment in the batch.

    In parallel for speed, unless disabled with ``--proccessing-serial``.
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Do the rendering.

        Arguments:

            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        exp_to_render = utils.exp_range_calc(self.cmdopts,
                                             self.cmdopts['batch_output_root'],
                                             criteria)

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_render:
            if self.cmdopts['project_rendering']:
                self._project_rendering(exp, q)

            if self.cmdopts['platform_vc']:
                self._platform_rendering(exp, q)

        # Render videos in parallel--waaayyyy faster
        if self.cmdopts['processing_serial']:
            parallelism = 1
        else:
            parallelism = mp.cpu_count()

        for _ in range(0, parallelism):
            p = mp.Process(target=BatchExpParallelVideoRenderer._thread_worker,
                           args=(q, self.main_config))
            p.start()

        q.join()

    def _platform_rendering(self,
                            exp: pathlib.Path,
                            q: mp.JoinableQueue) -> None:
        # Render targets are in
        # <batch_output_root>/<exp>/<sim>/<frames_leaf>, for all
        # runs in a given experiment (which can be a lot!).
        output_dir = pathlib.Path(self.cmdopts['batch_video_root'], exp.name)

        all_dirs = list(exp.iterdir())
        filtered = self._filter_sim_dirs(all_dirs, self.main_config)

        for sim in filtered:
            frames_leaf = config.kRendering[self.cmdopts['platform']]['frames_leaf']
            opts = {
                'ofile_leaf': str(sim.with_suffix(config.kRenderFormat)),
                'input_dir': str(exp / sim / frames_leaf),
                'output_dir': str(output_dir),
                'cmd_opts': self.cmdopts['render_cmd_opts']
            }
            utils.dir_create_checked(opts['output_dir'],
                                     exist_ok=True)
            q.put(copy.deepcopy(opts))

    def _project_rendering(self,
                           exp: pathlib.Path,
                           q: mp.JoinableQueue) -> None:
        exp_imagize_root = pathlib.Path(
            self.cmdopts['batch_imagize_root']) / exp.name

        # Project render targets are in
        # <averaged_output_root>/<metric_dir_name>, for all directories
        # in <averaged_output_root>.
        output_dir = pathlib.Path(self.cmdopts['batch_video_root']) / exp.name

        for candidate in exp_imagize_root.iterdir():
            if candidate.is_dir():
                opts = {
                    'input_dir': str(candidate),
                    'output_dir': str(output_dir),
                    'ofile_leaf': candidate.name + config.kRenderFormat,
                    'cmd_opts': self.cmdopts['render_cmd_opts']
                }

                utils.dir_create_checked(pathlib.Path(opts['output_dir']),
                                         True)
                q.put(opts)

    @staticmethod
    def _thread_worker(q: mp.Queue, main_config: types.YAMLDict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                render_opts = q.get(True, 3)
                ExpVideoRenderer()(main_config, render_opts)
                q.task_done()
            except queue.Empty:
                break

    @staticmethod
    def _filter_sim_dirs(sim_dirs: types.PathList,
                         main_config: types.YAMLDict) -> types.PathList:
        return [s for s in sim_dirs if s.name not in ['videos']]


class ExpVideoRenderer:
    """Render all images in the input directory to a video via :program:`ffmpeg`.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        assert shutil.which('ffmpeg') is not None, "ffmpeg not found"

    def __call__(self,
                 main_config: types.YAMLDict,
                 render_opts: tp.Dict[str, str]) -> None:
        self.logger.info("Rendering images in %s,ofile_leaf=%s...",
                         render_opts['input_dir'],
                         render_opts['ofile_leaf'])
        opts = render_opts['cmd_opts'].split(' ')

        ipaths = "'{0}/*.{1}'".format(render_opts['input_dir'], config.kImageExt)
        opath = pathlib.Path(render_opts['output_dir'],
                             render_opts['ofile_leaf'])
        cmd = ["ffmpeg",
               "-y",
               "-pattern_type",
               "glob",
               "-i",
               ipaths]
        cmd.extend(opts)
        cmd.extend([str(opath)])

        with subprocess.Popen(' '.join(cmd),
                              shell=True,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL) as p:
            p.wait()


__api__ = [
    'BatchExpParallelVideoRenderer',
    'ExpVideoRenderer'


]
