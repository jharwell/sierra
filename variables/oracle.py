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
from variables.oracle_parser import OracleParser
import itertools
from variables.swarm_size import SwarmSize


class Oracle(BaseVariable):
    info_types = {'entities': ['caches_enabled', 'blocks_enabled']}

    """
    Defines the type(s) of oracular information to disseminate to controllers during simulation.

    Attributes:
    tuples(list): List of tuples of types of oracular information to enable for a specific
      simulation. Each tuple is (oracle name, list(tuple(oracle feature name, oracle feature value))).
    """

    def __init__(self, tuples, swarm_size):
        self.tuples = tuples
        self.swarm_size = swarm_size

    def gen_attr_changelist(self):
        size_attr = next(iter(SwarmSize([self.swarm_size]).gen_attr_changelist()[0]))
        changes = []
        for t in self.tuples:
            c = [size_attr]
            c.extend([(".//oracle_manager/{0}".format(str(t[0])),
                       "{0}".format(str(feat[0])),
                       "{0}".format(str(feat[1]))) for feat in t[1]])
            changes.append(set(c))
        return changes

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


def Factory(criteria_str):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = OracleParser().parse(criteria_str)

    def gen_tuples(criteria_str):

        if 'entities' in attr['oracle_name']:
            tuples = []
            for val in list(itertools.product([False, True], repeat=len(Oracle.info_types['entities']))):
                tuples.append((attr['oracle_name'],
                               [(Oracle.info_types['entities'][i], str(val[i]).lower())
                                   for i in range(0, len(Oracle.info_types['entities']))]
                               ))
            return tuples

    def __init__(self):
        Oracle.__init__(self, gen_tuples(criteria_str), attr['swarm_size'])

    return type(criteria_str,
                (Oracle,),
                {"__init__": __init__})
