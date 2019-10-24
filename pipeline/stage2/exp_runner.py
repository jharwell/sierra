# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
import subprocess
import time
import sys


class ExpRunner:

    """
    Runs the specified  # of simulations in parallel using GNU Parallel on
    the provided set of hosts on MSI (or on a single personal computer for testing).

    Attributes:
      exp_generation_root(str): Root directory for all generated simulation input files for the
                                experiment.
      exp_num(int): Experiment number in the batch
      fn_threads_per_sim(int): # ARGoS threads being used per simulation.

    """

    def __init__(self, exp_generation_root, exp_num):
        self.exp_generation_root = os.path.abspath(exp_generation_root)
        self.exp_num = exp_num

    def run(self, exec_method, n_jobs, exec_resume):
        '''Runs the experiment.'''
        assert os.environ.get(
            "ARGOS_PLUGIN_PATH") is not None, ("ERROR: You must have ARGOS_PLUGIN_PATH defined")
        assert os.environ.get(
            "LOG4CXX_CONFIGURATION") is not None, ("ERROR: You must LOG4CXX_CONFIGURATION defined")

        # Root directory for the job. Chose the exp input directory rather than the output directory
        # in order to keep simulation outputs separate from those for the framework used to run the
        # experiments.
        jobroot = self.exp_generation_root

        cmdfile = os.path.join(self.exp_generation_root, "commands.txt")
        joblog = os.path.join(jobroot, "parallel$PBS_JOBID.log")

        sys.stdout.write('--' + ' Running exp{0} in {1}...'.format(self.exp_num,
                                                                   self.exp_generation_root))
        sys.stdout.flush()

        start = time.time()
        try:
            if 'local' == exec_method:
                ExpRunner.__run_local(jobroot, cmdfile, joblog, n_jobs, exec_resume)
            elif 'hpc' in exec_method:
                ExpRunner.__run_hpc_parallel(jobroot, cmdfile, joblog, exec_resume)
            else:
                assert False, "Bad exec method '{0}'".format(exec_method)

        # Catch the exception but do not raise it again so that additional experiments can still be
        # run if possible
        except subprocess.CalledProcessError:
            print("ERROR: Experiment failed!")
        elapsed = time.time() - start
        sys.stdout.write("{:.3f}s\n".format(elapsed))

    @staticmethod
    def __run_local(jobroot_path, cmdfile_path, joblog_path, n_jobs, exec_resume):
        resume = ''
        if exec_resume:
            resume = '--resume'

        p = subprocess.Popen('cd {0} &&'
                             'parallel {1} --jobs {2} --results {0} --joblog {3} --no-notice < "{4}"'.format(
                                 jobroot_path,
                                 resume,
                                 n_jobs,
                                 joblog_path,
                                 cmdfile_path),
                             shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(stdout, stderr)
            print("ERROR: Process exited with {0}".format(p.returncode))

    @staticmethod
    def __run_hpc_parallel(jobroot_path, cmdfile_path, joblog_path, exec_resume):
        nodelist = os.path.join(jobroot_path, "$PBS_JOBID-nodelist.txt")
        resume = ''
        if exec_resume:
            resume = '--resume'

        subprocess.run('sort -u $PBS_NODEFILE > {0} && '
                       'parallel {1} --jobs 1 --results {3} --joblog {2} --sshloginfile {0} --workdir {3} < "{4}"'.format(
                           nodelist,
                           resume,
                           joblog_path,
                           jobroot_path,
                           cmdfile_path),
                       shell=True, check=True)
