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

from variables.batch_criteria import BatchCriteria
from variables.oracle_parser import OracleParser
import itertools
from variables.swarm_size import SwarmSize


class Oracle(BatchCriteria):
    kInfoTypes = {'entities': ['caches', 'blocks']}

    """
    Defines the type(s) of oracular information to disseminate to controllers during simulation.

    Attributes:
    tuples(list): List of tuples of types of oracular information to enable for a specific
      simulation. Each tuple is (oracle name, list(tuple(oracle feature name, oracle feature value))).
    """

    def __init__(self, cmdline_str, main_config, batch_generation_root,
                 tuples, swarm_size):
        BatchCriteria.__init__(self, cmdline_str, main_config, batch_generation_root)

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

    def gen_exp_dirnames(self, cmdopts):
        changes = self.gen_attr_changelist()
        attr = OracleParser().parse(self.cmdline_str)
        dirs = []
        for chg in changes:
            d = ''
            for t in Oracle.kInfoTypes[attr['oracle_type']]:
                for path, at, value in chg:
                    if t in at:
                        d += '+' * ('' != d) + t + '=' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs']:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def sc_graph_labels(self, scenarios):
        return scenarios

    def sc_sort_scenarios(self, scenarios):
        return scenarios  # No sorting needed

    def graph_xvals(self, cmdopts):
        return [i for i in range(1, self.n_exp() + 1)]

    def graph_xlabel(self, cmdopts):
        return "Oracular Swarms"


def Factory(cmdline_str, main_config, batch_generation_root):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = OracleParser().parse(cmdline_str)

    def gen_tuples(cmdline_str):

        if 'entities' in attr['oracle_name']:
            tuples = []
            for val in list(itertools.product([False, True], repeat=len(Oracle.kInfoTypes['entities']))):
                tuples.append((attr['oracle_name'],
                               [(Oracle.kInfoTypes['entities'][i], str(val[i]).lower())
                                   for i in range(0, len(Oracle.kInfoTypes['entities']))]
                               ))
            return tuples

    def __init__(self):
        Oracle.__init__(self, cmdline_str, main_config, batch_generation_root,
                        gen_tuples(cmdline_str), attr['swarm_size'])

    return type(cmdline_str,
                (Oracle,),
                {"__init__": __init__})
