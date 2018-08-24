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
import math
import pickle
import os
from models.footbot import FootbotModel


class CAModelEnter:
    """
    Models the probability of a given robot entering collision avoidance analytically, for use in
    determining the level of interference/interaction/cooperation/etc should be present in a swarm.

    Assumes:
    - All robots are uniformly distributed in the arena each timestep.
    - The time spent in CA with walls/probability of entering CA due to being near a wall is
      extremely low/negligable.

    Attributes:
      robot_prox_radius(float): Radius of robot proximity/collision avoidance sensor, as measured
                                from the center of the robot (not from the limit of its physical
                                radius).
      robot_av_vel(float): Average robot velocity.
    """

    def __init__(self, batch_generation_root):
        self.robot_prox_radius = FootbotModel.kRobotProxRadius
        self.robot_av_vel = FootbotModel.kRobotAvgVelocity
        self.batch_generation_root = batch_generation_root

    def calc(self):
        """
        Calculate the analytical prediction for a set of swarm sizes, returning a list of
        integers specifying the # of robots that should be entering collision avoidance each
        timestep using this model.
        """
        ret = []
        for d in sorted(os.listdir(self.batch_generation_root), key=lambda t: int(t[3:])):
            size = 2 ** int(d[3:])
            exp_def_fpath = os.path.join(self.batch_generation_root, d, "exp_def.pkl")
            # Read in all the different sets of parameter changes that were pickled to make
            # crucial parts of the experiment definition easily accessible. I don't know how
            # many there are, so go until you get an exception.
            try:
                with open(exp_def_fpath, 'rb') as f:
                    exp_def = set()
                    while True:
                        exp_def = exp_def | pickle.load(f)
            except EOFError:
                pass

            for e in exp_def:
                if 'ticks_per_second' in e[0]:
                    timestep_duration = 1.0 / int(e[1])
                elif 'grid.size' in e[0]:
                    arena_dim = (int(e[1].split(',')[0]), int(e[1].split(',')[1]))

            print(self.robot_prox_radius, self.robot_av_vel, timestep_duration)
            neighbor_area = math.pi * (2 * self.robot_prox_radius + 2 * self.robot_av_vel *
                                       timestep_duration) ** 2
            robot_area = math.pi * (self.robot_prox_radius) ** 2
            total_area = arena_dim[0] * arena_dim[1]
            print(self.robot_prox_radius + 2 * self.robot_av_vel * timestep_duration)
            print(neighbor_area, robot_area, total_area)

            # This is the probability that a single neigbor robot moves into a given robot's
            # avoidance radius (i.e. close enough to trigger collision avoidance).

            prob_in_ca_area = (neighbor_area - robot_area) / (total_area - robot_area)
            print("prob in CA area:", prob_in_ca_area)
            neighbors_in_ca_area = prob_in_ca_area * (size - 1)
            print("neighbors:", neighbors_in_ca_area)
            prob_enter_c_area = 0.5

            a = (arena_dim[0] - (self.robot_prox_radius - self.robot_av_vel * timestep_duration)) *\
                (arena_dim[1] - (self.robot_prox_radius - self.robot_av_vel * timestep_duration))

            b = (arena_dim[0] - self.robot_prox_radius) * \
                (arena_dim[1] - self.robot_prox_radius)
            prob_ca_from_wall = (a - b) / total_area * 0.5
            print("prob CA from wall:", prob_ca_from_wall)
            prob_no_ca_from_wall = math.pow(1 - prob_ca_from_wall, size)
            prob_no_ca_from_neigbors = math.pow(1 - prob_enter_c_area, neighbors_in_ca_area)
            # Probability that all neigboring robots do NOT enter a given robot's collision
            # avoidance area, changing its state to CA.
            prob_no_ca = prob_no_ca_from_wall * prob_no_ca_from_neigbors

            print("prob no CA", prob_no_ca)
            prob_enter_ca = 1 - prob_no_ca
            print(prob_no_ca, prob_enter_ca)
            ret.append((prob_enter_ca + prob_ca_from_wall) * size)
        return ret


class CAModelDuration:
    """
    Models the distribution of the average collision avoidance duration for a given robot, once it
    enters CA analytically, for use in determining the level of
    interference/interaction/cooperation/etc should be present in a swarm.

    Assumes:
    - All robots are uniformly distributed in the arena each timestep.
    - No chained/cascading CA events occur (i.e. each one is resolved separately between two robots,
      or between a robot and a wall before the next one occurs).

    Attributes:
      robot_prox_radius(float): Radius of robot proximity/collision avoidance sensor, as measured
                                from the center of the robot (not from the limit of its physical
                                radius).
      robot_av_vel(float): Average robot velocity.
      timestep_duration(float): The length of a simulation timestep in seconds
      arena_dim(tuple): (X, Y) dimensions of the arena.
"""
