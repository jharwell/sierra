# Copyright 2018 John Harwell, All rights reserved.
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

# Core packages
import re
import typing as tp

# 3rd party packages

# Project packages
from sierra.core.variables.batch_criteria import UnivarBatchCriteria
from sierra.core.utils import ArenaExtent
from sierra.core.variables.arena_shape import ArenaShape
from sierra.core import types


class ConstantDensity(UnivarBatchCriteria):
    """
    A univariate range specifiying the density (ratio of SOMETHING to arena size) to hold constant
    as arena size is increased. This class is a base class which should NEVER be used on its
    own.

    Attributes:
        target_density: The target density.
        dimensions: List of (X,Y) dimensions to use (creates rectangular arenas).
        scenario_tag: A scenario tag (presumably part of `--scenario`) to use to generate scenario
                      names.
        changes: List of sets of changes to apply to generate the specified arena sizes.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_input_root: str,
                 target_density: float,
                 dimensions: tp.List[ArenaExtent],
                 scenario_tag: str) -> None:
        UnivarBatchCriteria.__init__(
            self, cli_arg, main_config, batch_input_root)
        self.target_density = target_density
        self.dimensions = dimensions
        self.scenario_tag = scenario_tag
        self.attr_changes = ArenaShape(dimensions).gen_attr_changelist()

    def exp_scenario_name(self, exp_num: int) -> str:
        """
        Given the exp number in the batch, compute a valid, parsable scenario name. It is necessary
        to query this criteria after generating the changelist in order to create generator classes
        for each experiment in the batch with the correct name and definition.

        Normally controller+scenario are used to look up all necessary changes for the specified
        arena size, but for this criteria the specified scenario is the base scenario (i.e., the
        starting arena dimensions), and the correct arena dimensions for a given exp must be found
        via lookup with THIS function).
        """
        dims = self.dimensions[exp_num]
        return self.scenario_tag + '.' + 'x'.join([str(dims.xsize()),
                                                   str(dims.ysize()),
                                                   str(dims.zsize())])


class Parser():
    """
    Enforces the cmdline definition of a :class:`ConstantDensity` derived batch
    criteria.
    """

    def __call__(self, cli_arg: str) -> types.CLIArgSpec:
        """
        Returns:
            Dictionary with keys:
                target_density: Floating point value of parsed target density
                arena_size_inc: Integer increment for arena size

        """
        ret = {}
        # Need to have 3 dot/4 parts
        assert len(cli_arg.split('.')) == 4,\
            "Bad criteria formatting in criteria '{0}': must have 4 sections, separated by '.'".format(
                cli_arg)

        # Parse density
        density = cli_arg.split('.')[1]
        res = re.search('[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density characteristic specification in criteria '{0}'".format(
                cli_arg)

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density mantissa specification in criteria '{0}'".format(
                cli_arg)
        mantissa = float("0." + res.group(0)[1:])

        ret['target_density'] = characteristic + mantissa

        # Parse arena size increment
        increment = cli_arg.split('.')[2]
        res = re.search('I[0-9]+', increment)
        assert res is not None, \
            "FATAL: Bad arena increment specification in criteria '{0}'".format(
                cli_arg)
        ret['arena_size_inc'] = int(res.group(0)[1:])

        # Parse cardinality
        increment = cli_arg.split('.')[3]
        res = re.search('C[0-9]+', increment)
        assert res is not None, \
            "FATAL: Bad cardinality specification in criteria '{0}'".format(
                cli_arg)

        ret['cardinality'] = int(res.group(0)[1:])

        return ret


__api__ = [
    'ConstantDensity'
]
