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
HPC plugin for running SIERRA with an ad-hoc set of allocated compute nodes (e.g., whatever
computers you happen to have laying around in the lab).
"""
import os
import math


def env_configure(args):
    """
    Configure SIERRA for ad-hoc HPC by reading environment variables and modifying the parsed
    cmdline arguments. Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - ``ADHOC_NODEFILE``

    """

    keys = ['ADHOC_NODEFILE']

    for k in keys:
        assert k in os.environ,\
            "FATAL: Attempt to run SIERRA in non-ADHOC environment: '{0}' not found".format(k)

    with open(os.environ['ADHOC_NODEFILE'], 'r') as f:
        lines = f.readlines()
        n_nodes = len(lines)

        ppn = math.inf
        for line in lines:
            ppn = min(ppn, int(line.split('/')[0]))

    # For HPC, we want to use the the maximum # of simultaneous jobs per node such that
    # there is no thread oversubscription. We also always want to allocate each physics
    # engine its own thread for maximum performance, per the original ARGoS paper.
    if args.exec_sims_per_node is None:
        args.exec_sims_per_node = int(float(args.n_sims) / n_nodes)

    args.physics_n_engines = int(ppn / args.exec_sims_per_node)


def argos_cmd_generate(input_fpath: str):
    """
    Generate the ARGOS cmd to run in the ad-hoc environment, given the path to an input file. The
    ARGoS executable is assumed to be called ``argos3``.
    """

    return 'argos3 -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


def gnu_parallel_cmd_generate(parallel_opts: dict):
    """
    Given a dictionary containing job information, generate the cmd to correctly invoke GNU Parallel
    in the ad-hoc environment.
    """

    jobid = os.getpid()
    nodelist = os.path.join(parallel_opts['jobroot_path'],
                            "{0}-nodelist.txt".format(jobid))

    resume = ''
    # This can't be --resume, because then GNU parallel looks at the results directory, and if there
    # is stuff in it, (apparently) assumes that the job finished...
    if parallel_opts['exec_resume']:
        resume = '--resume-failed'

    return 'sort -u $ADHOC_NODEFILE > {0} && ' \
        'parallel {2} --jobs {1} --results {4} --joblog {3} --sshloginfile {0} --workdir {4} < "{5}"'.format(
            nodelist,
            parallel_opts['n_jobs'],
            resume,
            parallel_opts['joblog_path'],
            parallel_opts['jobroot_path'],
            parallel_opts['cmdfile_path'])


def xvfb_cmd_generate(cmdopts: dict):
    return ''
