#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
Utility module for functionality for managing all the paths used in stage5.
"""
# Core packages
import pathlib
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types


class PathSet:
    """
    The set of filesystem paths used during stage 5.

    Collected here in the interest of DRY.

    Attributes:
        graph_root: The path where all graphs will be created.

        csv_root: The path where all collated CSVs will be stored.

        model_root: The path where all CSVs resulting from model execution will
                    be stored.
    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        controllers: tp.Optional[list[str]],
        scenarios: tp.Optional[list[str]],
    ) -> None:
        assert not (controllers and scenarios)

        # Exactly one of controllers/scenarios is populated (enforced above and
        # by the stage-5 dispatch), so all three roots are always assigned by
        # one of the branches below. Declared here so consumers see concrete,
        # non-Optional paths.
        self.graph_root: pathlib.Path
        self.csv_root: pathlib.Path
        self.model_root: pathlib.Path

        # We add the controller list to the directory path for the .csv
        # and graph directories so that multiple runs of stage5 with
        # different controller sets do not overwrite each other
        # (i.e. make stage5 more idempotent).
        if controllers:
            self.graph_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(controllers) + "-cc-graphs",
            ).resolve()

            self.csv_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(controllers) + "-cc-csvs",
            ).resolve()

            self.model_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(controllers) + "-cc-models",
            ).resolve()

        if scenarios:
            # We add the scenario list to the directory path for the .csv
            # and graph directories so that multiple runs of stage5 with
            # different scenario sets do not overwrite each other (i.e. make
            # stage5 idempotent).
            self.graph_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(scenarios) + "-sc-graphs",
            ).resolve()
            self.csv_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(scenarios) + "-sc-csvs",
            ).resolve()
            self.model_root = pathlib.Path(
                cmdopts["sierra_root"],
                cmdopts["project"],
                "+".join(scenarios) + "-sc-models",
            ).resolve()


__all__ = ["PathSet"]
