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
Classes for the variable population density batch criteria. See
:ref:`ln-bc-population-variable-density` for usage documentation.
"""

# Core packages
import typing as tp
import logging
import numpy as np

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import variable_density as vd
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
from sierra.core.vector import Vector3D
from sierra.core.xml import XMLAttrChange, XMLAttrChangeSet
import sierra.core.plugin_manager as pm
from sierra.core.utils import ArenaExtent


@implements.implements(bc.IConcreteBatchCriteria)
class PopulationVariableDensity(vd.VariableDensity):
    """
    A univariate range specifiying the population density (ratio of swarm size to arena size) to
    vary as arena size is held constant. Instead, the ``factory()`` function should be used to
    dynamically create derived classes expressing the user's desired density ranges.

    Does not change the # blocks/block manifest.

    """

    def __init__(self, *args, **kwargs) -> None:
        vd.VariableDensity.__init__(self, *args, **kwargs)
        self.already_added = False
        self.logger = logging.getLogger(__name__)

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate list of sets of changes to input file to set the # robots for a set of swarm
        densities. Robots are approximated as point masses.
        """
        if not self.already_added:
            for density in self.densities:
                # ARGoS won't start if there are 0 robots, so you always need to put at
                # least 1.
                n_robots = int(max(1, self.extent.area() * (density / 100.0)))
                changeset = XMLAttrChangeSet(XMLAttrChange(".//arena/distribute/entity",
                                                           "quantity",
                                                           str(n_robots)))
                self.attr_changes.append(changeset)
                self.logger.debug("Calculated swarm size=%d for extent=%s,density=%s",
                                  n_robots,
                                  str(self.extent),
                                  density)

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

        return [p / self.extent.area() for p in self.populations(cmdopts, exp_dirs)]

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, tp.Any],
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        return list(map(lambda x: str(round(x, 4)), self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        return r"Swarm Density"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']


def factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            batch_input_root: str,
            **kwargs) -> PopulationVariableDensity:
    """
    Factory to create :class:`PopulationVariableDensity` derived classes from the command line
    definition.

    """
    attr = vd.Parser()(cli_arg)
    sgp = pm.module_load_tiered(kwargs['project'], 'generators.scenario_generator_parser')
    kw = sgp.ScenarioGeneratorParser().to_dict(kwargs['scenario'])
    extent = ArenaExtent(Vector3D(kw['arena_x'], kw['arena_y'], kw['arena_z']))

    densities = [x for x in np.linspace(attr['density_min'],
                                        attr['density_max'],
                                        num=attr['cardinality'])]

    def __init__(self) -> None:
        PopulationVariableDensity.__init__(self,
                                           cli_arg,
                                           main_config,
                                           batch_input_root,
                                           densities,
                                           extent)

    return type(cli_arg,  # type: ignore
                (PopulationVariableDensity,),
                {"__init__": __init__})


__api__ = [
    'PopulationVariableDensity'
]
