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

# 3rd party packages

# Project packages
from sierra.core.variables.batch_criteria import UnivarBatchCriteria
from sierra.core.utils import ArenaExtent
from sierra.core.xml import XMLAttrChangeSet
from sierra.core import types


class VariableDensity(UnivarBatchCriteria):
    """A univariate range specifiying the density (ratio of SOMETHING to arena
    size) to vary as arena size is held constant. This class is a base class
    which should NEVER be used on its own.

    Attributes:
        densities: List of densities to use.

        dist_type: The type of block distribution to use.

        changes: List of sets of changes to apply to generate the specified
                 arena sizes.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_input_root: str,
                 densities: tp.List[float],
                 extent: ArenaExtent) -> None:
        UnivarBatchCriteria.__init__(
            self, cli_arg, main_config, batch_input_root)
        self.densities = densities
        self.extent = extent
        self.attr_changes = []


class Parser():
    """
    Enforces the cmdline definition of a :class:`VariableDensity` derived batch
    criteria.
    """

    def __call__(self, cli_arg: str) -> types.CLIArgSpec:
        """
        Returns:
            Dictionary with keys:
                density_min: Floating point value of target minimum density.
                density_max: Floating point value of target maximum density.
                cardinality: # densities in [min,max] that should be created.

        """
        ret = {}
        # Need to have 3 dot/4 parts
        assert len(cli_arg.split('.')) == 4,\
            "Bad criteria formatting in criteria '{0}': must have 4 sections, separated by '.'".format(
                cli_arg)

        # Parse density min
        chunk = cli_arg.split('.')[1]
        ret['density_min'] = self._parse_density(chunk, 'minimum')

        # Parse density pmax
        chunk = cli_arg.split('.')[2]
        ret['density_max'] = self._parse_density(chunk, 'maximum')

        # Parse cardinality
        cardinality = cli_arg.split('.')[3]
        res = re.search('C[0-9]+', cardinality)
        assert res is not None, \
            "Bad cardinality specification in criteria '{0}'".format(
                cli_arg)

        ret['cardinality'] = int(res.group(0)[1:])

        return ret

    @staticmethod
    def _parse_density(chunk: str, which: str) -> float:
        res = re.search('[0-9]+', chunk)
        assert res is not None, \
            "Bad {0} density characteristic specification in criteria '{1}'".format(
                which,
                chunk)

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', chunk)
        assert res is not None, \
            "Bad {0} density mantissa specification in criteria '{1}'".format(
                which,
                chunk)

        mantissa = float("0." + res.group(0)[1:])

        return characteristic + mantissa


__api__ = [
    'VariableDensity'
]
