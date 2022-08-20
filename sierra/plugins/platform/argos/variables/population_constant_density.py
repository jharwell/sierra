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
"""Classes for the constant population density batch criteria.

See :ref:`ln-sierra-platform-argos-bc-population-constant-density` for usage
documentation.

"""

# Core packages
import typing as tp
import logging
import math

# 3rd party packages
import implements

# Project packages
from sierra.plugins.platform.argos.variables import constant_density as cd
from sierra.core import utils, types
import sierra.core.variables.batch_criteria as bc
from sierra.core.vector import Vector3D
from sierra.core.experiment import xml


@implements.implements(bc.IConcreteBatchCriteria)
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

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """Generate XML modifications to to maintain constant population density.

        Robots are approximated as point masses.

        """
        if not self.already_added:
            for changeset in self.attr_changes:
                for path, attr, value in changeset:

                    if path == ".//arena" and attr == "size":
                        x, y, z = [int(float(_)) for _ in value.split(",")]
                        extent = utils.ArenaExtent(
                            Vector3D(x, y, z))
                        # ARGoS won't start if there are 0 robots, so you always
                        # need to put at least 1.
                        n_robots = int(extent.area() *
                                       (self.target_density / 100.0))
                        if n_robots == 0:
                            n_robots = 1
                            self.logger.warning(("n_robots set to 1 even though "
                                                 "calculated as 0 for area=%s,"
                                                 "density=%s"),
                                                str(extent.area()),
                                                self.target_density / 100.0)

                        changeset.add(xml.AttrChange(".//arena/distribute/entity",
                                                     "quantity",
                                                     str(n_robots)))
                        self.logger.debug("Calculated population size=%d for extent=%s,density=%s",
                                          n_robots,
                                          str(extent), self.target_density)
                        break

            self.already_added = True

        return self.attr_changes

    def gen_exp_names(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:

        if exp_names is None:
            exp_names = self.gen_exp_names(cmdopts)

        ret = list(map(float, self.populations(cmdopts, exp_names)))

        if cmdopts['plot_log_xscale']:
            return [int(math.log2(x)) for x in ret]
        elif cmdopts['plot_enumerated_xscale']:
            return list(range(0, len(ret)))
        else:
            return ret

    def graph_xticklabels(self,
                          cmdopts: types.Cmdopts,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        if exp_names is None:
            exp_names = self.gen_exp_names(cmdopts)

        ret = map(float, self.populations(cmdopts, exp_names))

        return list(map(lambda x: str(int(round(x, 4))), ret))

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        if cmdopts['plot_log_xscale']:
            return r"$\log_{2}$(Population Size)"

        return r"Population Size"

    def n_robots(self, exp_num: int) -> int:
        return int(self.target_density / 100.0 * self.dimensions[exp_num].area())


def calc_dims(cmdopts: types.Cmdopts,
              attr: types.CLIArgSpec,
              **kwargs) -> tp.List[utils.ArenaExtent]:

    kw = utils.gen_scenario_spec(cmdopts, **kwargs)

    is_2x1 = kw['arena_x'] == 2 * kw['arena_y']
    is_1x1 = kw['arena_x'] == kw['arena_y']

    if is_2x1:
        r = range(kw['arena_x'],
                  kw['arena_x'] + attr['cardinality'] * attr['arena_size_inc'],
                  attr['arena_size_inc'])
        return list(utils.ArenaExtent(Vector3D(x, int(x / 2), kw['arena_z'])) for x in r)
    elif is_1x1:
        r = range(kw['arena_x'],
                  kw['arena_x'] + attr['cardinality'] * attr['arena_size_inc'],
                  attr['arena_size_inc'])

        return list(utils.ArenaExtent(Vector3D(x, x, kw['arena_z'])) for x in r)
    else:
        raise NotImplementedError(
            "Unsupported arena X,Y scaling '{0}': Must be [2x1,1x1]")


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            **kwargs) -> PopulationConstantDensity:
    """Create a :class:`PopulationConstantDensity` derived class.

    """
    attr = cd.Parser()(cli_arg)
    kw = utils.gen_scenario_spec(cmdopts, **kwargs)
    dims = calc_dims(cmdopts, attr, **kwargs)

    def __init__(self) -> None:
        PopulationConstantDensity.__init__(self,
                                           cli_arg,
                                           main_config,
                                           cmdopts['batch_input_root'],
                                           attr["target_density"],
                                           dims,
                                           kw['scenario_tag'])

    return type(cli_arg,  # type: ignore
                (PopulationConstantDensity,),
                {"__init__": __init__})


__api__ = [
    'PopulationConstantDensity'
]
