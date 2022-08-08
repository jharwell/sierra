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
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.utils import ArenaExtent
from sierra.plugins.platform.argos.variables.arena_shape import ArenaShape
from sierra.core import types


class ConstantDensity(bc.UnivarBatchCriteria):
    """Defines common functionality for all constant-density classes.

    Constant density = SOMETHING/arena size is held constant as arena size is
    increased. This class is a base class which should NEVER be used on its own.

    Attributes:

        target_density: The target density.

        dimensions: List of (X,Y) dimensions to use (creates rectangular
                    arenas).

        scenario_tag: A scenario tag (presumably part of `--scenario`) to use to
                      generate scenario names.

        changes: List of sets of changes to apply to generate the specified
                 arena sizes.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path,
                 target_density: float,
                 dimensions: tp.List[ArenaExtent],
                 scenario_tag: str) -> None:
        bc.UnivarBatchCriteria.__init__(self,
                                        cli_arg,
                                        main_config,
                                        batch_input_root)
        self.target_density = target_density
        self.dimensions = dimensions
        self.scenario_tag = scenario_tag
        self.attr_changes = ArenaShape(dimensions).gen_attr_changelist()

    def exp_scenario_name(self, exp_num: int) -> str:
        """Given the exp number in the batch, compute a parsable scenario name.

        It is necessary to query this criteria after generating the changelist
        in order to create generator classes for each experiment in the batch
        with the correct name and definition in some cases.

        Normally controller+scenario are used to look up all necessary changes
        for the specified arena size, but for this criteria the specified
        scenario is the base scenario (i.e., the starting arena dimensions), and
        the correct arena dimensions for a given exp must be found via lookup
        with THIS function).

        """
        dims = self.dimensions[exp_num]
        return self.scenario_tag + '.' + 'x'.join([str(dims.xsize()),
                                                   str(dims.ysize()),
                                                   str(dims.zsize())])


class Parser():
    """Enforces specification of a :class:`ConstantDensity` derived batch criteria.

    """

    def __call__(self, arg: str) -> types.CLIArgSpec:
        """
        Parse the cmdline argument.

        Returns:

            Dict:
                target_density: Floating point value of parsed target density
                arena_size_inc: Integer increment for arena size

        """
        ret = {}

        sections = arg.split('.')
        # remove variable name, leaving only the spec
        sections = sections[1:]

        # Need to have 2 dot/3 parts
        assert len(sections) == 3, \
            (f"Spec must have 3 sections separated by '.'; have "
             f"{len(sections)} sections from '{arg}'")

        # Parse density
        res = re.search('[0-9]+', sections[0])
        assert res is not None, \
            f"Bad density characteristic spec in section '{sections[0]}'"

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', sections[0])
        assert res is not None, \
            f"Bad density mantissa spec in section '{sections[0]}'"
        mantissa = float("0." + res.group(0)[1:])

        ret['target_density'] = characteristic + mantissa

        # Parse arena size increment
        res = re.search('I[0-9]+', sections[1])
        assert res is not None, \
            f"Bad arena increment spec in section '{sections[1]}'"
        ret['arena_size_inc'] = int(res.group(0)[1:])

        # Parse cardinality
        res = re.search('C[0-9]+', sections[2])
        assert res is not None, \
            f"Bad cardinality spec in section '{sections[2]}'"

        ret['cardinality'] = int(res.group(0)[1:])

        return ret


__api__ = [
    'ConstantDensity'
]
