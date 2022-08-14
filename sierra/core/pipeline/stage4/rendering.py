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

"""Classes for rendering frames (images) into videos.

Frames can be:

- Captured by by the ``--platform`` during stage 2.

- Generated during stage 3 of SIERRA via imagizing.

- Generated inter-experiment heatmaps from bivariate experiments.

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
import psutil

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, config, utils


class ParallelRenderer:
    """Base class for performing the requested rendering in parallel.

    Unless disabled with ``--proccessing-serial``, then it is done serially.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def do_rendering(self, inputs: tp.List[types.SimpleDict]) -> None:
        """
        Do the rendering.

        """
        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for spec in inputs:
            q.put(spec)

        # Render videos in parallel--waaayyyy faster
        if self.cmdopts['processing_serial']:
            parallelism = 1
        else:
            parallelism = psutil.cpu_count()

        for _ in range(0, parallelism):
            p = mp.Process(target=ParallelRenderer._thread_worker,
                           args=(q, self.main_config))
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(q: mp.Queue, main_config: types.YAMLDict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                render_opts = q.get(True, 3)
                ExpRenderer()(main_config, render_opts)
                q.task_done()
            except queue.Empty:
                break


class PlatformFramesRenderer(ParallelRenderer):
    """Renders frames (images) captured in each experimental run by a platform.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        super().__init__(main_config, cmdopts)
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_render = utils.exp_range_calc(self.cmdopts,
                                             self.cmdopts['batch_output_root'],
                                             criteria)

        inputs = []
        for exp in exp_to_render:
            inputs.extend(self._calc_rendering_inputs(exp))

        self.do_rendering(inputs)

    def _calc_rendering_inputs(self,
                               exp: pathlib.Path) -> tp.List[types.SimpleDict]:
        # Render targets are in
        # <batch_output_root>/<exp>/<sim>/<frames_leaf>, for all
        # runs in a given experiment (which can be a lot!).
        output_dir = pathlib.Path(self.cmdopts['batch_video_root'], exp.name)

        inputs = []

        for run in exp.iterdir():
            platform = self.cmdopts['platform'].split('.')[1]
            frames_leaf = config.kRendering[platform]['frames_leaf']
            opts = {
                'ofile_name': run.name + config.kRenderFormat,
                'input_dir': str(exp / run / frames_leaf),
                'output_dir': str(output_dir),
                'ffmpeg_opts': self.cmdopts['render_cmd_opts']
            }
            inputs.append(copy.deepcopy(opts))

        return inputs


class ProjectFramesRenderer(ParallelRenderer):
    """Render the video for each experimental run in each experiment.
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        super().__init__(main_config, cmdopts)
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:

        exp_to_render = utils.exp_range_calc(self.cmdopts,
                                             self.cmdopts['batch_output_root'],
                                             criteria)

        inputs = []
        for exp in exp_to_render:
            inputs.extend(self._calc_rendering_inputs(exp))

        self.do_rendering(inputs)

    def _calc_rendering_inputs(self, exp: pathlib.Path) -> tp.List[types.SimpleDict]:
        exp_imagize_root = pathlib.Path(self.cmdopts['batch_imagize_root'],
                                        exp.name)
        if not exp_imagize_root.exists():
            return []

        # Project render targets are in
        # <batch_video_root>/<exp_name>, for all directories
        # in <exp_imagize_root>.
        output_dir = pathlib.Path(self.cmdopts['batch_video_root'], exp.name)

        inputs = []

        for candidate in exp_imagize_root.iterdir():
            if candidate.is_dir():
                opts = {
                    'input_dir': str(candidate),
                    'output_dir': str(output_dir),
                    'ofile_name': candidate.name + config.kRenderFormat,
                    'ffmpeg_opts': self.cmdopts['render_cmd_opts']
                }
                inputs.append(copy.deepcopy(opts))

        return inputs


class BivarHeatmapRenderer(ParallelRenderer):
    """Render videos from generated inter-experiment heatmaps.

    versionadded:: 1.2.20
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        super().__init__(main_config, cmdopts)
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        inputs = self._calc_rendering_inputs()
        self.do_rendering(inputs)

    def _calc_rendering_inputs(self) -> tp.List[types.SimpleDict]:
        graph_root = pathlib.Path(self.cmdopts['batch_graph_collate_root'])

        inputs = []

        for candidate in graph_root.iterdir():
            if "HM-" in candidate.name and candidate.is_dir():
                # Project render targets are in <batch_video_root>/<graph name>.
                output_dir = pathlib.Path(self.cmdopts['batch_video_root'],
                                          candidate.name)

                opts = {
                    'input_dir': str(candidate),
                    'output_dir': str(output_dir),
                    'ofile_name': candidate.name + config.kRenderFormat,
                    'ffmpeg_opts': self.cmdopts['render_cmd_opts']
                }
                inputs.append(copy.deepcopy(opts))

        return inputs


class ExpRenderer:
    """Render all images in the input directory to a video via :program:`ffmpeg`.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        assert shutil.which('ffmpeg') is not None, "ffmpeg not found"

    def __call__(self,
                 main_config: types.YAMLDict,
                 render_opts: tp.Dict[str, str]) -> None:
        output_dir = pathlib.Path(render_opts['output_dir'])

        self.logger.info("Rendering images in %s...", output_dir.name)

        opts = render_opts['ffmpeg_opts'].split(' ')

        ipaths = "'{0}/*{1}'".format(render_opts['input_dir'],
                                     config.kImageExt)
        opath = pathlib.Path(render_opts['output_dir'],
                             render_opts['ofile_name'])
        cmd = ["ffmpeg",
               "-y",
               "-pattern_type",
               "glob",
               "-i",
               ipaths]
        cmd.extend(opts)
        cmd.extend([str(opath)])

        to_run = ' '.join(cmd)
        self.logger.trace('Run cmd: %s', to_run)  # type: ignore

        utils.dir_create_checked(render_opts['output_dir'],
                                 exist_ok=True)

        with subprocess.Popen(to_run,
                              shell=True,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE) as proc:
            proc.wait()

        # We use communicate(), not wait() to avoid issues with IO buffers
        # becoming full (i.e., you get deadlocks with wait() regularly).
        stdout_raw, stderr_raw = proc.communicate()

        # Only show output if the process failed (i.e., did not return 0)
        if proc.returncode != 0:
            self.logger.error("Cmd '%s' failed!", to_run)
            stdout_str = stdout_raw.decode("ascii")
            stderr_str = stderr_raw.decode("ascii")

            self.logger.error(stdout_str)
            self.logger.error(stderr_str)


__api__ = [
    'ParallelRenderer',
    'PlatformFramesRenderer',
    'ProjectFramesRenderer',
    'BivarHeatmapRenderer',
    'ExpRenderer'
]
