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

See :ref:`ln-sierra-platform-ros1robot-bc-population-size` for usage
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
from sierra.core.experiment import xml


@implements.implements(bc.IConcreteBatchCriteria)
@implements.implements(bc.IQueryableBatchCriteria)
class PopulationSize(population_size.BasePopulationSize):
    """A univariate range of system sizes used to define batch experiments.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired size distribution.

    Note: Usage of this class assumes homogeneous systems.

    Attributes:

        size_list: List of integer system sizes defining the range of the
                   variable for the batch experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path,
                 robot: str,
                 sizes: tp.List[int]) -> None:
        population_size.BasePopulationSize.__init__(self,
                                                    cli_arg,
                                                    main_config,
                                                    batch_input_root)
        self.sizes = sizes
        self.robot = robot
        self.logger = logging.getLogger(__name__)
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        """
        Generate XML modifications to set system sizes.
        """
        if not self.tag_adds:
            robot_config = self.main_config['ros']['robots'][self.robot]
            prefix = robot_config['prefix']

            for s in self.sizes:
                per_robot = xml.TagAddList()
                per_robot.append(xml.TagAdd(".",
                                            "master",
                                            {},
                                            True))
                per_robot.append(xml.TagAdd("./master",
                                            "group",
                                            {
                                                'ns': 'sierra'
                                            },
                                            False))
                per_robot.append(xml.TagAdd("./master/group/[@ns='sierra']",
                                            "param",
                                            {
                                                'name': 'experiment/n_robots',
                                                'value': str(s)
                                            },
                                            False))

                for i in range(0, s):

                    # Note that we don't try to do any of the robot bringup
                    # here--we can't know the exact node/package names without
                    # using a lot of (brittle) config.
                    ns = f'{prefix}{i}'
                    per_robot.append(xml.TagAdd("./robot",
                                                "group",
                                                {
                                                    'ns': ns
                                                },
                                                True))

                    per_robot.append(xml.TagAdd(f"./robot/group/[@ns='{ns}']",
                                                "param",
                                                {
                                                    "name": "tf_prefix",
                                                    "value": ns
                                                },
                                                True))

                self.tag_adds.append(per_robot)

        return self.tag_adds

    def gen_exp_names(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        adds = self.gen_tag_addlist()
        return ['exp' + str(x) for x in range(0, len(adds))]

    def n_robots(self, exp_num: int) -> int:
        return self.sizes[exp_num]


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            **kwargs) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition.

    """
    parser = population_size.Parser()
    attr = parser(cli_arg)
    max_sizes = parser.to_sizes(attr)

    def __init__(self) -> None:
        PopulationSize.__init__(self,
                                cli_arg,
                                main_config,
                                cmdopts['batch_input_root'],
                                cmdopts['robot'],
                                max_sizes)

    return type(cli_arg,  # type: ignore
                (PopulationSize,),
                {"__init__": __init__})


__api__ = [
    'PopulationSize'
]
