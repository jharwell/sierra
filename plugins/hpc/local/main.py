# Copyright 2020 John Harwell, All rights reserved.
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
HPC plugin for running SIERRA locally (not necessarily HPC, but it fits well enough under that
semantic umbrella).
"""

import multiprocessing
import random


def env_configure(args):
    """
    Configure SIERRA for local HPC by the parsed cmdline arguments according to the # CPUs
    available on the local machine.
    """

    if any([1, 2]) in args.pipeline:
        assert args.physics_n_engines is not None,\
            'FATAL: --physics-n-engines is required for --hpc-env=local when running stage{1,2}'

    args.__dict__['n_threads'] = args.physics_n_engines

    if any(s in args.pipeline for s in [1, 2]):
        if args.exec_jobs_per_node is None:
            args.exec_jobs_per_node = min(args.n_sims,
                                          max(1,
                                              int(multiprocessing.cpu_count() / float(args.n_threads))))

    else:
        args.exec_jobs_per_node = 0


def argos_cmd_generate(input_fpath: str):
    """
    Generate the ARGoS cmd to run on the local machine, given the path to an input file. The
    ARGoS executable is assumed to be called ``argos3``.
    """
    return 'argos3 -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


def gnu_parallel_cmd_generate(parallel_opts: dict):
    """
    Given a dictionary containing job information, generate the cmd to correctly invoke GNU Parallel
    in the ad-hoc environment.

    Args:
        parallel_opts: Dictionary containing:
                       - jobroot_path - The root directory for the batch experiment.
                       - exec_resume - Is this a resume of a previously run experiment?
                       - n_jobs - How many parallel jobs are allowed per node?
                       - joblog_path - The logfile for GNU parallel output.
                       - cmdfile_path - The file containing the ARGoS cmds to run.
    """

    resume = ''

    # This can't be --resume, because then GNU parallel looks at the results directory, and if there
    # is stuff in it, assumes that the job finished...
    if parallel_opts['exec_resume']:
        resume = '--resume-failed'

    return 'cd {0} &&' \
        'parallel --eta {1} --jobs {2} --results {0} --joblog {3} --no-notice < "{4}"'.format(
            parallel_opts['jobroot_path'],
            resume,
            parallel_opts['n_jobs'],
            parallel_opts['joblog_path'],
            parallel_opts['cmdfile_path'])


def xvfb_cmd_generate(cmdopts: dict):
    """
    Generate the command for running ARGoS under Xvfb for headless rendering (if configured).
    """

    # When running ARGoS under Xvfb in order to headlessly render frames, we need to start a
    # per-instance Xvfb server that we tell ARGoS to use via the DISPLAY environment variable,
    # which will then be killed when the shell GNU parallel spawns to run each line in the
    # commands.txt file exits.
    xvfb_cmd = ''
    if cmdopts['argos_rendering']:
        display_port = random.randint(0, 1000000)
        xvfb_cmd = "eval 'Xvfb :{0} -screen 0, 1600x1200x24 &' && DISPLAY=:{0} ".format(
            display_port)
    return xvfb_cmd
