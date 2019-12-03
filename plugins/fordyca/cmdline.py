# Copyright 2019 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
#  General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#
"""
Command line parsing and validation classes.
"""

import argparse

import core.cmdline


class Cmdline(core.cmdline.CoreCmdline):
    """
    Defines FORDYCA extensions to the core command line arguments defined in
    :class:`~core.cmdline.CoreCmdline`.
    """

    def __init__(self, super_scaffold: bool = False):
        super().__init__(super_scaffold)

        self.parser.add_argument("--controller",
                                 metavar="{depth0, depth1, depth2}.<controller>",
                                 help="""

                                 Which controller footbot robots will use in the foraging experiment. All robots use the
                                 same controller (homogeneous swarms).

                                 Valid controllers:

                                 - depth0.{CRW, DPO, MDPO},
                                 - depth1.{BITD_DPO, OBITD_DPO},
                                 - depth2.{BIRTD_DPO, OBIRTD_DPO}

                                 Use=stage{1,2,3,4}; can be omitted otherwise.

                                 """)

        self.stage1.add_argument("--static-cache-blocks",
                                 help="""

                                 # of blocks used when the static cache is respawned (depth1 controllers
                                 Specify the
                                 only).

                                 Use=stage{1}; can be omitted otherwise.

                                 """,
                                 default=None)


class CmdlineValidator(core.cmdline.CoreCmdlineValidator):
    pass


def sphinx_cmdline():
    """
    Return a handle to the FORDYCA cmdline extensions to autogenerate nice documentation from it.
    """
    return Cmdline(True).parser
