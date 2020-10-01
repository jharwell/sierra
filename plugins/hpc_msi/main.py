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
HPC plugin for running SIERRA on the MSI supercomputing institute at the University of Minnesota.
"""
import os


def env_configure(args):
    """
    Configure SIERRA for HPC at MSI by reading environment variables and modifying the parsed
    cmdline arguments. Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - ``PBS_NUM_PPN``
    - ``PBS_NODEFILE``
    - ``PBS_NUM_NODES``
    - ``MSICLUSTER``
    """
    environs = ['mesabi', 'mangi']

    keys = ['MSICLUSTER', 'PBS_NUM_PPN', 'PBS_NUM_NODES', 'PBS_NODEFILE']

    for k in keys:
        assert k in os.environ,\
            "FATAL: Attempt to run SIERRA in non-MSI environment: '{0}' not found".format(k)

    assert os.environ['MSICLUSTER'] in environs,\
        "FATAL: Unknown MSI cluster '{0}'".format(os.environ['MSICLUSTER'])
    assert args.n_sims >= int(os.environ['PBS_NUM_NODES']),\
        "FATAL: Too few simulations requested: {0} < {1}".format(args.n_sims,
                                                                 os.environ['PBS_NUM_NODES'])
    assert args.n_sims % int(os.environ['PBS_NUM_NODES']) == 0,\
        "FATAL: # simulations ({0}) not a multiple of # nodes ({1})".format(args.n_sims,
                                                                            os.environ['PBS_NUM_NODES'])

    # For HPC, we want to use the the maximum # of simultaneous jobs per node such that
    # there is no thread oversubscription. We also always want to allocate each physics
    # engine its own thread for maximum performance, per the original ARGoS paper.
    args.__dict__['n_jobs_per_node'] = int(
        float(args.n_sims) / int(os.environ['PBS_NUM_NODES']))
    args.physics_n_engines = int(
        float(os.environ['PBS_NUM_PPN']) / args.n_jobs_per_node)
    args.__dict__['n_threads'] = args.physics_n_engines


def argos_cmd_generate(input_fpath: str):
    """
    Generate the ARGoS cmd to run in the MSI environment, given the path to an input file. Dependent
    on which MSI cluster you are running on, so that different versions compiled for different
    architectures/machines that exist on the same filesystem can easily be run, so the
    ``MSICLUSTER`` variable is used to determine the name of the ARGoS executable via
    ``argos3-$MSICLUSTER``.
    """

    return 'argos3-' + \
        os.environ['MSICLUSTER'] + \
        ' -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


def gnu_parallel_cmd_generate(parallel_opts: dict):
    """
    Given a dictionary containing job information, generate the cmd to correctly invoke GNU Parallel
    on MSI.

    Args:
        parallel_opts: Dictionary containing:
                       - jobroot_path - The root directory for the batch experiment.
                       - exec_resume - Is this a resume of a previously run experiment?
                       - n_jobs - How many parallel jobs are allowed per node?
                       - joblog_path - The logfile for GNU parallel output.
                       - cmdfile_path - The file containing the ARGoS cmds to run.
    """
    jobid = os.environ['PBS_JOBID']
    nodelist = os.path.join(parallel_opts['jobroot_path'],
                            "{0}-nodelist.txt".format(jobid))

    resume = ''
    if parallel_opts['exec_resume']:
        resume = '--resume'

    return 'sort -u $PBS_NODEFILE > {0} && ' \
        'parallel {2} --jobs {1} --results {4} --joblog {3} --sshloginfile {0} --workdir {4} < "{5}"'.format(
            nodelist,
            parallel_opts['n_jobs'],
            resume,
            parallel_opts['joblog_path'],
            parallel_opts['jobroot_path'],
            parallel_opts['cmdfile_path'])


def xvfb_cmd_generate(cmdopts: dict):
    return ''


__api__ = [
    'EnvConfigurer',
    'GNUParallelCmdGenerator',
    'ARGoSCmdGenerator'
]
