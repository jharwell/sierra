# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Sanity checks for verifying selected plugins.

Checks that selected plugins implement the necessary classes and
 functions. Currently checkes: ``--storage``, ``--exec-env``, and
 ``--engine``.

"""

# Core packages
import inspect
import logging

# 3rd party packages

# Project packages


def storage_sanity_checks(medium: str, module) -> None:
    """
    Check the selected ``--storage`` plugin.
    """
    logging.trace("Verifying --storage plugin interface")  # type: ignore

    functions = ["df_read", "df_write"]
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert any(
            f in name for (name, _) in in_module
        ), f"Storage medium {medium} does not define {f}()"


def exec_env_sanity_checks(exec_env: str, module) -> None:
    """
    Check the selected ``--exec-env`` plugin.
    """
    logging.trace("Verifying --exec-env plugin interface")  # type: ignore

    in_module = inspect.getmembers(module, inspect.isclass)

    opt_functions = ["cmdline_postparse_configure", "exec_env_checker"]
    opt_classes = ["ExpRunShellCmdsGenerator", "ExpShellCmdsGenerator"]

    for c in opt_classes:
        if not any(c in name for (name, _) in in_module):
            logging.debug(
                (
                    "Execution environment plugin %s does not define "
                    "%s--some SIERRA functionality may not be "
                    "available. See docs for details."
                ),
                exec_env,
                c,
            )

    for f in opt_functions:
        if not any(f in name for (name, _) in in_module):
            logging.debug(
                ("Execution environment plugin %s does not define " "%s()."),
                exec_env,
                f,
            )


def engine_sanity_checks(engine: str, module) -> None:
    """
    Check the selected ``--engine`` plugin.
    """
    logging.trace("Verifying --engine plugin interface")  # type: ignore

    req_classes = [
        "ExpConfigurer",
    ]

    req_functions = [
        "cmdline_parser",
        "population_size_from_def",
        "population_size_from_pickle",
    ]

    opt_classes = ["ExpRunShellCmdsGenerator", "ExpShellCmdsGenerator"]

    opt_functions = [
        "cmdline_postparse_configure",
        "exec_env_checker",
        "agent_prefix_extract",
        "arena_dims_from_criteria",
    ]

    in_module = inspect.getmembers(module, inspect.isclass)

    for c in req_classes:
        assert any(
            c in name for (name, _) in in_module
        ), f"Engine plugin {engine} does not define {c}"

    for f in opt_classes:
        if not any(f in name for (name, _) in in_module):
            logging.debug(
                (
                    "Engine plugin %s does not define %s"
                    "--some SIERRA functionality may not be available. "
                    "See docs for details."
                ),
                engine,
                f,
            )

    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in req_functions:
        assert any(
            f in name for (name, _) in in_module
        ), f"Engine plugin {engine} does not define {f}()"

    for f in opt_functions:
        if not any(f in name for (name, _) in in_module):
            logging.debug(
                (
                    "Engine plugin %s does not define %s()"
                    "--some SIERRA functionality may not be available. "
                    "See docs for details."
                ),
                engine,
                f,
            )


__all__ = ["storage_sanity_checks", "exec_env_sanity_checks", "engine_sanity_checks"]
