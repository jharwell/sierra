# Copyright 2021 John Harwell, All rights reserved.
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

# Core packages
import typing as tp

# 3rd party packages

# Project packages


def env_configure(args):
    """
     Configure SIERRA for HPC by reading environment variables and modifying
     the parsed cmdline arguments (namespace object) as needed. Arguments of
     interest include:

     - --exec-sims-per-node
     - --physics-n-engines

     Though you can modify whatever you want.
     """

 def argos_cmd_generate(input_fpath: str):
     """
     Generate the ARGoS cmd to run in the HPC environment, given the path to
     an input file. Depending on your environment, you may want to use
     SIERRA_ARCH to chose a version of ARGoS compiled for a given architecture
     for maximum performance.
     """

 def gnu_parallel_cmd_generate(parallel_opts: dict):
     """
     Given a dictionary containing job information, generate the cmd to
     correctly invoke GNU Parallel on the HPC environment. The job information
     dictionary contains:

     - ``jobroot_path`` - The root directory GNU parallel will run in.
     - ``cmdfile_path`` - The absolute path to the file containing the ARGoS commands
                          to execute.
     - ``joblog_path``  - The absolute path to the log file that GNU parallel will log job progress
                          to.
     - ``exec-resume``  - Is this invocation resuming a previously failed/incomplete run?
     - ``n_jobs``       - How many jobs to run in parallel.
     """

def xvfb_cmd_generate(cmdopts: tp.Dict[str, tp.Any]):
    """
    Generate the command for running ARGoS under Xvfb for headless rendering, using the dictionary
    of parsed cmdline options. If your HPC environment does not support this, return ``''``.
    """
