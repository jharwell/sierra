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
import argparse
import os

# 3rd party packages

# Project packages
import sierra.plugins.platform.argos.cmdline as cmd
from sierra.core import hpc, xml, config


def cmdline_parser_generate() -> argparse.ArgumentParser:
    parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
    return cmd.PlatformCmdline(parents=[parser],
                               stages=[-1, 1, 2, 3, 4, 5]).parser


def launch_cmd_generate(exec_env: str, input_fpath: str) -> str:
    if exec_env in ['hpc.local', 'hpc.adhoc']:
        cmd = '{0} -c {1}{2}'.format(config.kARGoS['launch_cmd'],
                                     input_fpath,
                                     config.kARGoS['launch_file_ext'])
    elif exec_env in ['hpc.slurm', 'hpc.adhoc']:
        cmd = '{0}-{1} -c {2}'.format(config.kARGoS['launch_cmd'],
                                      os.environ['SIERRA_ARCH'],
                                      input_fpath)
    else:
        assert False, f"Unsupported exec environment '{exec_env}'"

        # ARGoS is pretty good about not printing stuff if we pass these
        # arguments. We don't want to pass > /dev/null so that we get the text
        # of any exceptions that cause ARGoS to crash.
    cmd += ' --log-file /dev/null --logerr-file /dev/null'
    return cmd


def population_size_extract(exp_def: xml.XMLLuigi) -> int:
    for path, attr, value in exp_def:
        if path == ".//arena/distribute/entity" and attr == "quantity":
            return int(value)

    return -1
