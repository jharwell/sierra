"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

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
      batch(bool): Whether or not the experiment is part of a batch.

    """

    def __init__(self, exp_generation_root, batch):
        self.exp_generation_root = os.path.abspath(exp_generation_root)
        self.batch = batch

    def run(self, exec_method):
        '''Runs the experiment.'''
        assert os.environ.get(
            "ARGOS_PLUGIN_PATH") is not None, ("ERROR: You must have ARGOS_PLUGIN_PATH defined")
        assert os.environ.get(
            "LOG4CXX_CONFIGURATION") is not None, ("ERROR: You must LOG4CXX_CONFIGURATION defined")

        sys.stdout.write('-' + '-' * self.batch +
                         " Running experiment in {0}...".format(self.exp_generation_root))
        sys.stdout.flush()

        # Root directory for the job. Chose the exp input directory rather than the output directory
        # in order to keep simulation outputs separate from those for the framework used to run the
        # experiments.
        jobroot = self.exp_generation_root

        cmdfile = os.path.join(self.exp_generation_root, "commands.txt")
        joblog = os.path.join(jobroot, "parallel$PBS_JOBID.log")

        start = time.time()
        try:
            if 'local.parallel' == exec_method:
                self._run_local_parallel(jobroot, cmdfile, joblog)
            elif 'local.serial' == exec_method:
                self._run_local_serial(jobroot, cmdfile, joblog)
            elif 'hpc.parallel' == exec_method:
                self._run_hpc_parallel(jobroot, cmdfile, joblog)

        # Catch the exception but do not raise it again so that additional experiments can still be
        # run if possible
        except subprocess.CalledProcessError:
            print("ERROR: Experiment failed!")
        elapsed = time.time() - start
        sys.stdout.write("{:.3f}s\n".format(elapsed))

    def _run_local_serial(self, jobroot_path, cmdfile_path, joblog_path):
        p = subprocess.Popen('cd {0} &&'
                             'parallel --results {0} --joblog {1} --no-notice < "{2}"'.format(
                                 jobroot_path,
                                 joblog_path,
                                 cmdfile_path),
                             shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(stdout, stderr)
            print("ERROR: Process exited with {0}".format(p.returncode))

    def _run_local_parallel(self, jobroot_path, cmdfile_path, joblog_path):
        p = subprocess.Popen('cd {0} &&'
                             'parallel --jobs 1 --results {0} --joblog {1} --no-notice < "{2}"'.format(
                                 jobroot_path,
                                 joblog_path,
                                 cmdfile_path),
                             shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(stdout, stderr)
            print("ERROR: Process exited with {0}".format(p.returncode))

    def _run_hpc_parallel(self, jobroot_path, cmdfile_path, joblog_path):
        nodelist = os.path.join(jobroot_path, "$PBS_JOBID-nodelist.txt")

        subprocess.run('sort -u $PBS_NODEFILE > {0} && '
                       'parallel --jobs 1 --results {2} --joblog {1} --sshloginfile {0} --workdir {2} < "{3}"'.format(
                           nodelist,
                           joblog_path,
                           jobroot_path,
                           cmdfile_path),
                       shell=True, check=True)
