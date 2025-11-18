# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Container module for all plugins in SIERRA."""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import cmdline


class PluginCmdline(cmdline.BaseCmdline):
    """Base class for plugin cmdlines using :class:`argparse`.

    Note that this can't be in a cmdline.py in this folder because SIERRA will
    erroneouly pick it up as a plugin cmdline module.
    """

    def __init__(
        self,
        parents: list[argparse.ArgumentParser],
        stages: list[int],
    ) -> None:
        super().__init__()
        self._scaffold_cli(parents)
        self._init_cli(stages)

    def _scaffold_cli(self, parents: list[argparse.ArgumentParser]) -> None:
        """
        Scaffold CLI by defining the parser and common argument groups.
        """
        if parents:
            self.parser = argparse.ArgumentParser(
                prog="sierra-cli", parents=parents, add_help=False, allow_abbrev=False
            )
        else:
            self.parser = argparse.ArgumentParser(
                prog="sierra-cli", add_help=False, allow_abbrev=False
            )

        self.multistage = self.parser.add_argument_group(
            self.multistage_desc[0], self.multistage_desc[1]
        )
        self.stage1 = self.parser.add_argument_group(
            self.stage1_desc[0], self.stage1_desc[1]
        )
        self.stage2 = self.parser.add_argument_group(
            self.stage2_desc[0], self.stage2_desc[1]
        )
        self.stage3 = self.parser.add_argument_group(
            self.stage3_desc[0], self.stage3_desc[1]
        )
        self.stage4 = self.parser.add_argument_group(
            self.stage4_desc[0], self.stage4_desc[1]
        )
        self.stage5 = self.parser.add_argument_group(
            self.stage5_desc[0], self.stage5_desc[1]
        )
        self.shortforms = self.parser.add_argument_group(
            title="Shortform aliases",
            description="""
                        Most cmdline options to SIERRA are longform (i.e.,
                        ``--option``), but some families of options have
                        shortforms (i.e., ``-o`` for ``--option``) as
                        well. Shortform arguments behave the same as their
                        longform counterparts.
                        """,
        )

    def _init_cli(self, stages: list[int]) -> None:
        """Define cmdline arguments for stages 1-5."""
        if -1 in stages:
            self.init_shortforms()
            self.init_multistage()

        if 1 in stages:
            self.init_stage1()

        if 2 in stages:
            self.init_stage2()

        if 3 in stages:
            self.init_stage3()

        if 4 in stages:
            self.init_stage4()

        if 5 in stages:
            self.init_stage5()

    def init_shortforms(self) -> None:
        """
        Define cmdline shortform arguments for all pipeline stages.
        """

    def init_multistage(self) -> None:
        """
        Define cmdline arguments for all pipeline stages.
        """

    def init_stage1(self) -> None:
        """
        Define cmdline arguments for stage 1.
        """

    def init_stage2(self) -> None:
        """
        Define cmdline arguments for stage 2.
        """

    def init_stage3(self) -> None:
        """
        Define cmdline arguments for stage 3.
        """

    def init_stage4(self) -> None:
        """
        Define cmdline arguments for stage 4.
        """

    def init_stage5(self) -> None:
        """
        Define cmdline arguments for stage 5.
        """
