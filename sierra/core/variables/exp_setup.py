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

# 3rd party packages

# Project packages
from sierra.core import types


class Parser():
    """Enforces the cmdline definition of ``--exp-setup``. See
    :ref:`ln-vars-expsetup` for documentation.

    """

    def __init__(self, dflts: tp.Dict[str, int]):
        self.dflts = dflts

    def __call__(self, arg: str) -> types.CLIArgSpec:
        ret = self.dflts

        # Get pretty name for logging
        ret['pretty_name'] = '.'.join(arg.split(".")[1:])

        # Sanity checks
        sections = arg.split('.')
        assert len(sections) >= 2 and len(sections) <= 4,\
            "Must have between 2 and 4 sections, separated by '.'"

        # Parse duration, which must be present
        res = re.search(r"T\d+", sections[1])
        assert res is not None, \
            "Bad duration spec in section '{0}'".format(sections[1])
        ret['n_secs_per_run'] = int(res.group(0)[1:])

        # Parse # ticks per second for controllers, which can be absent
        res = re.search(r"K\d+", arg)
        if res is not None:
            ret['n_ticks_per_sec'] = int(res.group(0)[1:])

        # Parse # datapoints to capture, which can be absent
        res = re.search(r"N\d+", arg)
        if res is not None:
            ret['n_datapoints'] = int(res.group(0)[1:])

        return ret
