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
from perf_measures.scalability import ControllerCompScalabilityMeasure
from perf_measures.emergence import ControllerCompEmergenceMeasure


class PipelineStage5:

    """

    Implements stage 5 of the experimental pipeline:

    Compare controllers that have been tested with the same batch criteria across different
    performance measures.

    Attributes:
      args(??): Input arguments to sierra
      targets(list): List of controllers (as strings) that should be compared within sierra_root.
    """

    def __init__(self, args, targets):
        self.args = args
        self.targets = targets
        self.comp_graph_root = os.path.join(args.sierra_root, "comp-graphs")
        self.comp_csv_root = os.path.join(args.sierra_root, "comp-csvs")

        os.makedirs(self.comp_graph_root, exist_ok=True)
        os.makedirs(self.comp_csv_root, exist_ok=True)

    def _comp_measures(self):
        measures = [
            {
                'type': 'ControllerCompScalabilityMeasure',
                'src_stem': 'pm-scalability-raw',
                'dest_stem': 'comp-pm-scalability-raw',
            },
            {
                'type': 'ControllerCompScalabilityMeasure',
                'src_stem': 'pm-scalability-fl',
                'dest_stem': 'comp-pm-scalability-fl',
            },
            {
                'type': 'ControllerCompEmergenceMeasure',
                'src_stem': 'pm-emergence',
                'dest_stem': 'comp-pm-emergence',
            },
        ]
        return measures

    def run(self):
        # Verify that all controllers have run the same set of experiments before doing the
        # comparison
        print("- Comparing controllers...")
        if self.targets is None:
            self.targets = [d for d in os.listdir(self.args.sierra_root) if d not in ["comp-graphs",
                                                                                      "comp-csvs"]
                            and os.path.isdir(os.path.join(self.args.sierra_root, d))]
        else:
            self.targets = self.targets.split(',')

        for t1 in self.targets:
            for t2 in self.targets:
                for item in os.listdir(os.path.join(self.args.sierra_root, t1)):
                    path1 = os.path.join(self.args.sierra_root, t1, item,
                                         "exp-outputs/collated-csvs")
                    path2 = os.path.join(self.args.sierra_root, t2, item,
                                         "exp-outputs/collated-csvs")
                    if os.path.isdir(path1):
                        assert(os.path.exists(path2)), "FATAL: {0} does not exist".format(path2)
                    if os.path.isdir(path2):
                        assert(os.path.exists(path1)), "FATAL: {0} does not exist".format(path1)

        measures = self._comp_measures()
        for m in measures:
            eval(m['type'])(sierra_root=self.args.sierra_root,
                            controllers=self.targets,
                            src_stem=m['src_stem'],
                            dest_stem=m['dest_stem']).generate()
        print("- Controller comparison complete")
