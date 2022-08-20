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

See :ref:`ln-sierra-platform-ros1gazebo-bc-population-size` for usage
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
from sierra.core.experiment import xml
from sierra.core import types, utils
from sierra.core.vector import Vector3D
from sierra.core.variables import population_size


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
                 sizes: tp.List[int],
                 positions: tp.List[Vector3D]) -> None:
        population_size.BasePopulationSize.__init__(self,
                                                    cli_arg,
                                                    main_config,
                                                    batch_input_root)
        self.sizes = sizes
        self.robot = robot
        self.positions = positions
        self.logger = logging.getLogger(__name__)
        if len(positions) < self.sizes[-1]:
            self.logger.warning("# possible positions < # robots: %s < %s",
                                len(positions),
                                self.sizes[-1])
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        """Generate XML modifications to set system sizes.

        """
        if not self.tag_adds:
            robot_config = self.main_config['ros']['robots'][self.robot]
            prefix = robot_config['prefix']
            model_base = robot_config['model']
            model_variant = robot_config.get('model_variant', '')

            if model_variant != '':
                model = f"{model_base}_{model_variant}"
            else:
                model = model_base

            desc_cmd = f"$(find xacro)/xacro $(find {model_base}_description)/urdf/{model}.urdf.xacro"
            for s in self.sizes:
                exp_adds = xml.TagAddList()
                pos_i = random.randint(0, len(self.positions) - 1)

                exp_adds.append(xml.TagAdd(".",
                                           "master",
                                           {},
                                           True))
                exp_adds.append(xml.TagAdd("./master",
                                           "group",
                                           {
                                               'ns': 'sierra'
                                           },
                                           False))
                exp_adds.append(xml.TagAdd("./master/group/[@ns='sierra']",
                                           "param",
                                           {
                                               'name': 'experiment/n_robots',
                                               'value': str(s)
                                           },
                                           False))

                for i in range(0, s):

                    ns = f'{prefix}{i}'
                    pos = self.positions[pos_i]
                    pos_i = (pos_i + 1) % len(self.positions)
                    spawn_cmd_args = f"-urdf -model {model}_{ns} -x {pos.x} -y {pos.y} -z {pos.z} -param robot_description"

                    exp_adds.append(xml.TagAdd("./robot",
                                               "group",
                                               {
                                                   'ns': ns
                                               },
                                               True))

                    exp_adds.append(xml.TagAdd(f"./robot/group/[@ns='{ns}']",
                                               "param",
                                               {
                                                   "name": "tf_prefix",
                                                   "value": ns
                                               },
                                               True))

                    # These two tag adds are OK to use because:
                    #
                    # - All robots in Gazebo are created using spawn_model
                    #   initially.
                    #
                    # - All robots in Gazebo will provide a robot description
                    #   .urdf.xacro per ROS naming conventions
                    exp_adds.append(xml.TagAdd(f"./robot/group/[@ns='{ns}']",
                                               "param",
                                               {
                                                   "name": "robot_description",
                                                   "command": desc_cmd
                                               },
                                               True))

                    exp_adds.append(xml.TagAdd(f"./robot/group/[@ns='{ns}']",
                                               "node",
                                               {
                                                   "name": "spawn_urdf",
                                                   "pkg": "gazebo_ros",
                                                   "type": "spawn_model",
                                                   "args": spawn_cmd_args
                                               },
                                               True))

                self.tag_adds.append(exp_adds)

        return self.tag_adds

    def gen_exp_names(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        adds = self.gen_tag_addlist()
        return ['exp' + str(x) for x in range(0, len(adds))]

    def n_robots(self, exp_num: int) -> int:
        return int(len(self.tag_adds[exp_num]) / len(self.tag_adds[0]))


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            **kwargs) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition.

    """
    parser = population_size.Parser()
    attr = parser(cli_arg)
    max_sizes = parser.to_sizes(attr)

    if cmdopts['robot_positions']:
        positions = [Vector3D.from_str(s,
                                       astype=float) for s in cmdopts['robot_positions']]
    else:
        # Get the dimensions of the effective arena from the scenario so we can
        # place robots randomly within it.
        kw = utils.gen_scenario_spec(cmdopts, **kwargs)

        xs = random.choices(range(0, kw['arena_x']), k=max_sizes[-1])  # type: ignore
        ys = random.choices(range(0, kw['arena_y']), k=max_sizes[-1])  # type: ignore
        zs = random.choices(range(0, kw['arena_z']), k=max_sizes[-1])  # type: ignore
        positions = [Vector3D(x, y, z) for x, y, z in zip(xs, ys, zs)]

    def __init__(self) -> None:
        PopulationSize.__init__(self,
                                cli_arg,
                                main_config,
                                cmdopts['batch_input_root'],
                                cmdopts['robot'],
                                max_sizes,
                                positions)

    return type(cli_arg,  # type: ignore
                (PopulationSize,),
                {"__init__": __init__})


__api__ = [
    'PopulationSize'
]
