# Copyright 2020 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""Classes for the population size batch criteria.

See :ref:`plugins/engine/ros1robot/bc/population-size` for usage
documentation.

"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types
from sierra.core.variables import population_size
from sierra.core.experiment import definition
from sierra.core.graphs import bcbridge


@implements.implements(bcbridge.IGraphable)
@implements.implements(bc.IQueryableBatchCriteria)
class PopulationSize(population_size.PopulationSize):
    """A univariate range of system sizes used to define batch experiments.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired size distribution.

    Note: Usage of this class assumes homogeneous systems.

    Attributes:
        size_list: List of integer system sizes defining the range of the
                   variable for the batch experiment.

    """

    def __init__(
        self,
        cli_arg: str,
        main_config: types.YAMLDict,
        batch_input_root: pathlib.Path,
        robot: str,
        sizes: list[int],
    ) -> None:
        population_size.PopulationSize.__init__(
            self, cli_arg, main_config, batch_input_root
        )
        self.sizes = sizes
        self.robot = robot
        self.logger = logging.getLogger(__name__)
        self.element_adds = []  # type: tp.List[definition.ElementAddList]

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        """
        Generate XML modifications to set system sizes.
        """
        if not self.element_adds:
            robot_config = self.main_config["ros"]["robots"][self.robot]
            prefix = robot_config["prefix"]

            for s in self.sizes:
                per_robot = definition.ElementAddList()
                per_robot.append(definition.ElementAdd(".", "master", {}, True))
                per_robot.append(
                    definition.ElementAdd("./master", "group", {"ns": "sierra"}, False)
                )
                per_robot.append(
                    definition.ElementAdd(
                        "./master/group/[@ns='sierra']",
                        "param",
                        {"name": "experiment/n_agents", "value": str(s)},
                        False,
                    )
                )

                for i in range(0, s):

                    # Note that we don't try to do any of the robot bringup
                    # here--we can't know the exact node/package names without
                    # using a lot of (brittle) config.
                    ns = f"{prefix}{i}"
                    per_robot.append(
                        definition.ElementAdd("./robot", "group", {"ns": ns}, True)
                    )

                    per_robot.append(
                        definition.ElementAdd(
                            f"./robot/group/[@ns='{ns}']",
                            "param",
                            {"name": "tf_prefix", "value": ns},
                            True,
                        )
                    )

                self.element_adds.append(per_robot)

        return self.element_adds

    def n_agents(self, exp_num: int) -> int:
        return self.sizes[exp_num]


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition."""
    max_sizes = population_size.parse(cli_arg)

    return PopulationSize(
        cli_arg, main_config, batch_input_root, cmdopts["robot"], max_sizes
    )


__all__ = ["PopulationSize"]
