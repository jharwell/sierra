# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for the ``--exp-setup`` cmdline option for ROS1 engines.

See :ref:`usage/vars/expsetup` for usage documentation.

"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import definition
from sierra.core import config
from sierra.core.variables import exp_setup


@implements.implements(IBaseVariable)
class ExpSetup:
    """
    Defines the experimental setup for ROS experiments.

    Attributes:
        n_secs_per_run: The :term:`Experimental Run` duration in seconds, NOT
                        :term:`Ticks <Tick>` or timesteps.

        n_ticks_per_sec: How many times per second robot controllers will be
                         run.

    """

    def __init__(
        self,
        n_secs_per_run: int,
        n_ticks_per_sec: int,
        barrier_start: bool,
        robots_need_timekeeper: bool,
    ) -> None:
        self.n_secs_per_run = n_secs_per_run
        self.n_ticks_per_sec = n_ticks_per_sec
        self.barrier_start = barrier_start
        self.robots_need_timekeeper = robots_need_timekeeper

        self.element_adds = None

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        return []

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        return []

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        if not self.element_adds:
            adds = definition.ElementAddList(
                definition.ElementAdd(
                    "./master/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/length",
                        "value": str(self.n_secs_per_run),
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./master/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/ticks_per_sec",
                        "value": str(self.n_ticks_per_sec),
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./master/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/barrier_start",
                        "value": str(self.barrier_start).lower(),
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./master/group/[@ns='sierra']",
                    "node",
                    {
                        "name": "sierra_timekeeper",
                        "pkg": "sierra_rosbridge",
                        "type": "sierra_timekeeper.py",
                        "required": "true",
                        # Otherwise rospy prints nothing
                        "output": "screen",
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./robot/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/length",
                        "value": str(self.n_secs_per_run),
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./robot/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/ticks_per_sec",
                        "value": str(self.n_ticks_per_sec),
                    },
                    True,
                ),
                definition.ElementAdd(
                    "./robot/group/[@ns='sierra']",
                    "param",
                    {
                        "name": "experiment/barrier_start",
                        "value": str(self.barrier_start).lower(),
                    },
                    True,
                ),
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
                adds.append(
                    definition.ElementAdd(
                        "./robot/group/[@ns='sierra']",
                        "node",
                        {
                            "name": "sierra_timekeeper",
                            "pkg": "sierra_rosbridge",
                            "type": "sierra_timekeeper.py",
                            "required": "true",
                            # Otherwise rospy prints nothing
                            "output": "screen",
                        },
                        True,
                    )
                )
            self.element_adds = adds

        return [self.element_adds]

    def gen_files(self) -> None:
        pass


def factory(arg: str, barrier_start: bool, robots_need_timekeeper: bool) -> ExpSetup:
    """Create an :class:`ExpSetup` derived class from the command line definition.

    Arguments:

       arg: The value of ``--exp-setup``.

    """
    attr = exp_setup.parse(
        arg,
        {
            "n_secs_per_run": config.ROS["n_secs_per_run"],
            "n_ticks_per_sec": config.ROS["n_ticks_per_sec"],
        },
    )

    return ExpSetup(
        attr["n_secs_per_run"],
        attr["n_ticks_per_sec"],
        barrier_start,
        robots_need_timekeeper,
    )


__all__ = [
    "ExpSetup",
]
