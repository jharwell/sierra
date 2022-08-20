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
"""
Reusable classes related to the homogeneous populations of agents.
"""
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
            return r"$\log$(System Size)"

        return "System Size"


class Parser():
    """A base parser for use in changing the # robots/agents.

    """

    def __call__(self, arg: str) -> types.CLIArgSpec:
        ret = {
            'max_size': int(),
            'model': str(),
            'cardinality': None
        }  # type: tp.Dict[str, tp.Union[str, tp.Optional[int]]]

        sections = arg.split('.')

        # remove batch criteria variable name, leaving only the spec
        sections = sections[1:]
        assert len(sections) >= 1 and len(sections) <= 2,\
            ("Spec must have 1 or 2 sections separated by '.'; "
             f"have {len(sections)} from '{arg}'")

        # Parse increment type
        res = re.search("Log|Linear", sections[0])
        assert res is not None, \
            f"Bad size increment spec in criteria section '{sections[0]}'"
        ret['model'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", sections[0])
        assert res is not None, \
            "Bad population max in criteria section '{sections[0]}'"
        max_size = int(res.group(0))
        ret['max_size'] = max_size

        # Parse cardinality for linear models
        if ret['model'] == 'Linear':
            if len(sections) == 2:
                res = re.search("C[0-9]+", sections[1])
                assert res is not None, \
                    "Bad cardinality in criteria section '{sections[1]}'"
                ret['cardinality'] = int(res.group(0)[1:])
            else:
                ret['cardinality'] = int(ret['max_size'] / 10.0)   # type: ignore
        elif ret['model'] == 'Log':
            ret['cardinality'] = len(range(0, int(math.log2(max_size)) + 1))

        return ret

    def to_sizes(self, attr: types.CLIArgSpec) -> tp.List[int]:
        """
        Generate the system sizes for each experiment in a batch.
        """
        if attr["model"] == 'Linear':
            increment = int(attr['max_size'] / attr['cardinality'])
            return [increment * x for x in range(1, attr['cardinality'] + 1)]
        elif attr["model"] == 'Log':
            return [int(2 ** x) for x in range(0, attr['cardinality'])]
        else:
            raise AssertionError


__api__ = [
    'BasePopulationSize',
    'Parser',
]
