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
from sierra.plugins.execenv import prefectserver
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(
    parents: list[argparse.ArgumentParser], stages: list[int]
) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``prefectserver.local`` execution environment.
    """
    return prefectserver.cmdline.PrefectCmdline(parents, stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return prefectserver.cmdline.to_cmdopts(args)
