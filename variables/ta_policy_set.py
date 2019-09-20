"""
 Copyright 2019 John Harwell, All rights reserved.

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

from variables.base_variable import BaseVariable
from variables.ta_policy_set_parser import TAPolicySetParser
from variables.swarm_size import SwarmSize


class TAPolicySet(BaseVariable):
    """
    Defines the task allocation policy to use during simulation.

    Attributes:
      policies(list): List of policies to enable for a specific simulation.
      swarm_size(str): Swarm size to use for a specific simulation.
    """

    def __init__(self, policies, swarm_size):
        self.policies = policies
        self.swarm_size = swarm_size

    def gen_attr_changelist(self):
        size_attr = next(iter(SwarmSize([self.swarm_size]).gen_attr_changelist()[0]))
        changes = []
        for p in self.policies:
            c = [size_attr]
            c.extend([(".//task_executive",
                       "alloc_policy",
                       "{0}".format(p))])
            changes.append(set(c))
        return changes

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []

    def gen_exp_dirnames(self, criteria_str):
        changes = self.gen_attr_changelist()
        dirs = []
        for chg in changes:
            for path, attr, value in chg:
                if 'alloc_policy' in attr:
                    policy = value
                elif 'quantity' in attr:
                    size = 'size' + value
            dirs.append(policy + '+' + size)
        return dirs


def Factory(criteria_str):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = TAPolicySetParser().parse(criteria_str)

    def gen_policies():
        return ['random', 'stoch_greedy_nbhd', 'greedy_global']

    def __init__(self):
        TAPolicySet.__init__(self, gen_policies(), attr['swarm_size'])

    return type(criteria_str,
                (TAPolicySet,),
                {"__init__": __init__})
