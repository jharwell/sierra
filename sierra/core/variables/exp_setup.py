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
"""Reusable classes for configuring general aspects of experiments.

Aspects include experiment length, controller frequency, etc.

"""
# Core packages
import re

# 3rd party packages

# Project packages
from sierra.core import types


class Parser():
    """Enforces the cmdline definition of ``--exp-setup``.

    See :ref:`ln-sierra-vars-expsetup` for documentation.

    """

    def __init__(self, dflts: types.SimpleDict):
        self.dflts = dflts

    def __call__(self, arg: str) -> types.CLIArgSpec:
        ret = self.dflts

        sections = arg.split('.')
        # remove variable name, leaving only the spec
        sections = sections[1:]

        assert len(sections) >= 1 and len(sections) <= 3,\
            ("Spec must have between 1 and 3 sections separated by '.'; "
             f"have {len(sections)} from '{arg}'")

        # Get pretty name for logging
        ret['pretty_name'] = '.'.join(sections)

        # Parse duration, which must be present
        res = re.search(r"T\d+", sections[0])
        assert res is not None, \
            f"Bad duration spec in section '{sections[0]}'"
        ret['n_secs_per_run'] = int(res.group(0)[1:])

        # Parse # ticks per second for controllers, which can be absent
        if len(sections) >= 2:
            res = re.search(r"K\d+", sections[1])
            assert res is not None, \
                f"Bad ticks per second spec in section '{sections[1]}'"
            ret['n_ticks_per_sec'] = int(res.group(0)[1:])

        # Parse # datapoints to capture, which can be absent
        if len(sections) == 3:
            res = re.search(r"N\d+", sections[2])
            assert res is not None, \
                f"Bad # datapoints spec in section '{sections[2]}'"
            ret['n_datapoints'] = int(res.group(0)[1:])

        return ret


__api__ = [
    'Parser'


]
