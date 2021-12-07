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

# 3rd party packages

# Project packages
import sierra.plugins.platform.rosgazebo.cmdline as cmd
from sierra.core import hpc, xml, platform, config


def cmdline_parser_generate() -> argparse.ArgumentParser:
    parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
    return cmd.PlatformCmdline(parents=[parser],
                               stages=[-1, 1, 2, 3, 4, 5]).parser


def launch_cmd_generate(exec_env: str, input_fpath: str) -> str:
    if exec_env in ['hpc.local']:
        # First, the cmd to start roscore. We need to be on a unique port so
        # that multiple ROS instances corresponding to multiple Gazebo instances
        # with the same topic names are considered distinct/not accessible
        # between instances of Gazebo.
        roscore_port = platform.get_free_port()

        # Second, the command to start Gazebo via roslaunch. We need to be on a
        # unique port so that multiple Gazebo instances can be run in
        # parallel. Note the -p argument to start a NEW roscore instance on the
        # current machine with the selected port.
        gazebo_port = platform.get_free_port()
        roslaunch = '{0} -p {1} {2}{3}'.format(config.kROS['launch_cmd'],
                                               roscore_port,
                                               input_fpath,
                                               config.kROS['launch_file_ext'])

        # 2021/12/13: You can't use HTTPS for some reason or gazebo won't
        # start...
        export_ros = f'ROS_MASTER_URI=http://localhost:{roscore_port}'
        export_gazebo = f'GAZEBO_MASTER_URI=http://localhost:{gazebo_port}'

        return f'{export_ros} {export_gazebo} {roslaunch}'
    else:
        assert False, f"Unsupported exec environment '{exec_env}'"


def population_size_extract(adds_def: xml.XMLLuigi) -> int:
    size = 0
    for add in adds_def:
        if (add.tag == "node" and "args" in add.attr and
                "robot_description" in add.attr["args"]):
            size += 1
    return size
