# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for the ``--exp-setup`` cmdline option.

See :ref:`ln-sierra-vars-expsetup` for usage documentation.

"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import xml
from sierra.core import config, types
from sierra.core.variables.exp_setup import Parser


@implements.implements(IBaseVariable)
class ExpSetup():
    """
    Defines the simulation duration.

    Attributes:

        duration: The simulation duration in seconds, NOT timesteps.
    """
    @staticmethod
    def extract_time_params(exp_def: xml.AttrChangeSet) -> types.IntDict:
        """
        Extract and return time parameters for the experiment.

        Returns:

            length (in seconds), ticks_per_second
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
        self.attr_changes = []  # type: tp.List[xml.AttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        if not self.attr_changes:
            chgs = xml.AttrChangeSet(xml.AttrChange(".//experiment",
                                                    "length",
                                                    "{0}".format(self.n_secs_per_run)),
                                     xml.AttrChange(".//experiment",
                                                    "ticks_per_second",
                                                    "{0}".format(self.n_ticks_per_sec)),
                                     )
            self.attr_changes = [chgs]
        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        return []

    def gen_files(self) -> None:
        pass


def factory(arg: str) -> ExpSetup:
    """Create an :class:`ExpSetup` derived class from the command line definition.

    Arguments:

       arg: The value of ``--exp-setup``.

    """
    parser = Parser({'n_secs_per_run': config.kARGoS['n_secs_per_run'],
                     'n_ticks_per_sec': config.kARGoS['n_ticks_per_sec'],
                     'n_datapoints': config.kExperimentalRunData['n_datapoints_1D']})
    attr = parser(arg)

    def __init__(self: ExpSetup) -> None:
        ExpSetup.__init__(self,
                          attr["n_secs_per_run"],
                          attr['n_datapoints'],
                          attr['n_ticks_per_sec'])

    return type(attr['pretty_name'],
                (ExpSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'ExpSetup',
]
