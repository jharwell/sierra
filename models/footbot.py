"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""


class FootbotModel:
    # Property of robot--OK to hardcode
    kRobotRadius = 0.2
    kRobotProxRadius = kRobotRadius + 0.15

    # Rough estimate--should be tweaked a bit depending on simulation results.  TODO: Get # this
    # from the simulation results themselves, or from the maximum speed which is currently
    # specified in the input file, but not written to exp_def where it would be accessible,
    # which record average velocity, rather than just guessing as I'm doing now.
    kRobotAvgVelocity = 0.06
