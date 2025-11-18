#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Command line definitions for the :ref:`plugins/execenv/hpc/PBS`."""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.plugins.execenv import hpc
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(
    parents: list[argparse.ArgumentParser], stages: list[int]
) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``hpc.adhoc`` execution environment.
    """
    return hpc.cmdline.HPCCmdline(parents, stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return hpc.cmdline.to_cmdopts(args)
