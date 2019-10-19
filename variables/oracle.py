# Copyright 2019 John Harwell, All rights reserved.
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

"""
Definition:
    {oracle_name}[.Z{swarm_size}]

    oracle_name = {entities, tasks}
    swarm_size = Size of the swarm to use (optional)

Examples:
    - ``entities.Z16``: All permutations of oracular information about entities in the arena, run with
      swarms of size 16.
    - ``tasks.Z8``: All permutations of oracular information about tasks in the arena, run with swarms
      of size 8.
    - ``entities``: All permuntations of oracular information of entities in the arena (swarm size is
      not modified).
    """


import typing as tp
import re
from variables.batch_criteria import UnivarBatchCriteria
import itertools
from variables.swarm_size import SwarmSize


class Oracle(UnivarBatchCriteria):
    """
    A univariate range specifiying the types of oracular information to disseminate to the swarm
    during simulation. This class is a base class which should (almost) never be used on its
    own. Instead, the ``Factory()`` function should be used to dynamically create derived classes
    expressing the user's desired types to disseminate.

    Attributes:
        tuples: List of tuples of types of oracular information to enable for a specific.
        simulation. Each tuple is (oracle name, list(tuple(oracle feature name, oracle
        feature value))).
        swarm_size: Swarm size to set for the swarm (can be ``None``).
    """
    kInfoTypes = {'entities': ['caches', 'blocks']}

    def __init__(self, cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 tuples: tp.List[tuple],
                 swarm_size: int):
        UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)

        self.tuples = tuples
        self.swarm_size = swarm_size

    def gen_attr_changelist(self) -> list:
        # Swarm size is optional. It can be (1) controlled via this variable, (2) controlled by
        # another variable in a bivariate batch criteria, (3) not controlled at all. For (2), (3),
        # the swarm size can be None.
        changes = [set([(".//oracle_manager/{0}".format(str(t[0])),
                         "{0}".format(str(feat[0])),
                         "{0}".format(str(feat[1]))) for feat in t[1]]) for t in self.tuples]

        if self.swarm_size is not None:
            size_attr = [next(iter(SwarmSize([self.swarm_size]).gen_attr_changelist()[0]))]
            for c in changes:
                c.add(size_attr)

        return changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str], always_named: bool = False) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        attr = OracleParser().parse(self.cli_arg)
        dirs = []

        for chg in changes:
            d = ''
            for t in Oracle.kInfoTypes[attr['oracle_type']]:
                for path, at, value in chg:
                    if t in at:
                        d += '|' * ('' != d) + t + '=' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs'] and not always_named:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def sc_graph_labels(self, scenarios: str) -> tp.List[str]:
        return scenarios

    def sc_sort_scenarios(self, scenarios: str) -> tp.List[str]:
        return scenarios  # No sorting needed

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: tp.List[str]) -> str:
        return [d for d in self.gen_exp_dirnames(cmdopts, True)]

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: tp.List[str] = None) -> tp.List[float]:
        raise NotImplementedError

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Oracular Information Type"

    def pm_query(self, query: str) -> bool:
        return query in ['blocks-collected']


class OracleParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def parse(self, criteria_str: str) -> dict:
        """
        Returns:
            Dictionary with keys:
                oracle_type: entities|tasking
                oracle_name: entities_oracle|tasking_oracle
                swarm_size: Size of swarm to use (optional)

        """
        ret = {}

        # Parse oracle name
        if 'entities' in criteria_str:
            ret['oracle_type'] = 'entities'
            ret['oracle_name'] = 'entities_oracle'
        elif 'tasking' in criteria_str:
            ret['oracle_type'] = 'tasking'
            ret['oracle_name'] = 'tasking_oracle'

        # Parse swarm size
        res = re.search("\.Z[0-9]+", criteria_str)
        if res is not None:
            ret['swarm_size'] = int(res.group(0)[2:])
        return ret


def Factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            batch_generation_root: str,
            **kwargs):
    """
    Factory to create ``Oracle`` derived classes from the command line definition of batch
    criteria.

    """
    attr = OracleParser().parse(cli_arg)

    def gen_tuples(cli_arg):

        if 'entities' in attr['oracle_name']:
            tuples = []
            for val in list(itertools.product([False, True], repeat=len(Oracle.kInfoTypes['entities']))):
                tuples.append((attr['oracle_name'],
                               [(Oracle.kInfoTypes['entities'][i], str(val[i]).lower())
                                   for i in range(0, len(Oracle.kInfoTypes['entities']))]
                               ))

            return tuples

    def __init__(self):
        Oracle.__init__(self, cli_arg, main_config, batch_generation_root,
                        gen_tuples(cli_arg), attr.get('swarm_size', None))

    return type(cli_arg,
                (Oracle,),
                {"__init__": __init__})
