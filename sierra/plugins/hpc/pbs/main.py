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
HPC plugin for running SIERRA on HPC clusters using the TORQUE-PBS scheduler.
"""
import os
import typing as tp


def env_configure(args):
    """
    Configure SIERRA for HPC by reading environment variables and modifying the parsed
    cmdline arguments. Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - ``PBS_NUM_PPN``
    - ``PBS_NODEFILE``
    - ``PBS_JOBID``
    - ``SIERRA_ARCH``
    - ``PARALLEL``
    """

    keys = ['PBS_NUM_PPN', 'PBS_NODEFILE', 'PBS_JOBID', 'SIERRA_ARCH', 'PARALLEL']

    for k in keys:
        assert k in os.environ,\
            "FATAL: Attempt to run SIERRA in non-PBS environment: '{0}' not found".format(k)

    assert args.exec_sims_per_node is not None, "FATAL: --exec-sims-per-node is required"

    # For HPC, we want to use the the maximum # of simultaneous jobs per node such that
    # there is no thread oversubscription. We also always want to allocate each physics
    # engine its own thread for maximum performance, per the original ARGoS paper.
    #
    # However, PBS does not have an environment variable for # jobs/node, so we have to rely on the
    # user to set this appropriately.
    args.physics_n_engines = int(float(os.environ['PBS_NUM_PPN']) / args.exec_sims_per_node)


def argos_cmd_generate(input_fpath: str):
    """
    Generate the ARGoS cmd to run in the TORQUE environment, given the path to an input
    file. Dependent on which TORQUE cluster you are running on, so that different versions compiled
    for different architectures/machines that exist on the same filesystem can easily be run, so the
    ``SIERRA_ARCH`` variable is used to determine the name of the ARGoS executable via
    ``argos3-$SIERRA_ARCH``.

    """

    return 'argos3-' + \
        os.environ['SIERRA_ARCH'] + \
        ' -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


def gnu_parallel_cmd_generate(parallel_opts: dict):
    """
    Given a dictionary containing job information, generate the cmd to correctly invoke GNU Parallel
    on a TORQUE managed cluster.
    """
    jobid = os.environ['PBS_JOBID']
    nodelist = os.path.join(parallel_opts['jobroot_path'],
                            "{0}-nodelist.txt".format(jobid))

    resume = ''
    # This can't be --resume, because then GNU parallel looks at the results directory, and if there
    # is stuff in it, (apparently) assumes that the job finished...
    if parallel_opts['exec_resume']:
        resume = '--resume-failed'

    return 'sort -u $PBS_NODEFILE > {0} && ' \
        'parallel {2} --jobs {1} --results {4} --joblog {3} --sshloginfile {0} --workdir {4} < "{5}"'.format(
            nodelist,
            parallel_opts['n_jobs'],
            resume,
            parallel_opts['joblog_path'],
            parallel_opts['jobroot_path'],
            parallel_opts['cmdfile_path'])


def xvfb_cmd_generate(cmdopts: tp.Dict[str, tp.Any]):
    return ''


__api__ = [
    'EnvConfigurer',
    'GNUParallelCmdGenerator',
    'ARGoSCmdGenerator'
]
