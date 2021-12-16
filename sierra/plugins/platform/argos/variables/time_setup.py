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
Classes for the ``--time-setup`` cmdline option. See
:ref:`ln-vars-ts` for usage documentation.
"""

# Core packages
import typing as tp
import re

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.xml import XMLAttrChangeSet, XMLAttrChange, XMLTagRmList, XMLTagAddList
from sierra.core import config
from sierra.core.variables.time_setup import Parser


@implements.implements(IBaseVariable)
class TimeSetup():
    """
    Defines the simulation duration.

    Attributes:
        duration: The simulation duration in seconds, NOT timesteps.
    """
    @staticmethod
    def extract_time_params(exp_def: XMLAttrChangeSet) -> tp.Dict[str, int]:
        """
        Extract and return the length (in seconds), ticks_per_second for the
        specified experiment.
        """
        ret = {
            'T_in_secs': int(),
            'n_ticks_per_sec': int()
        }

        for path, attr, value in exp_def:
            if 'experiment' in path:
                if 'length' in attr:
                    ret['T_in_secs'] = int(value)
                if 'ticks_per_second' in attr:
                    ret['n_ticks_per_sec'] = int(value)

        return ret

    def __init__(self,
                 n_secs_per_run: int,
                 n_datapoints: int,
                 n_ticks_per_sec: int) -> None:
        self.n_secs_per_run = n_secs_per_run
        self.n_datapoints = n_datapoints
        self.n_ticks_per_sec = n_ticks_per_sec
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        if not self.attr_changes:
            self.attr_changes = [XMLAttrChangeSet(XMLAttrChange(".//experiment",
                                                                "length",
                                                                "{0}".format(self.n_secs_per_run)),
                                                  XMLAttrChange(".//experiment",
                                                                "ticks_per_second",
                                                                "{0}".format(self.n_ticks_per_sec)),
                                                  )]
        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        return []

    def gen_files(self) -> None:
        pass


def factory(arg: str) -> TimeSetup:
    """
    Factory to create :class:`TimeSetup` derived classes from the command
    line definition.

    Arguments:

       arg: The value of ``--time-setup``.
    """
    parser = Parser({'n_secs_per_run': config.kARGoS['n_secs_per_run'],
                     'n_ticks_per_sec': config.kARGoS['n_ticks_per_sec'],
                     'n_datapoints': config.kExperimentalRunData['n_datapoints_1D']})
    attr = parser(arg)

    def __init__(self: TimeSetup) -> None:
        TimeSetup.__init__(self,
                           attr["n_secs_per_run"],
                           attr['n_datapoints'],
                           attr['n_ticks_per_sec'])

    return type(attr['pretty_name'],
                (TimeSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'TimeSetup',
]
