# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Classes for the variable population density batch criteria.

See :ref:`plugins/engine/argos/bc/population-variable-density` for usage
documentation.

"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import variable_density as vd
from sierra.core.vector import Vector3D
from sierra.core.experiment import definition
from sierra.core import types, utils
from sierra.core.graphs import bcbridge


@implements.implements(bcbridge.IGraphable)
class PopulationVariableDensity(vd.VariableDensity):
    """Defines XML changes for variable population density within a single arena.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired density ranges.

    """

    def __init__(self, *args, **kwargs) -> None:
        vd.VariableDensity.__init__(self, *args, **kwargs)
        self.already_added = False
        self.logger = logging.getLogger(__name__)

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """Generate XML modifications to achieve the desired population densities.

        Robots are approximated as point masses.

        """
        if not self.already_added:
            for density in self.densities:
                # ARGoS won't start if there are 0 robots, so you always
                # need to put at least 1.
                n_agents = int(self.extent.area() * (density / 100.0))
                if n_agents == 0:
                    n_agents = 1
                    self.logger.warning(
                        "n_agents set to 1 even though \
                    calculated as 0 for area=%d,density=%s",
                        self.extent.area(),
                        density,
                    )
                changeset = definition.AttrChangeSet(
                    definition.AttrChange(
                        ".//arena/distribute/entity", "quantity", str(n_agents)
                    )
                )
                self.attr_changes.append(changeset)
                self.logger.debug(
                    "Calculated swarm size=%d for extent=%s,density=%s",
                    n_agents,
                    str(self.extent),
                    density,
                )

            self.already_added = True

        return self.attr_changes

    def graph_info(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[list[str]] = None,
    ) -> bcbridge.GraphInfo:
        info = bcbridge.GraphInfo(
            cmdopts,
            batch_output_root,
            exp_names if exp_names else self.gen_exp_names(),
        )

        info.xticks = [
            p / self.extent.area()
            for p in self.populations(info.cmdopts, info.exp_names)
        ]
        info.xticklabels = [str(round(x, 4)) for x in info.xticks]
        info.xlabel = "Population Density"
        return info

    def n_agents(self, exp_num: int) -> int:
        return int(self.extent.area() * self.densities[exp_num] / 100.0)


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationVariableDensity:
    """
    Create a :class:`PopulationVariableDensity` derived class.
    """
    densities = vd.parse(cli_arg)
    kw = utils.gen_scenario_spec(cmdopts, **kwargs)

    extent = utils.ArenaExtent(Vector3D(kw["arena_x"], kw["arena_y"], kw["arena_z"]))

    return PopulationVariableDensity(
        cli_arg, main_config, batch_input_root, densities, extent
    )


__all__ = ["PopulationVariableDensity"]
