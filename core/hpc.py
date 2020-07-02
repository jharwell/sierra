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

import os
import multiprocessing
import math
import random

################################################################################
# MSI
################################################################################


class MSIEnvConfigurer():
    def __init__(self) -> None:
        self.environs = ['mesabi', 'mangi']

    def __call__(self, args):
        keys = ['MSICLUSTER', 'PBS_NUM_PPN', 'PBS_NUM_NODES', 'PBS_NODEFILE']

        for k in keys:
            assert k in os.environ,\
                "FATAL: Attempt to run SIERRA in non-MSI environment: '{0}' not found".format(k)

        assert os.environ['MSICLUSTER'] in self.environs,\
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


class MSIARGoSCmdGenerator():
    """
    Generate the name of the ARGoS executable to use in the MSI environment. Dependent on which MSI
    cluster you are running on, so that different versions compiled for different
    architectures/machines that exist on the same filesystem can easily be run.

    """

    def __call__(self, input_fpath: str):
        return 'argos3-' + \
            os.environ['MSICLUSTER'] + \
            ' -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


class MSIParallelCmdGenerator():
    def __call__(self,
                 parallel_opts: dict):
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

################################################################################
# Ad-Hoc
################################################################################


class AdHocEnvConfigurer():
    def __call__(self, all_args):
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
        all_args.__dict__['n_jobs_per_node'] = int(float(all_args.n_sims) / n_nodes)
        all_args.physics_n_engines = int(ppn / all_args.n_jobs_per_node)
        all_args.__dict__['n_threads'] = all_args.physics_n_engines


class AdHocARGoSCmdGenerator():
    def __call__(self, input_fpath: str):
        return 'argos3 -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


class AdHocParallelCmdGenerator():
    def __call__(self,
                 parallel_opts: dict):
        jobid = os.getpid()
        nodelist = os.path.join(parallel_opts['jobroot_path'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        if parallel_opts['exec_resume']:
            resume = '--resume'

        return 'sort -u $ADHOC_NODEFILE > {0} && ' \
            'parallel {2} --jobs {1} --results {4} --joblog {3} --sshloginfile {0} --workdir {4} < "{5}"'.format(
                nodelist,
                parallel_opts['n_jobs'],
                resume,
                parallel_opts['joblog_path'],
                parallel_opts['jobroot_path'],
                parallel_opts['cmdfile_path'])


################################################################################
# Local
################################################################################

class LocalEnvConfigurer():
    def __call__(self, args):
        assert args.physics_n_engines is not None,\
            'FATAL: --physics-n-engines is required for --hpc-env=local'

        args.__dict__['n_threads'] = args.physics_n_engines

        if any(s in args.pipeline for s in [1, 2]):
            args.__dict__['n_jobs_per_node'] = min(args.n_sims,
                                                   max(1,
                                                       int(multiprocessing.cpu_count() / float(args.n_threads))))
        else:
            args.__dict__['n_jobs_per_node'] = 0


class LocalARGoSCmdGenerator():
    def __call__(self, input_fpath: str):
        return 'argos3 -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(input_fpath)


class LocalParallelCmdGenerator():
    def __call__(self,
                 parallel_opts: dict):

        resume = ''
        if parallel_opts['exec_resume']:
            resume = '--resume'

        return 'cd {0} &&' \
            'parallel {1} --jobs {2} --results {0} --joblog {3} --no-notice < "{4}"'.format(
                parallel_opts['jobroot_path'],
                resume,
                parallel_opts['n_jobs'],
                parallel_opts['joblog_path'],
                parallel_opts['cmdfile_path'])


class LocalXvfbCmdGenerator():
    def __call__(self, cmdopts: dict):

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

################################################################################
# Dispatchers
################################################################################


class ARGoSCmdGenerator():
    def __call__(self, cmdopts: dict, input_fpath: str):
        if cmdopts['hpc_env'] == 'local':
            return LocalARGoSCmdGenerator()(input_fpath)
        elif cmdopts['hpc_env'] == 'adhoc':
            return AdHocARGoSCmdGenerator()(input_fpath)
        elif cmdopts['hpc_env'] == 'MSI':
            return MSIARGoSCmdGenerator()(input_fpath)


class ParallelCmdGenerator():
    def __call__(self, hpc_env: str, parallel_opts: dict):

        if hpc_env == 'local':
            return LocalParallelCmdGenerator()(parallel_opts)
        elif hpc_env == 'adhoc':
            return AdHocParallelCmdGenerator()(parallel_opts)
        elif hpc_env == 'MSI':
            return MSIParallelCmdGenerator()(parallel_opts)


class XvfbCmdGenerator():
    def __call__(self, cmdopts: dict):
        if cmdopts['hpc_env'] == 'local':
            return LocalXvfbCmdGenerator()(cmdopts)
        else:
            assert False, "FATAL: Xvfb only supported on local HPC environments"


class EnvConfigurer():
    def __init__(self, hpc_env: str) -> None:
        self.hpc_env = hpc_env

    def __call__(self, args):
        args.__dict__['hpc_env'] = self.hpc_env

        if self.hpc_env == 'local':
            LocalEnvConfigurer()(args)
        elif self.hpc_env == 'adhoc':
            AdHocEnvConfigurer()(args)
        elif self.hpc_env == 'MSI':
            MSIEnvConfigurer()(args)

        return args


class EnvChecker():
    def __call__(self):
        # Verify environment
        assert os.environ.get(
            "ARGOS_PLUGIN_PATH") is not None, ("FATAL: You must have ARGOS_PLUGIN_PATH defined")
        assert os.environ.get(
            "LOG4CXX_CONFIGURATION") is not None, ("FATAL: You must LOG4CXX_CONFIGURATION defined")


__api__ = [
    'HPCEnvAdHocConfigurer',
    'HPCEnvMSIConfigurer',
    'HPCEnvLocalConfigurer',
    'HPCEnvConfigurer'
]
