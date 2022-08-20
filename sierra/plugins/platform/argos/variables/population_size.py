# Copyright 2020 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
#
# SIERRA is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SIERRA.  If not, see <http://www.gnu.org/licenses/
"""Classes for the population size batch criteria.

See :ref:`ln-sierra-platform-argos-bc-population-size` for usage documentation.

"""

# Core packages
import typing as tp
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.experiment import xml
from sierra.core import types
from sierra.core.variables import population_size


@implements.implements(bc.IConcreteBatchCriteria)
@implements.implements(bc.IQueryableBatchCriteria)
class PopulationSize(population_size.BasePopulationSize):
    """A univariate range of swarm sizes used to define batch experiments.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired size distribution.

    Note: Usage of this class assumes homogeneous swarms.

    Attributes:

        size_list: List of integer swarm sizes defining the range of the
                   variable for the batch experiment.

    """

    @staticmethod
    def gen_attr_changelist_from_list(sizes: tp.List[int]) -> tp.List[xml.AttrChangeSet]:
        return [xml.AttrChangeSet(xml.AttrChange(".//arena/distribute/entity",
                                                 "quantity",
                                                 str(s)))
                for s in sizes]

    def __init__(self,
                 cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path,
                 size_list: tp.List[int]) -> None:
        population_size.BasePopulationSize.__init__(self,
                                                    cli_arg,
                                                    main_config,
                                                    batch_input_root)
        self.size_list = size_list
        self.attr_changes = []  # type: tp.List[xml.AttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """
        Generate list of sets of changes for swarm sizes to define a batch experiment.
        """
        if not self.attr_changes:
            self.attr_changes = PopulationSize.gen_attr_changelist_from_list(
                self.size_list)
        return self.attr_changes

    def gen_exp_names(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def n_robots(self, exp_num: int) -> int:
        return self.size_list[exp_num]


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            **kwargs) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition.

    """
    parser = population_size.Parser()
    max_sizes = parser.to_sizes(parser(cli_arg))

    def __init__(self) -> None:
        PopulationSize.__init__(self,
                                cli_arg,
                                main_config,
                                cmdopts['batch_input_root'],
                                max_sizes)

    return type(cli_arg,  # type: ignore
                (PopulationSize,),
                {"__init__": __init__})


__api__ = [
    'PopulationSize'
]
