#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types


class PathSet:
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 controllers: tp.List[str],
                 scenarios: tp.List[str]) -> None:
        assert not (controllers and scenarios)

        # We add the controller list to the directory path for the .csv
        # and graph directories so that multiple runs of stage5 with
        # different controller sets do not overwrite each other
        # (i.e. make stage5 more idempotent).
        if controllers:
            self.graph_root = pathlib.Path(cmdopts['sierra_root'],
                                           cmdopts['project'],
                                           '+'.join(controllers) + "-cc-graphs")

            self.csv_root = pathlib.Path(cmdopts['sierra_root'],
                                         cmdopts['project'],
                                         '+'.join(controllers) + "-cc-csvs")

            self.model_root = None

        if scenarios:
            # We add the scenario list to the directory path for the .csv
            # and graph directories so that multiple runs of stage5 with
            # different scenario sets do not overwrite each other (i.e. make
            # stage5 idempotent).
            self.graph_root = pathlib.Path(cmdopts['sierra_root'],
                                           cmdopts['project'],
                                           '+'.join(scenarios) + "-sc-graphs")
            self.csv_root = pathlib.Path(cmdopts['sierra_root'],
                                         cmdopts['project'],
                                         '+'.join(scenarios) + "-sc-csvs")
            self.model_root = pathlib.Path(cmdopts['sierra_root'],
                                           cmdopts['project'],
                                           '+'.join(scenarios) + "-sc-models")
