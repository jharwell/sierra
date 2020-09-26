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
Classes for the population size batch criteria. See :ref:`ln-bc-population-size` for usage
documentation.
"""

import typing as tp
import re
import math
import implements

from core.variables import batch_criteria as bc


@implements.implements(bc.IConcreteBatchCriteria)
class PopulationSize(bc.UnivarBatchCriteria):
    """
    A univariate range of swarm sizes used to define batched
    experiments. This class is a base class which should (almost) never be used on its own. Instead,
    the ``factory()`` function should be used to dynamically create derived classes expressing the
    user's desired size distribution.

    Attributes:
        size_list: List of integer swarm sizes defining the range of the variable for the batched
                   experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 size_list: tp.List[int]) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
        self.size_list = size_list
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes for swarm sizes to define a batch experiment.

        Note that we also modify the maximum size allowed by population dynamics, even though that
        is not the active variable here, because this is the best place to do it, even if it is not
        the greatest logical fit. We give it a value of 4N, where N is the initial quantity of
        robots for the simulation, in order to provide buffer so that the queueing theoretic
        predictions of long-run population size are accurate.
        """
        if not self.attr_changes:
            self.attr_changes = PopulationSize.gen_attr_changelist_from_list(self.size_list)
        return self.attr_changes

    def gen_exp_dirnames(self, cmdopts: dict) -> list:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ret = list(map(float, self.populations(cmdopts, exp_dirs)))
        if cmdopts['plot_log_xaxis']:
            return [int(math.log2(x)) for x in ret]
        else:
            return ret

    def graph_xticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        return list(map(str, self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: dict) -> str:
        if cmdopts['plot_log_xaxis']:
            return r"$\log_{2}$(Swarm Size)"

        return "Swarm Size"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        return False

    @staticmethod
    def gen_attr_changelist_from_list(size_list: list):
        return [set([(".//arena/distribute/entity", "quantity", str(s)),
                     (".//population_dynamics", "max_size", str(4 * s))]) for s in size_list]


class PopulationSizeParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def __call__(self, criteria_str) -> dict:
        ret = {}

        # Parse increment type
        res = re.search("Log|Linear", criteria_str)
        assert res is not None, \
            "FATAL: Bad size increment specification in criteria '{0}'".format(criteria_str)
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad population max in criteria '{0}'".format(criteria_str)
        ret['max_size'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(ret['max_size'] / 10.0)

        return ret


def factory(cli_arg: str, main_config: tp.Dict[str, str], batch_generation_root: str, **kwargs):
    """
    Factory to create ``PopulationSize`` derived classes from the command line definition.

    """
    attr = PopulationSizeParser()(cli_arg)

    def gen_max_sizes():
        """
        Generates the maximum swarm sizes for each experiment in a batch.
        """
        if attr["increment_type"] == 'Linear':
            return [attr["linear_increment"] * x for x in range(1, 11)]
        elif attr["increment_type"] == 'Log':
            return [2 ** x for x in range(0, int(math.log2(attr["max_size"])) + 1)]
        else:
            return None

    def __init__(self) -> None:
        PopulationSize.__init__(self,
                                cli_arg,
                                main_config,
                                batch_generation_root,
                                gen_max_sizes())

    return type(cli_arg,
                (PopulationSize,),
                {"__init__": __init__})


__api__ = [
    'PopulationSize'
]
