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

"""Classes for the ``--exp-setup`` cmdline option for ROS1 platforms.

See :ref:`ln-sierra-vars-expsetup` for usage documentation.

"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import xml
from sierra.core import config
from sierra.core.variables.exp_setup import Parser


@implements.implements(IBaseVariable)
class ExpSetup():
    """
    Defines the experimental setup for ROS experiments.

    Attributes:

        n_secs_per_run: The :term:`Experimental Run` duration in seconds, NOT
                        :term:`Ticks <Tick>` or timesteps.

        n_datapoints: How many datapoints to capture during the experimental
                      run.

        n_ticks_per_sec: How many times per second robot controllers will be
                         run.

    """

    def __init__(self,
                 n_secs_per_run: int,
                 n_datapoints: int,
                 n_ticks_per_sec: int,
                 barrier_start: bool,
                 robots_need_timekeeper: bool) -> None:
        self.n_secs_per_run = n_secs_per_run
        self.n_datapoints = n_datapoints
        self.n_ticks_per_sec = n_ticks_per_sec
        self.barrier_start = barrier_start
        self.robots_need_timekeeper = robots_need_timekeeper

        self.tag_adds = None

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        return []

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        if not self.tag_adds:
            adds = xml.TagAddList(
                xml.TagAdd("./master/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/length",
                               "value": str(self.n_secs_per_run),
                           },
                           True),
                xml.TagAdd("./master/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/ticks_per_sec",
                               "value": str(self.n_ticks_per_sec),
                           },
                           True),
                xml.TagAdd("./master/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/barrier_start",
                               "value": str(self.barrier_start).lower(),
                           },
                           True),
                xml.TagAdd("./master/group/[@ns='sierra']",
                           "node",
                           {
                               "name": "sierra_timekeeper",
                               "pkg": "sierra_rosbridge",
                               "type": "sierra_timekeeper.py",
                               "required": "true",
                               # Otherwise rospy prints nothing
                               "output": "screen"
                           },
                           True),

                xml.TagAdd("./robot/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/length",
                               "value": str(self.n_secs_per_run),
                           },
                           True),
                xml.TagAdd("./robot/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/ticks_per_sec",
                               "value": str(self.n_ticks_per_sec),
                           },
                           True),
                xml.TagAdd("./robot/group/[@ns='sierra']",
                           "param",
                           {
                               "name": "experiment/barrier_start",
                               "value": str(self.barrier_start).lower()
                           },
                           True)
            )
            if self.robots_need_timekeeper:
                # Robots also need the timekeeper when they are real and not
                # simulated robots. With simulated robots, robots share the root
                # ROS namespace with the master, so duplicating the timekeeper
                # in that case causes an error.
                #
                # Because real robot nodes are launch in a separate roslaunch
                # than the master node (potentially), and that node exiting will
                # not cause all robots to exit. This is needed even if robot
                # nodes respect the set experiment time, because they might be
                # using ROS packages which launch nodes which DON'T respect the
                # set experiment time and will stay active until you kill
                # them. This can cause issues if a robot node expects that at
                # most 1 dependent node will be active at a given time. Plus,
                # it's just sloppy to leave that sort of thing hanging around
                # after a run exits.
                adds.append(xml.TagAdd("./robot/group/[@ns='sierra']",
                                       "node",
                                       {
                                           "name": "sierra_timekeeper",
                                           "pkg": "sierra_rosbridge",
                                           "type": "sierra_timekeeper.py",
                                           "required": "true",
                                           # Otherwise rospy prints nothing
                                           "output": "screen"
                                       },
                                       True)
                            )
            self.tag_adds = adds

        return [self.tag_adds]

    def gen_files(self) -> None:
        pass


def factory(arg: str,
            barrier_start: bool,
            robots_need_timekeeper: bool) -> ExpSetup:
    """Create an :class:`ExpSetup` derived class from the command line definition.

    Arguments:

       arg: The value of ``--exp-setup``.

    """
    parser = Parser({'n_secs_per_run': config.kROS['n_secs_per_run'],
                     'n_ticks_per_sec': config.kROS['n_ticks_per_sec'],
                     'n_datapoints': config.kExperimentalRunData['n_datapoints_1D']})
    attr = parser(arg)

    def __init__(self: ExpSetup) -> None:
        ExpSetup.__init__(self,
                          attr["n_secs_per_run"],
                          attr['n_datapoints'],
                          attr['n_ticks_per_sec'],
                          barrier_start,
                          robots_need_timekeeper)

    return type(attr['pretty_name'],
                (ExpSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'ExpSetup',


]
