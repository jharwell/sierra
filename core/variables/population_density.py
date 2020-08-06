# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#
"""
Classes for the population density batch criteria. See :ref:`ln-bc-population-density` for usage
documentation.
"""

import typing as tp
import os

from core.variables import constant_density as cd
import core.generators.scenario_generator_parser as sgp
import core.utils


class PopulationConstantDensity(cd.ConstantDensity):
    """
    A univariate range specifiying the population density (ratio of swarm size to arena size) to
    hold constant as swarm and arena size are increased. This class is a base class which should
    (almost) never be used on its own. Instead, the ``factory()`` function should be used to
    dynamically create derived classes expressing the user's desired density.

    Does not change the # blocks/block manifest.

    """

    # How many experiments to run for the given density value, in which the arena size is increased
    # from its initial value according to parsed parameters.
    kExperimentsPerDensity = 10

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 target_density: float,
                 dimensions: tp.List[core.utils.ArenaExtent],
                 dist_type: str) -> None:
        cd.ConstantDensity.__init__(self,
                                    cli_arg,
                                    main_config,
                                    batch_generation_root,
                                    target_density,
                                    dimensions,
                                    dist_type)

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes to input file to set the # robots for a set of arena
        sizes such that the swarm density is constant. Robots are approximated as point masses.
        """
        for changeset in self.changes:
            for path, attr, value in changeset:
                if path == ".//arena" and attr == "size":
                    x, y, z = [int(float(_)) for _ in value.split(",")]
                    extent = core.utils.ArenaExtent((x, y, z))
                    # ARGoS won't start if there are 0 robots, so you always need to put at least
                    # 1.
                    n_robots = int(max(1, (extent.x() * extent.y())
                                       * (self.target_density / 100.0)))
                    changeset.add((".//arena/distribute/entity", "quantity", str(n_robots)))
                    break

        return self.changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: tp.Dict[str, str],
                     exp_dirs: list = None) -> tp.List[float]:
        areas = []
        if exp_dirs is not None:
            dirs = exp_dirs
        else:
            dirs = self.gen_exp_dirnames(cmdopts)

        for d in dirs:
            pickle_fpath = os.path.join(self.batch_generation_root,
                                        d,
                                        "exp_def.pkl")
            exp_def = core.utils.unpickle_exp_def(pickle_fpath)
            for path, attr, value in exp_def:
                if path == ".//arena" and attr == "size":
                    extent = core.utils.ArenaExtent((value.split(",")))
                    areas.append(float((extent.x() * extent.y())))
        return areas

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, str],
                          exp_dirs: list = None) -> tp.List[str]:
        return [str(int(self.target_density / 100.0 * x)) for x in self.graph_xticks(cmdopts, exp_dirs)]

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return r"Population Size"

    def pm_query(self, pm) -> bool:
        return pm in ['blocks-transported', 'scalability', 'self-org']


def factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            batch_generation_root: str,
            **kwargs):
    """
    Factory to create ``ConstantDensity`` derived classes from the command line definition of batch
    criteria.

    """
    attr = cd.ConstantDensityParser().parse(cli_arg)
    kw = sgp.ScenarioGeneratorParser.reparse_str(kwargs['scenario'])

    if kw['dist_type'] == "SS" or kw['dist_type'] == "DS":
        r = range(kw['arena_x'],
                  kw['arena_x'] + PopulationConstantDensity.kExperimentsPerDensity *
                  attr['arena_size_inc'],
                  attr['arena_size_inc'])
        dims = [core.utils.ArenaExtent((x, int(x / 2), 0)) for x in r]
    elif kw['dist_type'] == "QS" or kw['dist_type'] == "RN" or kw['dist_type'] == 'PL':
        r = range(kw['arena_x'],
                  kw['arena_x'] + PopulationConstantDensity.kExperimentsPerDensity *
                  attr['arena_size_inc'],
                  attr['arena_size_inc'])
        dims = [core.utils.ArenaExtent((x, x, 0)) for x in r]
    else:
        raise NotImplementedError(
            "Unsupported block dstribution '{0}': Only SS,DS,QS,RN,PL supported".format(kw['dist_type']))

    def __init__(self) -> None:
        PopulationConstantDensity.__init__(self,
                                           cli_arg,
                                           main_config,
                                           batch_generation_root,
                                           attr["target_density"],
                                           dims,
                                           kw['dist_type'])

    return type(cli_arg,
                (PopulationConstantDensity,),
                {"__init__": __init__})


__api__ = [
    'PopulationConstantDensity'
]
