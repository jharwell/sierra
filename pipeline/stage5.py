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

from perf_measures.scalability import ScalabilityMeasure
import os


class PipelineStage5:

    """

    Implements stage 5 of the experimental pipeline:

    Compare controllers that have been tested with the same batch criteria across different
    performance measures.

    Attributes:
      args(??): Input arguments to sierra
      targets(str): List of controllers (as strings) that should be compared within sierra_root.
    """

    def __init__(self, args, targets):
        self.args = args
        self.targets = targets

    def _comp_targets(self):
        measures = []
        for t1 in self.targets:
            for t2 in self.targets:
                if t1 == t2:
                    continue
                measures.append({'measure': 'ScalabilityMeasure',
                                 'dest_stem': 'scalability-{0}-{1}'.format(t1, t2),
                                 'title_stem': '{0} vs. {1} (interval):'.format(t1, t2),
                                 'xlabel': 'timestep',
                                 'ylabel': '# Blocks Gathered (interval)'
                                 })
        return measures

    def run(self):
        # Verify that all controllers have run the same set of experiments before doing the
        # comparison
        print("- Comparing controllers...")
        for t1 in self.targets:
            for t2 in self.targets:
                for item in os.listdir(os.path.join(self.args.sierra_root, t1)):
                    path1 = os.path.join(self.args.sierra_root, t1, item)
                    path2 = os.path.join(self.args.sierra_root, t2, item)
                    if os.path.isdir(path1):
                        assert(os.path.exists(path2)), "FATAL: {0} does not exist".format(path2)
                    if os.path.isdir(path2):
                        assert(os.path.exists(path1)), "FATAL: {0} does not exist".format(path1)

        ScalabilityMeasure(path1, path2).generate()
        print("- Controller comparison complete")
