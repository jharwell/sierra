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
"""
Classes for the population size batch criteria. See
:ref:`ln-platform-rosgazebo-bc-population-size` for usage documentation.
"""

# Core packages
import typing as tp
import re
import math
import random
import logging  # type: tp.Any

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.xml import XMLTagAdd, XMLTagAddList
from sierra.core import types
from sierra.core.vector import Vector3D
from sierra.core.utils import ArenaExtent
import sierra.core.plugin_manager as pm


@implements.implements(bc.IConcreteBatchCriteria)
class PopulationSize(bc.UnivarBatchCriteria):
    """
    A univariate range of system sizes used to define batch experiments. This
    class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired size distribution.

    Note: Usage of this class assumes homogeneous systems.

    Attributes:
        size_list: List of integer system sizes defining the range of the
                   variable for the batch experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_input_root: str,
                 robot: str,
                 sizes: tp.List[float],
                 positions: tp.List[float]) -> None:
        bc.UnivarBatchCriteria.__init__(self,
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
        self.tag_adds = []  # type: tp.List[XMLTagAddList]

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        """
        Generate list of sets of changes for system sizes to define a batch
        experiment.
        """
        if not self.tag_adds:
            robot_config = self.main_config['rosgazebo']['robots'][self.robot]
            prefix = robot_config['prefix']
            model_base = robot_config['model']
            model_variant = robot_config.get('model_variant', '')

            if model_variant != '':
                model = f"{model_base}_{model_variant}"
            else:
                model = model_base

            desc_cmd = f"$(find xacro)/xacro $(find {model_base}_description)/urdf/{model}.urdf.xacro"

            for s in self.sizes:
                exp_adds = XMLTagAddList()
                pos_i = random.randint(0, len(self.positions) - 1)
                for i in range(0, s):

                    ns = f'{prefix}{i}'
                    pos = self.positions[pos_i]
                    pos_i = (pos_i + 1) % len(self.positions)
                    spawn_cmd_args = f"-urdf -model {model}_{ns} -x {pos.x} -y {pos.y} -z {pos.z} -param robot_description"

                    exp_adds.append(XMLTagAdd(".//launch",
                                              "group",
                                              {'ns': ns}))

                    exp_adds.append(XMLTagAdd(f".//launch/group/[@ns='{ns}']",
                                              "param",
                                              {"name": "robot_description",
                                               "command": desc_cmd}))

                    exp_adds.append(XMLTagAdd(f".//launch/group/[@ns='{ns}']",
                                              "node",
                                              {"name": "spawn_urdf",
                                               "pkg": "gazebo_ros",
                                               "type": "spawn_model",
                                               "args": spawn_cmd_args}))

                    exp_adds.append(XMLTagAdd(f".//launch/group/[@ns='{ns}']",
                                              "param",
                                              {"name": "tf_prefix",
                                               "value": ns}))

                self.tag_adds.append(exp_adds)

        return self.tag_adds

    def gen_exp_dirnames(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        adds = self.gen_tag_addlist()
        return ['exp' + str(x) for x in range(0, len(adds))]

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
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
                          cmdopts: types.Cmdopts,
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ret = map(float, self.populations(cmdopts, exp_dirs))

        return list(map(lambda x: str(int(round(x, 4))), ret))

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        if cmdopts['plot_log_xscale']:
            return r"$\log$(System Size)"

        return "System Size"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']

    def n_robots(self, exp_num: int) -> int:
        return int(len(self.tag_adds[exp_num]) / len(self.tag_adds[0]))


class Parser():
    """
    Enforces the cmdline definition of the :class:`PopulationSize` batch
    criteria defined in :ref:`ln-platform-rosgazebo-bc-population-size`.

    """

    def __call__(self, criteria_str: str) -> types.CLIArgSpec:
        ret = {
            'max_size': int(),
            'increment_type': str(),
            'linear_increment': None,
        }  # type: tp.Dict[str, tp.Union[int, str, None]]

        sections = criteria_str.split('.')
        assert len(sections) == 2,\
            "Cmdline spec must have 2 sections separated by '.'"

        # Parse increment type
        res = re.search("Log|Linear", sections[1])
        assert res is not None, \
            f"Bad size increment spec in criteria section '{sections[2]}'"
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", sections[1])
        assert res is not None, \
            "Bad population max in criteria section '{sections[2]}'"
        ret['max_size'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(
                ret['max_size'] / 10.0)  # type: ignore

        return ret

    def to_sizes(self, attr: types.CLIArgSpec) -> tp.List[float]:
        """
        Generates the swarm sizes for each experiment in a batch.
        """
        if attr["increment_type"] == 'Linear':
            return [attr["linear_increment"] * x for x in range(1, 11)]
        elif attr["increment_type"] == 'Log':
            return [2 ** x for x in range(0, int(math.log2(attr["max_size"])) + 1)]
        else:
            assert False


def factory(cli_arg: str,
            main_config: types.YAMLDict,
            cmdopts: types.Cmdopts) -> PopulationSize:
    """
    Factory to create :class:`PopulationSize` derived classes from the command
    line definition.

    """
    parser = Parser()
    attr = parser(cli_arg)
    max_sizes = parser.to_sizes(attr)

    if cmdopts['robot_positions']:
        positions = [Vector3D.from_str(s,
                                       astype=float) for s in cmdopts['robot_positions']]
    else:
        # Get the dimensions of the effective arena from the scenario so we can
        # place robots randomly within it.
        sgp = pm.module_load_tiered(project=cmdopts['project'],
                                    path='generators.scenario_generator_parser')
        kw = sgp.ScenarioGeneratorParser().to_dict(cmdopts['scenario'])
        xs = random.choices(range(0, kw['arena_x']), k=max_sizes[-1])
        ys = random.choices(range(0, kw['arena_y']), k=max_sizes[-1])
        zs = random.choices(range(0, kw['arena_z']), k=max_sizes[-1])
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
    'PopulationSize',
    'Parser'
]
