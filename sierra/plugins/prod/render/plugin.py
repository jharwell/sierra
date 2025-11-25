# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for rendering frames (images) into videos.

Frames can be:

- Captured by by the ``--engine`` during stage 2.

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
import time
import datetime

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, config, utils, batchroot
from sierra.core import plugin as pm

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Render videos.

        #. From :term:`Engine` if ``--engine-vc`` was passed.

        #. From imagized images if ``proc.imagize`` was run previously to
           generate frames, and ``--project-rendering`` is passed.
    """
    if (not cmdopts["engine_vc"]) and (not cmdopts["project_rendering"]):
        _logger.warning(
            "Rendering plugin active without --engine-vc or --project-rendering"
        )
        return

    _logger.info("Rendering videos...")
    start = time.time()

    graphs_path = pathlib.Path(cmdopts["project_config_root"]) / pathlib.Path(
        config.PROJECT_YAML.graphs
    )
    if utils.path_exists(graphs_path):
        _logger.info("Loading render config for project=%s", cmdopts["project"])
        loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")
        render_config = loader.load_config(cmdopts, config.PROJECT_YAML.graphs)

    else:
        _logger.warning("%s does not exist--cannot generate render", graphs_path)
        return

    if cmdopts["engine_vc"]:
        _from_engine(render_config["intra-exp"], cmdopts, pathset, criteria)
    else:
        _logger.debug(
            "--engine-vc not passed--(possibly) skipping "
            "rendering frames captured by the engine"
        )

    if cmdopts["project_rendering"] and "imagize" in render_config:
        _from_project_imagized(render_config["imagize"], cmdopts, pathset, criteria)
    else:
        _logger.debug(
            "--project-rendering not passed--(possibly) "
            "skipping rendering frames captured by the "
            "project"
        )

    elapsed = int(time.time() - start)
    sec = datetime.timedelta(seconds=elapsed)
    _logger.info("Rendering complete in %s", str(sec))


def _from_engine(
    render_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """Render frames (images) captured in by a engine into videos.

    Frames are stitched together to make a video using :program:`ffmpeg`.  Output
    format controlled via configuration.

    Targets to render are found in::

      <batch_root>/<exp_name>/<run_name>/<frames_leaf>

    Videos are output in::

      <batch_root>/videos/<exp_name>

    ``<frames_leaf>`` is controlled via configuration.  For more
    details, see :ref:`plugins/prod/render`.

    .. note:: This currently only works with PNG images.
    """
    exp_to_render = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    inputs = []
    for exp in exp_to_render:
        output_dir = pathset.video_root / exp.name

        for run in exp.iterdir():
            engine = cmdopts["engine"].split(".")[1]
            frames_leaf = config.RENDERING[engine]["frames_leaf"]
            output_path = output_dir / (run.name + config.RENDERING["format"])
            opts = {
                "exp_root": pathset.imagize_root / exp.name,
                "output_path": output_path,
                "input_dir": str(exp / run / frames_leaf),
                "ffmpeg_opts": cmdopts["render_cmd_opts"],
            }
            inputs.append(copy.deepcopy(opts))

    _parallel(render_config, cmdopts, inputs)


def _from_project_imagized(
    render_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """Render THINGS previously imagized in a project in stage 3 into videos.

    Frames (images) in the imagize root (see :ref:`usage/run-time-tree`) are
    stitched together to make a video using :program:`ffmpeg`.  Output format
    controlled via configuration.

    Targets to render are found in::

        <batch_root>/imagize/<subdir_path>

    Videos are output in::

        <batch_root>/videos/<exp>/<subdir_path>

    For more details, see :ref:`plugins/prod/render`.

    .. NOTE:: This currently only works with PNG images.
    """
    exp_to_render = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    inputs = []
    # For each graph in each category
    for graph in render_config:
        # Across all experiments
        for exp in exp_to_render:
            exp_imagize_root = pathset.imagize_root / exp.name
            if not exp_imagize_root.exists():
                continue

            # Check all directories recursively
            for candidate in exp_imagize_root.rglob("*"):
                path = pathlib.Path(dict(graph)["src_stem"])
                fragment = path.parent / path.name
                if candidate.is_file():
                    continue

                if str(fragment) not in str(candidate):
                    continue

                output_path = (
                    pathset.video_root
                    / exp.name
                    / candidate.relative_to(exp_imagize_root)
                ) / (candidate.name + config.RENDERING["format"])
                inputs.append(
                    {
                        "input_dir": candidate,
                        "exp_root": pathset.imagize_root / exp.name,
                        "output_path": output_path,
                        "ffmpeg_opts": cmdopts["render_cmd_opts"],
                    }
                )

    _parallel(render_config, cmdopts, inputs)


def _parallel(
    render_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    inputs: list[types.SimpleDict],
) -> None:
    """Perform the requested rendering in parallel."""
    q = mp.JoinableQueue()  # type: mp.JoinableQueue

    for spec in inputs:
        q.put(spec)

    # Render videos in parallel--waaayyyy faster
    parallelism = cmdopts["processing_parallelism"]

    for _ in range(0, parallelism):
        p = mp.Process(target=_worker, args=(q, render_config))
        p.start()

    q.join()


def _worker(q: mp.Queue, render_config: types.YAMLDict) -> None:
    assert shutil.which("ffmpeg") is not None, "ffmpeg not found"
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            render_opts = q.get(True, 3)

            _logger.info("Rendering images in %s...", render_opts["exp_root"].name)

            opts = render_opts["ffmpeg_opts"].split(" ")

            ipaths = "'{}/*.{}'".format(
                render_opts["input_dir"], config.GRAPHS["static_type"]
            )
            cmd = ["ffmpeg", "-y", "-pattern_type", "glob", "-i", ipaths]
            cmd.extend(opts)
            cmd.extend([str(render_opts["output_path"])])

            to_run = " ".join(cmd)
            _logger.trace("Run cmd: %s", to_run)

            utils.dir_create_checked(render_opts["output_path"].parent, exist_ok=True)

            with subprocess.Popen(
                to_run, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
            ) as proc:
                proc.wait()

            # We use communicate(), not wait() to avoid issues with IO buffers
            # becoming full (e.g., you get deadlocks with wait() regularly).
            stdout_raw, stderr_raw = proc.communicate()

            # Only show output if the process failed (i.e., did not return 0)
            if proc.returncode != 0:
                _logger.error("Cmd '%s' failed!", to_run)
                stdout_str = stdout_raw.decode("ascii")
                stderr_str = stderr_raw.decode("ascii")

                _logger.error("Return code=%d", proc.returncode)
                _logger.error("stdout: %s", stdout_str)
                _logger.error("stderr: %s", stderr_str)

            q.task_done()

        except queue.Empty:
            break


__all__ = ["proc_batch_exp"]
