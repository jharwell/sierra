# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

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
from sierra.core import types, config, utils, batchroot

_logger = logging.getLogger(__name__)


def _parallel(main_config: types.YAMLDict,
              cmdopts: types.Cmdopts,
              inputs: tp.List[types.SimpleDict]) -> None:
    """Perform the requested rendering in parallel.

    Unless disabled with ``--proccessing-serial``, then it is done serially.
    """
    q = mp.JoinableQueue()  # type: mp.JoinableQueue

    for spec in inputs:
        q.put(spec)

    # Render videos in parallel--waaayyyy faster
    if cmdopts['processing_serial']:
        parallelism = 1
    else:
        parallelism = psutil.cpu_count()

    for _ in range(0, parallelism):
        p = mp.Process(target=_worker,
                       args=(q, main_config))
        p.start()

    q.join()


def _worker(q: mp.Queue, main_config: types.YAMLDict) -> None:
    assert shutil.which('ffmpeg') is not None, "ffmpeg not found"

    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            render_opts = q.get(True, 3)
            output_dir = pathlib.Path(render_opts['output_dir'])

            _logger.info("Rendering images in %s...", output_dir.name)

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
            _logger.trace('Run cmd: %s', to_run)  # type: ignore

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
                _logger.error("Cmd '%s' failed!", to_run)
                stdout_str = stdout_raw.decode("ascii")
                stderr_str = stderr_raw.decode("ascii")

                _logger.error(stdout_str)
                _logger.error(stderr_str)

            q.task_done()

        except queue.Empty:
            break


def from_platform(main_config: types.YAMLDict,
                  cmdopts: types.Cmdopts,
                  pathset: batchroot.PathSet,
                  criteria: bc.IConcreteBatchCriteria) -> None:
    """Render frames (images) captured in by a platform into videos.

    Frames are stitched together to make a video using :program:`ffmpeg`.  Output
    format controlled via configuration.

    Targets to render are found in::

      <batch_root>/<exp_name>/<run_name>/<frames_leaf>

    Videos are output in::

      <batch_root>/videos/<exp_name>

    ``<frames_leaf>`` is controlled via configuration.  For more
    details, see :ref:`ln-sierra-usage-rendering`.

    .. note:: This currently only works with PNG images.
    """
    exp_to_render = utils.exp_range_calc(cmdopts["exp_range"],
                                         pathset.output_root,
                                         criteria)

    inputs = []
    for exp in exp_to_render:
        output_dir = pathset.video_root / exp.name

        for run in exp.iterdir():
            platform = cmdopts['platform'].split('.')[1]
            frames_leaf = config.kRendering[platform]['frames_leaf']
            opts = {
                'ofile_name': run.name + config.kRenderFormat,
                'input_dir': str(exp / run / frames_leaf),
                'output_dir': str(output_dir),
                'ffmpeg_opts': cmdopts['render_cmd_opts']
            }
            inputs.append(copy.deepcopy(opts))

    _parallel(main_config, cmdopts, inputs)


def from_project_imagized(main_config: types.YAMLDict,
                          cmdopts: types.Cmdopts,
                          pathset: batchroot.PathSet,
                          criteria: bc.IConcreteBatchCriteria) -> None:
    """Render THINGS previously imagized in a project in stage 3 into videos.

    Frames (images) in each subdirectory in the imagize root (see
    :ref:`ln-sierra-usage-runtime-exp-tree`) are stitched together to make a
    video using :program:`ffmpeg`.  Output format controlled via configuration.

    Targets to render are found in::

      <batch_root>/imagize/<subdir_name>

    Videos are output in::

      <batch_root>/videos/<exp>/<subdir_name>

    For more details, see :ref:`ln-sierra-usage-rendering`.

    .. note:: This currently only works with PNG images.
    """
    exp_to_render = utils.exp_range_calc(cmdopts["exp_range"],
                                         pathset.output_root,
                                         criteria)

    inputs = []
    for exp in exp_to_render:
        exp_imagize_root = pathset.imagize_root / exp.name
        if not exp_imagize_root.exists():
            continue

        output_dir = pathset.videoroot / exp.name

        for candidate in exp_imagize_root.iterdir():
            if candidate.is_dir():
                opts = {
                    'input_dir': str(candidate),
                    'output_dir': str(output_dir),
                    'ofile_name': candidate.name + config.kRenderFormat,
                    'ffmpeg_opts': cmdopts['render_cmd_opts']
                }
                inputs.append(copy.deepcopy(opts))

    _parallel(main_config, cmdopts, inputs)


def from_bivar_heatmaps(main_config: types.YAMLDict,
                        cmdopts: types.Cmdopts,
                        pathset: batchroot.PathSet,
                        criteria: bc.IConcreteBatchCriteria) -> None:
    """Render inter-experiment heatmaps into videos.

    Heatmap (images) are stitched together to make a video using
    :program:`ffmpeg`.  Output format controlled via configuration.

    Targets to render are found in::

      <batch root>/graphs/collated

    Videos are output in::

      <batch_root>/videos/<graph name>

    For more details, see :ref:`ln-sierra-usage-rendering`.

    versionadded:: 1.2.20
    """

    inputs = []

    for candidate in pathset.graph_collate_root.iterdir():
        if "HM-" in candidate.name and candidate.is_dir():
            output_dir = pathset.video_root / candidate.name

            opts = {
                'input_dir': str(candidate),
                'output_dir': str(output_dir),
                'ofile_name': candidate.name + config.kRenderFormat,
                'ffmpeg_opts': cmdopts['render_cmd_opts']
            }
            inputs.append(copy.deepcopy(opts))

    _parallel(main_config, cmdopts, inputs)


__api__ = [
    '_parallel_render'
    'from_imagized',
    'from_platform',
    'from_bivar_heatmaps'
]
