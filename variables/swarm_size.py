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

from variables.batch_criteria import BatchCriteria
from variables.swarm_size_parser import SwarmSizeParser
import math


class SwarmSize(BatchCriteria):

    """
    Defines a range of swarm sizes to test with

    Attributes:
      size_list(list): List of integer sizes to test with.
    """

    def __init__(self, cmdline_str, main_config, batch_generation_root, size_list):
        BatchCriteria.__init__(self, cmdline_str, main_config, batch_generation_root)
        self.size_list = size_list

    def gen_attr_changelist(self):
        """
        Generate list of sets of swarm sizes. Each entry in the list is a set of changes
        necessary to make to the input file to correctly set up the simulation with the specified
        swarm size.
        """
        return [set([(".//arena/distribute/entity", "quantity", str(s))]) for s in self.size_list]

    def gen_exp_dirnames(self, cmdopts):
        changes = self.gen_attr_changelist()
        dirs = []
        for chg in changes:
            d = ''
            for path, attr, value in chg:

                if 'quantity' in attr:
                    d += 'size' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs']:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def sc_graph_labels(self, scenarios):
        return [s[-4:] for s in scenarios]

    def sc_sort_scenarios(self, scenarios):
        return scenarios  # No sorting needed

    def graph_xvals(self, cmdopts):
        ret = self.swarm_sizes(cmdopts)

        if cmdopts['plot_log_xaxis']:
            return [math.log2(x) for x in ret]
        else:
            return ret

    def graph_xlabel(self, cmdopts):
        return "Swarm Size"


def Factory(cmdline_str, main_config, batch_generation_root):
    """
    Creates swarm size classes from the command line definition of batch criteria.
    """
    attr = SwarmSizeParser().parse(cmdline_str.split(".")[1])

    def gen_sizes(cmdline_str):

        if "Linear" == attr["increment_type"]:
            return [attr["linear_increment"] * x for x in range(1, 11)]
        if "Log" == attr["increment_type"]:
            return [2 ** x for x in range(0, int(math.log2(attr["max_size"])) + 1)]

    def __init__(self):
        SwarmSize.__init__(self, cmdline_str, main_config, batch_generation_root,
                           gen_sizes(cmdline_str))

    return type(cmdline_str,
                (SwarmSize,),
                {"__init__": __init__})
