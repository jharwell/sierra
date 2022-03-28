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

# Core packages
import typing as tp
import re
import math

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.variables import batch_criteria as bc


class BasePopulationSize(bc.UnivarBatchCriteria):
    """
    Base class for changing the # agents/robots to reduce code duplication.
    """

    def __init__(self, *args, **kwargs) -> None:
        bc.UnivarBatchCriteria.__init__(self, *args, *kwargs)

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


class Parser():
    """A base parser for use in changing the # robots/agents.

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


__api__ = [
    'Parser',
    'PopulationSize'
]
