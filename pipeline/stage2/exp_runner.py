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
import logging
import multiprocessing
import typing as tp
import variables.batch_criteria as bc


class BatchedExpRunner:

    """
    Runs each experiment in the specified batch directory in sequence using GNU Parallel.

    Attributes:
        batch_exp_root: Absolute path to the root directory for the batch experiment
                        (i.e. experiment directories are placed in here).
        cmdopts: Dictionary of parsed cmdline options.
        criteria: Batch criteria for the experiment.
        exec_exp_range: The subset of experiments in the batch to run (can be None to run all
                        experiments in the batch).

    """

    def __init__(self, cmdopts: tp.Dict[str, str], criteria: bc.BatchCriteria):
        self.cmdopts = cmdopts
        self.criteria = criteria

        self.batch_exp_root = os.path.abspath(self.cmdopts['generation_root'])
        self.exec_exp_range = self.cmdopts['exec_exp_range']

    def run(self,
            exec_method: str,
            n_threads_per_sim: int,
            n_sims: int,
            exec_resume: bool,
            with_rendering: bool):
        """
        Runs experiments in the batch according to configuration.

        Arguments:
            exec_method: The method of running the experiments (HPC or on local machine).
            n_threads_per_sim: How many threads each ARGoS simulation will use. Not used in this
                               function except as diagnostic output (setting # threads used is done
                               in stage1).
            n_sims: How many ARGoS simulations will be run for each experiment. Not used in this
                    function except as diagnostic output (setting # simulations used is done in
                    stage1).
            exec_resume: Is this run of SIERRA resuming a previous run that failed/did not finish?

            with_rendering: Is ARGoS headless rendering enabled? If so, we will need to kill all the
                            Xvfb processes that get run for each simulation after all experiments
                            are finished.
        """
        n_jobs = min(n_sims, max(1, int(multiprocessing.cpu_count() / float(n_threads_per_sim))))
        logging.info("Stage2: Running batched experiment in {0}: ".format(self.batch_exp_root) +
                     "sims_per_exp={0},threads_per_sim={1},n_jobs={2}".format(n_sims,
                                                                              n_threads_per_sim,
                                                                              n_jobs))

        exp_all = [os.path.join(self.batch_exp_root, d)
                   for d in self.criteria.gen_exp_dirnames(self.cmdopts)]
        exp_to_run = []

        if self.exec_exp_range is not None:
            min_exp = int(self.exec_exp_range.split(':')[0])
            max_exp = int(self.exec_exp_range.split(':')[1])
            assert min_exp <= max_exp, "FATAL: Min batch exp >= max batch exp({0} vs. {1})".format(
                min_exp, max_exp)

            exp_to_run = exp_all[min_exp: max_exp + 1]
        else:
            exp_to_run = exp_all

        # Verify environment
        assert os.environ.get(
            "ARGOS_PLUGIN_PATH") is not None, ("FATAL: You must have ARGOS_PLUGIN_PATH defined")
        assert os.environ.get(
            "LOG4CXX_CONFIGURATION") is not None, ("FATAL: You must LOG4CXX_CONFIGURATION defined")

        for exp in exp_to_run:
            ExpRunner(exp, exp_all.index(exp), self.cmdopts['hpc_env']).run(exec_method,
                                                                            n_jobs,
                                                                            exec_resume)

        # Cleanup Xvfb processes which were started in the background
        if with_rendering:
            subprocess.run(['killall', 'Xvfb'], check=True)


class ExpRunner:
    """
    Runs the specified  # of simulations in parallel using GNU Parallel on a provided set of hosts
    in an HPC environment, or on the current local machine.

    Attributes:
        exp_generation_root: Absolute path to the root directory for all generated simulation
                             input files for the experiment (i.e. an experiment directory
                             within the batch experiment root).
        exp_num: Experiment number in the batch.

    """

    def __init__(self, exp_generation_root: str, exp_num: int, hpc_env: str):
        self.exp_generation_root = os.path.abspath(exp_generation_root)
        self.exp_num = exp_num
        self.hpc_env = hpc_env

    def run(self, exec_method: str, n_jobs: int, exec_resume: bool):
        """
        Runs the simulations for a single experiment in parallel.

        Arguments:
            exec_method: Should the experiments be run in an HPC environment on on the local
                         machine?
            n_jobs: If running on a local machine, how many concurrent jobs are allowed? (Don't want
                    to oversubscribe the machine)
            exec_resume: Is this run of SIERRA resuming a previous run that failed/did not finish?

        """

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
            elif 'hpc' in exec_method and self.hpc_env == 'MSI':
                ExpRunner.__run_hpc_MSI(jobroot, cmdfile, joblog, exec_resume)
            else:
                assert False, "Bad exec method '{0}' or HPC env {1}".format(exec_method,
                                                                            self.hpc_env)

        # Catch the exception but do not raise it again so that additional experiments can still be
        # run if possible
        except subprocess.CalledProcessError as e:
            logging.error("Experiment failed! return code=%s", e.returncode)
            logging.error(e.output)

        elapsed = time.time() - start
        sys.stdout.write("{:.3f}s\n".format(elapsed))

    @staticmethod
    def __run_local(jobroot_path, cmdfile_path, joblog_path, n_jobs, exec_resume):
        resume = ''
        if exec_resume:
            resume = '--resume'

        cmd = 'cd {0} &&' \
            'parallel {1} --jobs {2} --results {0} --joblog {3} --no-notice < "{4}"'.format(
                jobroot_path,
                resume,
                n_jobs,
                joblog_path,
                cmdfile_path)
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def __run_hpc_MSI(jobroot_path, cmdfile_path, joblog_path, exec_resume):
        jobid = os.environ['PBS_JOBID']
        nodelist = os.path.join(jobroot_path, "{0}-nodelist.txt".format(jobid))

        resume = ''
        if exec_resume:
            resume = '--resume'

        cmd = 'sort -u $PBS_NODEFILE > {0} && ' \
            'parallel {1} --jobs 1 --results {3} --joblog {2} --sshloginfile {0} --workdir {3} < "{4}"'.format(
                nodelist,
                resume,
                joblog_path,
                jobroot_path,
                cmdfile_path)

        subprocess.run(cmd, shell=True, check=True)
