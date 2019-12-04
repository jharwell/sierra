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
Command line parsing and validation classes for the SILICON project.
"""

import typing as tp

import core.cmdline


class Cmdline(core.cmdline.CoreCmdline):
    """
    Defines SILICON extensions to the core command line arguments defined in
    :class:`~core.cmdline.CoreCmdline`.
    """

    def __init__(self, super_scaffold: bool = False):
        super().__init__(super_scaffold)

        self.parser.add_argument("--controller",
                                 metavar="{depth0}.<controller>",
                                 help="""

                                 Which controller footbot robots will use in the construction experiment. All robots use the
                                 same controller (homogeneous swarms).

                                 Valid controllers:

                                 - depth0.{DPOB}

                                 Head over to the :xref:`SILICON` docs for the descriptions of these controllers.

                                 Use=stage{1,2,3,4}; can be omitted otherwise.

                                 """)

        construct = self.parser.add_argument_group('Stage1: Construction',
                                                   'Construction target options for stage1')

        construct.add_argument("--construct-targets",
                               metavar="<type>.AxBxC@X,Y",
                               help="""

                               A list of construction targets within a scenario, separated by spaces.

                               (A,B,C) are the dimensions of the bounding box for the target, and must be
                               integers. (X,Y) specifies the anchor of the target in the XY plane, defined as the
                               lower-left hand corner of the target.

                               Valid types are:

                               - ``rectprism`` - A rectangular, prismatic solid comprising a 4 sided polygonal base of
                                 dimensions AxB in X and Y, respectively, a second base which is a copy of the first,
                                 translated upward in Z by C units, and 4 other rectangular faces.

                               - ``ramp`` - A sloped ramp with slope along the X-axis from 0 to C.

                               For all structures, the active face is always on the positive X axis (for now).
                               Use=stage{1}; can be omitted otherwise.

                               """,
                               nargs='*',
                               default=None)
        construct.add_argument("--construct-n-subtargets",
                               type=int,
                               choices=[1, 2, 4],
                               help="""

                               Specify how many subtargets each construction target will be broken into. Effectively
                               creates N structures out of the target, incident/joined along the active face. This
                               allows for more fine grained task allocation decisions to be made by the swarm.

                               Using=stage{1}; can be omitted otherwise.
                               """,
                               default=1)
        construct.add_argument("--construct-orientation",
                               choices=['X', 'Y'],
                               help="""

                               Specify the primary orientation for the target, which defines the axis along which the
                               slope will be placed (for ``ramp`` structures), and the orientation of the X axis for
                               ``rectprism`` structures.

                               Using=stage{1}; can be omitted otherwise.
                               """,
                               default=1)

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: tp.Dict[str, str]):
        """
        Updates the core cmdopts dictionary with (key,value) pairs from the SILICON-specific cmdline options.
        """
        # Stage1
        updates = {
            'controller': cli_args.controller,
            'construct_targets': cli_args.construct_targets,
            'construct_n_subtargets': cli_args.construct_n_subtargets,
            'construct_orientation': cli_args.construct_orientation
        }
        cmdopts.update(updates)


class CmdlineValidator(core.cmdline.CoreCmdlineValidator):
    pass


def sphinx_cmdline():
    """
    Return a handle to the FORDYCA cmdline extensions to autogenerate nice documentation from it.
    """
    return Cmdline(True).parser
