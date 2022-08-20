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
#

# Core packages
import re
import typing as tp
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables.batch_criteria import UnivarBatchCriteria
from sierra.core.utils import ArenaExtent
from sierra.core import types
from sierra.core.experiment import xml


class VariableDensity(UnivarBatchCriteria):
    """A univariate range for variable density (# THINGS/m^2).

    # THINGS is varied as arena size is held constant. This class is a base
    class which should NEVER be used on its own.

    Attributes:

        densities: List of densities to use.

        dist_type: The type of block distribution to use.

        changes: List of sets of changes to apply to generate the specified
                 arena sizes.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path,
                 densities: tp.List[float],
                 extent: ArenaExtent) -> None:
        UnivarBatchCriteria.__init__(
            self, cli_arg, main_config, batch_input_root)
        self.densities = densities
        self.extent = extent
        self.attr_changes = []  # type: tp.List[xml.AttrChangeSet]


class Parser():
    """Enforces specification of a :class:`VariableDensity` derived batch criteria.

    """

    def __call__(self, arg: str) -> types.CLIArgSpec:
        """
        Parse the cmdline argument.

        Returns:

            dict:
                density_min: Floating point value of target minimum density.
                density_max: Floating point value of target maximum density.
                cardinality: # densities in [min,max] that should be created.

        """
        ret = {}
        sections = arg.split('.')

        # remove batch criteria variable name, leaving only the spec
        sections = sections[1:]
        assert len(sections) == 3,\
            ("Spec must have 3 sections separated by '.'; "
             f"have {len(sections)} from '{arg}'")

        # Parse density min
        ret['density_min'] = self._parse_density(sections[0], 'minimum')

        # Parse density pmax
        ret['density_max'] = self._parse_density(sections[1], 'maximum')

        # Parse cardinality
        res = re.search('C[0-9]+', sections[2])
        assert res is not None, \
            "Bad cardinality specification in '{sections[2]}'"

        ret['cardinality'] = int(res.group(0)[1:])

        return ret

    @staticmethod
    def _parse_density(chunk: str, which: str) -> float:
        res = re.search('[0-9]+', chunk)
        assert res is not None, \
            f"Bad {which} density characteristic specification in '{chunk}'"

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', chunk)
        assert res is not None, \
            f"Bad {which} density mantissa specification in '{chunk}'"

        mantissa = float("0." + res.group(0)[1:])

        return characteristic + mantissa


__api__ = [
    'VariableDensity',
    'Parser'

]
