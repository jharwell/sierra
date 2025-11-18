# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Classes for the constant population density batch criteria.

See :ref:`plugins/engine/argos/bc/population-constant-density` for usage
documentation.

"""

# Core packages
import typing as tp
import logging
import math
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.plugins.engine.argos.variables import constant_density as cd
from sierra.core import utils, types
from sierra.core.vector import Vector3D
from sierra.core.experiment import definition
from sierra.core.graphs import bcbridge


@implements.implements(bcbridge.IGraphable)
class PopulationConstantDensity(cd.ConstantDensity):
    """Defines XML changes for maintain population density across arena sizes.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired density.

    Does not change the # blocks/block manifest.

    """

    def __init__(self, *args, **kwargs) -> None:
        cd.ConstantDensity.__init__(self, *args, **kwargs)
        self.already_added = False
        self.logger = logging.getLogger(__name__)

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """Generate XML modifications to to maintain constant population density.

        Robots are approximated as point masses.

        """
        if not self.already_added:
            for changeset in self.attr_changes:
                for path, attr, value in changeset:

                    if path == ".//arena" and attr == "size":
                        x, y, z = [int(float(_)) for _ in value.split(",")]
                        extent = utils.ArenaExtent(Vector3D(x, y, z))
                        # ARGoS won't start if there are 0 robots, so you always
                        # need to put at least 1.
                        n_agents = int(extent.area() * (self.target_density / 100.0))
                        if n_agents == 0:
                            n_agents = 1
                            self.logger.warning(
                                (
                                    "n_agents set to 1 even though "
                                    "calculated as 0 for area=%s,"
                                    "density=%s"
                                ),
                                str(extent.area()),
                                self.target_density / 100.0,
                            )

                        changeset.add(
                            definition.AttrChange(
                                ".//arena/distribute/entity", "quantity", str(n_agents)
                            )
                        )
                        self.logger.debug(
                            "Calculated population size=%d for extent=%s,density=%s",
                            n_agents,
                            str(extent),
                            self.target_density,
                        )
                        break

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
        if info.cmdopts["plot_log_xscale"]:
            info.xlabel = r"$\log_{2}$(Population Size)"
        else:
            info.xlabel = "Population Size"

        tmp = map(float, self.populations(info.cmdopts, info.exp_names))

        info.xticklabels = [str(int(round(x, 4))) for x in tmp]

        tmp2 = list(map(float, self.populations(info.cmdopts, info.exp_names)))

        if info.cmdopts["plot_log_xscale"]:
            info.xticks = [int(math.log2(x)) for x in tmp2]
        elif info.cmdopts["plot_enumerated_xscale"]:
            info.xticks = list(range(0, len(tmp2)))

        return info

    def n_agents(self, exp_num: int) -> int:
        return int(self.target_density / 100.0 * self.dimensions[exp_num].area())


def calc_dims(
    cmdopts: types.Cmdopts, attr: types.CLIArgSpec, **kwargs
) -> list[utils.ArenaExtent]:

    kw = utils.gen_scenario_spec(cmdopts, **kwargs)

    is_2x1 = kw["arena_x"] == 2 * kw["arena_y"]
    is_1x1 = kw["arena_x"] == kw["arena_y"]

    if is_2x1:
        r = range(
            kw["arena_x"],
            kw["arena_x"] + attr["cardinality"] * attr["arena_size_inc"],
            attr["arena_size_inc"],
        )
        return [
            utils.ArenaExtent(Vector3D(x, int(x / 2), kw["arena_z"])) for x in r
        ]

    if is_1x1:
        r = range(
            kw["arena_x"],
            kw["arena_x"] + attr["cardinality"] * attr["arena_size_inc"],
            attr["arena_size_inc"],
        )

        return [utils.ArenaExtent(Vector3D(x, x, kw["arena_z"])) for x in r]

    raise NotImplementedError("Unsupported arena X,Y scaling '{0}': Must be [2x1,1x1]")


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationConstantDensity:
    """Create a :class:`PopulationConstantDensity` derived class."""
    attr = cd.parse(cli_arg)
    kw = utils.gen_scenario_spec(cmdopts, **kwargs)
    dims = calc_dims(cmdopts, attr, **kwargs)

    return PopulationConstantDensity(
        cli_arg,
        main_config,
        batch_input_root,
        attr["target_density"],
        dims,
        kw["scenario_tag"],
    )


__all__ = ["PopulationConstantDensity"]
