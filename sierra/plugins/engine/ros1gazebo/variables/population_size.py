# Copyright 2020 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""Classes for the population size batch criteria.

See :ref:`plugins/engine/ros1gazebo/bc/population-size` for usage
documentation.

"""

# Core packages
import typing as tp
import random
import logging
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.experiment import definition
from sierra.core import types, utils
from sierra.core.vector import Vector3D
from sierra.core.variables import population_size
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
        positions: list[Vector3D],
    ) -> None:
        population_size.PopulationSize.__init__(
            self, cli_arg, main_config, batch_input_root
        )
        self.sizes = sizes
        self.robot = robot
        self.positions = positions
        self.logger = logging.getLogger(__name__)
        if len(positions) < self.sizes[-1]:
            self.logger.warning(
                "# possible positions < # robots: %s < %s",
                len(positions),
                self.sizes[-1],
            )
        self.element_adds = []  # type: tp.List[definition.ElementAddList]

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        """Generate XML modifications to set system sizes."""
        if not self.element_adds:
            robot_config = self.main_config["ros"]["robots"][self.robot]
            prefix = robot_config["prefix"]
            model_base = robot_config["model"]
            model_variant = robot_config.get("model_variant", "")

            model = (
                f"{model_base}_{model_variant}" if model_variant != "" else model_base
            )

            desc_cmd = f"$(find xacro)/xacro $(find {model_base}_description)/urdf/{model}.urdf.xacro"
            for s in self.sizes:
                exp_adds = definition.ElementAddList()
                pos_i = random.randint(0, len(self.positions) - 1)

                exp_adds.append(definition.ElementAdd(".", "master", {}, True))
                exp_adds.append(
                    definition.ElementAdd("./master", "group", {"ns": "sierra"}, False)
                )
                exp_adds.append(
                    definition.ElementAdd(
                        "./master/group/[@ns='sierra']",
                        "param",
                        {"name": "experiment/n_agents", "value": str(s)},
                        False,
                    )
                )

                for i in range(0, s):

                    ns = f"{prefix}{i}"
                    pos = self.positions[pos_i]
                    pos_i = (pos_i + 1) % len(self.positions)
                    spawn_cmd_args = f"-urdf -model {model}_{ns} -x {pos.x} -y {pos.y} -z {pos.z} -param robot_description"

                    exp_adds.append(
                        definition.ElementAdd("./robot", "group", {"ns": ns}, True)
                    )

                    exp_adds.append(
                        definition.ElementAdd(
                            f"./robot/group/[@ns='{ns}']",
                            "param",
                            {"name": "tf_prefix", "value": ns},
                            True,
                        )
                    )

                    # These two tag adds are OK to use because:
                    #
                    # - All robots in Gazebo are created using spawn_model
                    #   initially.
                    #
                    # - All robots in Gazebo will provide a robot description
                    #   .urdf.xacro per ROS naming conventions
                    exp_adds.append(
                        definition.ElementAdd(
                            f"./robot/group/[@ns='{ns}']",
                            "param",
                            {"name": "robot_description", "command": desc_cmd},
                            True,
                        )
                    )

                    exp_adds.append(
                        definition.ElementAdd(
                            f"./robot/group/[@ns='{ns}']",
                            "node",
                            {
                                "name": "spawn_urdf",
                                "pkg": "gazebo_ros",
                                "type": "spawn_model",
                                "args": spawn_cmd_args,
                            },
                            True,
                        )
                    )

                self.element_adds.append(exp_adds)

        return self.element_adds

    def n_agents(self, exp_num: int) -> int:
        return int(len(self.element_adds[exp_num]) / len(self.element_adds[0]))


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition."""
    max_sizes = population_size.parse(cli_arg)

    if cmdopts["robot_positions"]:
        positions = [
            Vector3D.from_str(s, astype=float) for s in cmdopts["robot_positions"]
        ]
    else:
        # Get the dimensions of the effective arena from the scenario so we can
        # place robots randomly within it.
        kw = utils.gen_scenario_spec(cmdopts, **kwargs)

        xs = random.choices(range(0, kw["arena_x"]), k=max_sizes[-1])
        ys = random.choices(range(0, kw["arena_y"]), k=max_sizes[-1])
        zs = random.choices(range(0, kw["arena_z"]), k=max_sizes[-1])
        positions = [Vector3D(x, y, z) for x, y, z in zip(xs, ys, zs)]

    return PopulationSize(
        cli_arg,
        main_config,
        batch_input_root,
        cmdopts["robot"],
        max_sizes,
        positions,
    )


__all__ = ["PopulationSize"]
