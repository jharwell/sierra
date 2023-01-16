# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Sanity checks for verifying selected plugins.

Checks that selected plugins implement the necessary classes and
 functions. Currently checkes: ``--storage-medium``, ``--exec-env``, and
 ``--platform``.

"""

# Core packages
import inspect
import logging

# 3rd party packages

# Project packages


def storage_sanity_checks(module) -> None:
    """
    Check the selected ``--storage-medium`` plugin.
    """
    logging.trace("Verifying --storage-medium plugin interface")  # type: ignore

    functions = ['df_read',
                 'df_write']
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert (any(f in name for (name, _) in in_module)),\
            f"Storage medium plugin does not define {f}"


def exec_env_sanity_checks(module) -> None:
    """
    Check the selected ``--exec-env`` plugin.
    """
    logging.trace("Verifying --exec-env plugin interface")  # type: ignore

    in_module = inspect.getmembers(module, inspect.isclass)

    opt_classes = ['ParsedCmdlineConfigurer',
                   'ExpRunShellCmdsGenerator',
                   'ExpShellCmdsGenerator',
                   'ExecEnvChecker']

    for c in opt_classes:
        if not any(c in name for (name, _) in in_module):
            logging.debug(("Execution environment plugin '%s' does not define "
                           "'%s'"),
                          module.__name__,
                          c)


def platform_sanity_checks(module) -> None:
    """
    Check the selected ``--platform`` plugin.
    """
    logging.trace("Verifying --platform plugin interface")  # type: ignore

    req_classes = ['ExpConfigurer',
                   'CmdlineParserGenerator'
                   ]

    req_functions = ['population_size_from_def',
                     'population_size_from_pickle',
                     ]

    opt_classes = ['ParsedCmdlineConfigurer',
                   'ExpRunShellCmdsGenerator',
                   'ExpShellCmdsGenerator',
                   'ExecEnvChecker']

    opt_functions = ['robot_prefix_extract',
                     'arena_dims_from_criteria']

    in_module = inspect.getmembers(module, inspect.isclass)

    for c in req_classes:
        assert (any(c in name for (name, _) in in_module)),\
            f"Platform plugin '{module.__name__}' does not define '{c}'"

    for f in opt_classes:
        if not any(f in name for (name, _) in in_module):
            logging.debug(("Platform plugin '%s' not define define '%s'"
                           "--some SIERRA functionality may not be available. "
                           "See docs for details."),
                          module.__name__,
                          f)

    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in req_functions:
        assert (any(f in name for (name, _) in in_module)),\
            f"Platform plugin '{module.__name__}' does not define '{f}()'"

    for f in opt_functions:
        if not any(f in name for (name, _) in in_module):
            logging.debug(("Platform plugin '%s' not define define '%s()'"
                           "--some SIERRA functionality may not be available. "
                           "See docs for details."),
                          module.__name__,
                          f)


__api__ = {
    'storage_sanity_checks',
    'exec_env_sanity_checks',
    'platform_sanity_checks'
}
