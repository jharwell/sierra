# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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


class ControllerGeneratorParser:
    """
    Parse the controller generator specification from cmdline arguments. Used later to
    create generator classes to make modifications to template input files.

    Format for pair is <decomposition depth>.<controller>

    Return:
      Parsed controller specification, the generator is missing from the command line
      altogether; this can occur if the user is only running stage [4,5], and is not an error. In
      that case, None is returned.
    """

    def __call__(self, args):
        if args.controller is None:
            return None

        return args.controller
