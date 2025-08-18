#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.plugins.execenv import hpc
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(
    parents: tp.List[argparse.ArgumentParser], stages: tp.List[int]
) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``hpc.slurm`` execution environment.
    """
    return hpc.cmdline.HPCCmdline(parents, stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return hpc.cmdline.to_cmdopts(args)
