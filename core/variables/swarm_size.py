# Copyright 2018 John Harwell, All rights reserved.
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
Definition:
    {increment_type}{max_size}

    - increment_type = {Log,Linear}
    - max_size = Integer

Examples:
    - ``Log1024``: Swarm sizes 1...1024 by powers of 2
    - ``Linear1000``: Swarm sizes 10...1000, step size of 100

"""

import typing as tp
import re
import math

from core.variables import batch_criteria as bc


class SwarmSize(bc.UnivarBatchCriteria):
    """
    A univariate range of swarm sizes to use to define batched experiments. This class is a base
    class which should (almost) never be used on its own. Instead, the ``factory()`` function should
    be used to dynamically create derived classes expressing the user's desired size distribution.

    Attributes:
        size_list: List of integer swarm sizes defining the range of the variable for the batched
                   experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 size_list: tp.List[str]):
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
        self.size_list = size_list

    def gen_attr_changelist(self) -> list:
        """Generate list of sets of swarm sizes. Each entry in the list is a set of changes necessary to
        make to the input file to correctly set up the simulation with the specified swarm size.

        """
        return [set([(".//arena/distribute/entity", "quantity", str(s))]) for s in self.size_list]

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> list:
        changes = self.gen_attr_changelist()
        dirs = []
        for chg in changes:
            d = ''
            for path, attr, value in chg:

                if 'quantity' in attr:
                    d += 'size' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs']:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def sc_graph_labels(self, scenarios: list) -> tp.List[str]:
        return [s[-4:] for s in scenarios]

    def sc_sort_scenarios(self, scenarios: list) -> tp.List[str]:
        return scenarios  # No sorting needed

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        ret = self.swarm_sizes(cmdopts, exp_dirs)

        if cmdopts['plot_log_xaxis']:
            return [math.log2(x) for x in ret]
        else:
            return ret

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        return self.graph_xticks(cmdopts, exp_dirs)

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Swarm Size"

    def pm_query(self, query: str) -> bool:
        return query in ['blocks-collected', 'scalability', 'self-org']


class SwarmSizeParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def parse(self, criteria_str) -> dict:
        """
        Returns:
            Dictionary with keys:
                increment_type: Log|Linear
                max_size: Integer maximum swarm size
                linear_increment: Integer linear increment; only present if `increment_type=Linear`

        """
        ret = {}

        # Parse increment type
        res = re.search("^Log|Linear", criteria_str)
        assert res is not None, \
            "FATAL: Bad swarm size increment type in criteria '{0}'".format(criteria_str)
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad swarm size max in criteria '{0}'".format(criteria_str)
        ret['max_size'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(ret['max_size'] / 10.0)

        return ret


def factory(cli_arg: str, main_config: tp.Dict[str, str], batch_generation_root: str, **kwargs):
    """
    factory to create ``SwarmSize`` derived classes from the command line definition of batch
    criteria.

    """
    attr = SwarmSizeParser().parse(cli_arg.split(".")[1])

    def gen_sizes(cli_arg):

        if attr["increment_type"] == "Linear":
            return [attr["linear_increment"] * x for x in range(1, 11)]
        elif attr["increment_type"] == "Log":
            return [2 ** x for x in range(0, int(math.log2(attr["max_size"])) + 1)]

    def __init__(self):
        SwarmSize.__init__(self,
                           cli_arg,
                           main_config,
                           batch_generation_root,
                           gen_sizes(cli_arg))

    return type(cli_arg,
                (SwarmSize,),
                {"__init__": __init__})
