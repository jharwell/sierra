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

import os
import copy
from pipeline.inter_exp_linegraphs import InterExpLinegraphs
from perf_measures.scalability import InterExpScalability
from perf_measures.self_organization import InterExpSelfOrganization
from perf_measures.collection import InterExpBlockCollection
from perf_measures.reactivity import InterExpReactivity

from graphs.ca_graphs import InterExpCAModelEnterGraph
from pipeline.inter_exp_targets import Linegraphs


class InterExpGraphGenerator:
    """
    Generates graphs from collated .csv data across a batch of experiments.

    Attributes:
    """

    def __init__(self, cmdopts):

        self.cmdopts = copy.deepcopy(cmdopts)
        self.cmdopts["collate_root"] = os.path.abspath(os.path.join(self.cmdopts["output_root"],
                                                                    'collated-csvs'))
        self.cmdopts["graph_root"] = os.path.abspath(os.path.join(self.cmdopts["graph_root"],
                                                                  'collated-graphs'))
        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)

    def __call__(self):
        if "all" == self.cmdopts["perf_measures"]:
            InterExpLinegraphs(self.cmdopts["collate_root"],
                               self.cmdopts["graph_root"],
                               Linegraphs.targets('depth2' in self.cmdopts["generator"])).generate()

        if "all" == self.cmdopts["perf_measures"] or "sp" == self.cmdopts["perf_measures"]:
            InterExpBlockCollection(self.cmdopts).generate()

        if "all" == self.cmdopts["perf_measures"] or "sc" == self.cmdopts["perf_measures"]:
            InterExpScalability(self.cmdopts).generate()

        if "all" == self.cmdopts["perf_measures"] or "so" == self.cmdopts["perf_measures"]:
            InterExpSelfOrganization(self.cmdopts).generate()

        if "all" == self.cmdopts["perf_measures"] or "sr" == self.cmdopts["perf_measures"]:
            InterExpReactivity(self.cmdopts).generate()

            # InterExpCAModelEnterGraph(self.batch_output_root, self.batch_graph_root,
            #                           self.batch_generation_root).generate()
