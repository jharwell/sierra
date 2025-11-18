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
from sierra.core import plugin as pm


def cmdline_parser(
    plugin: str, parents: list[argparse.ArgumentParser], stages: list[int]
) -> tp.Optional[argparse.ArgumentParser]:
    """
    Dispatches cmdline parser creation to selected plugin.

    If the selected plugin does not define a cmdline, None is returned.
    """
    path = "{}.cmdline".format(plugin)
    if pm.module_exists(path):
        module = pm.module_load_tiered(path)
        return module.build(parents, stages).parser

    return None
