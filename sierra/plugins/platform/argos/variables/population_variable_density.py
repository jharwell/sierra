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
:ref:`ln-platform-argos-bc-population-variable-density` for usage
documentation.
"""

# Core packages
import typing as tp
import logging  # type: tp.Any
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
from sierra.core import types


@implements.implements(bc.IConcreteBatchCriteria)
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

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate list of sets of changes to input file to set the # robots for a
        set of swarm densities. Robots are approximated as point masses.
        """
        if not self.already_added:
            for density in self.densities:
                # ARGoS won't start if there are 0 robots, so you always
                # need to put at least 1.
                n_robots = int(self.extent.area() *
                               (self.target_density / 100.0))
                if n_robots == 0:
                    n_robots = 1
                    self.logger.warning("n_robots set to 1 even though \
                    calculated as 0 for area=%s,density=%s",
                                        self.extent.area,
                                        self.target_density)
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

    def gen_exp_dirnames(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
                     exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[float]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        return [p / self.extent.area() for p in self.populations(cmdopts, exp_dirs)]

    def graph_xticklabels(self,
                          cmdopts: types.Cmdopts,
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        return list(map(lambda x: str(round(x, 4)), self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        return r"Swarm Density"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            **kwargs) -> PopulationVariableDensity:
    """
    Factory to create :class:`PopulationVariableDensity` derived classes from
    the command line definition.
    """
    attr = vd.Parser()(cli_arg)
    sgp = pm.module_load_tiered(project=cmdopts['project'],
                                path='generators.scenario_generator_parser')

    # scenario is passed in kwargs during stage 5 (can't be passed via
    # --scenario in general )
    if 'scenario' in kwargs:
        scenario = kwargs['scenario']
    else:
        scenario = cmdopts['scenario']

    kw = sgp.ScenarioGeneratorParser().to_dict(scenario)
    extent = ArenaExtent(Vector3D(kw['arena_x'], kw['arena_y'], kw['arena_z']))

    densities = [x for x in np.linspace(attr['density_min'],
                                        attr['density_max'],
                                        num=attr['cardinality'])]

    def __init__(self) -> None:
        PopulationVariableDensity.__init__(self,
                                           cli_arg,
                                           main_config,
                                           cmdopts['batch_input_root'],
                                           densities,
                                           extent)

    return type(cli_arg,  # type: ignore
                (PopulationVariableDensity,),
                {"__init__": __init__})


__api__ = [
    'PopulationVariableDensity'
]
