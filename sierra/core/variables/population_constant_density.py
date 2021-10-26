# Copyright 2021 John Harwell, All rights reserved.
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
Classes for the constant population density batch criteria. See
:ref:`ln-bc-population-constant-density` for usage documentation.

"""

# Core packages
import typing as tp
import logging
import math

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import constant_density as cd
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
from sierra.core.vector import Vector3D
from sierra.core.xml import XMLAttrChange, XMLAttrChangeSet
import sierra.core.plugin_manager as pm


@implements.implements(bc.IConcreteBatchCriteria)
class PopulationConstantDensity(cd.ConstantDensity):
    """
    A univariate range specifiying the population density (ratio of swarm size to arena size) to
    hold constant as swarm and arena size are increased. This class is a base class which should
    (almost) never be used on its own. Instead, the ``factory()`` function should be used to
    dynamically create derived classes expressing the user's desired density.

    Does not change the # blocks/block manifest.

    """

    def __init__(self, *args, **kwargs) -> None:
        cd.ConstantDensity.__init__(self, *args, **kwargs)
        self.already_added = False
        self.logger = logging.getLogger(__name__)

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate list of sets of changes to input file to set the # robots for a set of arena
        sizes such that the swarm density is constant. Robots are approximated as point masses.
        """
        if not self.already_added:
            for changeset in self.attr_changes:
                for path, attr, value in changeset:

                    if path == ".//arena" and attr == "size":
                        x, y, z = [int(float(_)) for _ in value.split(",")]
                        extent = sierra.core.utils.ArenaExtent(Vector3D(x, y, z))
                        # ARGoS won't start if there are 0 robots, so you always need to put at
                        # least 1.
                        n_robots = int(max(1, extent.area() * (self.target_density / 100.0)))
                        changeset.add(XMLAttrChange(".//arena/distribute/entity",
                                                    "quantity",
                                                    str(n_robots)))
                        self.logger.debug("Calculated swarm size=%d for extent=%s,density=%s",
                                          n_robots,
                                          str(extent), self.target_density)
                        break

            self.already_added = True

        return self.attr_changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, tp.Any]) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: tp.Dict[str, tp.Any],
                     exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[float]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ret = list(map(float, self.populations(cmdopts, exp_dirs)))

        if cmdopts['plot_log_xscale']:
            return [int(math.log2(x)) for x in ret]
        elif cmdopts['plot_enumerated_xscale']:
            return [i for i in range(0, len(ret))]
        else:
            return ret

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, tp.Any],
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ret = map(float, self.populations(cmdopts, exp_dirs))

        return list(map(lambda x: str(int(round(x, 4))), ret))

    def graph_xlabel(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        if cmdopts['plot_log_xscale']:
            return r"$\log_{2}$(Swarm Size)"

        return r"Swarm Size"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']


def factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            batch_input_root: str,
            **kwargs) -> PopulationConstantDensity:
    """
    Factory to create :class:`PopulationConstantDensity` derived classes from the command line
    definition.

    """
    attr = cd.Parser()(cli_arg)
    sgp = pm.module_load_tiered(kwargs['project'], 'generators.scenario_generator_parser')
    kw = sgp.ScenarioGeneratorParser().to_dict(kwargs['scenario'])

    is_2x1 = kw['arena_x'] == 2 * kw['arena_y']
    is_1x1 = kw['arena_x'] == kw['arena_y']

    if is_2x1:
        r = range(kw['arena_x'],
                  kw['arena_x'] + attr['cardinality'] * attr['arena_size_inc'],
                  attr['arena_size_inc'])
        dims = [sierra.core.utils.ArenaExtent(Vector3D(x, int(x / 2), kw['arena_z'])) for x in r]
    elif is_1x1:
        r = range(kw['arena_x'],
                  kw['arena_x'] + attr['cardinality'] * attr['arena_size_inc'],
                  attr['arena_size_inc'])

        dims = [sierra.core.utils.ArenaExtent(Vector3D(x, x, kw['arena_z'])) for x in r]
    else:
        raise NotImplementedError("Unsupported arena X,Y scaling '{0}': Must be [2x1,1x1]")

    def __init__(self) -> None:
        PopulationConstantDensity.__init__(self,
                                           cli_arg,
                                           main_config,
                                           batch_input_root,
                                           attr["target_density"],
                                           dims,
                                           kw['scenario_tag'])

    return type(cli_arg,  # type: ignore
                (PopulationConstantDensity,),
                {"__init__": __init__})


__api__ = [
    'PopulationConstantDensity'
]
