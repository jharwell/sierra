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
import inspect
import logging  # type: tp.Any

# 3rd party packages

# Project packages


def storage_sanity_checks(module) -> None:
    logging.trace("Verifying selected --storage-medium plugin interface")

    functions = ['df_read',
                 'df_write']
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert (any([f in name for name, _ in in_module])),\
            f"Storage medium plugin does not define {f}"


def exec_env_sanity_checks(module) -> None:
    logging.trace("Verifying selected --exec-env plugin interface")

    classes = ['ParsedCmdlineConfigurer',
               'ExpRunShellCmdsGenerator',
               'ExpShellCmdsGenerator',
               'ExecEnvChecker'
               ]
    in_module = inspect.getmembers(module, inspect.isclass)
    for c in classes:
        assert (any([c in name for name, _ in in_module])),\
            f"Execution environment plugin '{module.__name__}' does not define '{c}'"


def platform_sanity_checks(module) -> None:
    logging.trace("Verifying selected --platform plugin interface")

    classes = ['ParsedCmdlineConfigurer',
               'ExpRunShellCmdsGenerator',
               'ExpShellCmdsGenerator',
               'ExpConfigurer',
               'ExecEnvChecker',
               'CmdlineParserGenerator'
               ]
    functions = ['population_size_from_def',
                 'population_size_from_pickle',
                 'robot_prefix_extract'
                 ]
    in_module = inspect.getmembers(module, inspect.isclass)

    for c in classes:
        assert (any([c in name for name, _ in in_module])),\
            f"Platform plugin '{module.__name__}' does not define '{c}'"

    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert (any([f in name for name, _ in in_module])),\
            f"Platform plugin '{module.__name__}' does not define '{f}'"
