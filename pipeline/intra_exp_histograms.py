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
import multiprocessing
from multiprocessing import Queue
from graphs.histogram import Histogram


class IntraExpHistograms:
    """
    Generates histograms from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
      targets(list): Dictionary of lists of dictiaries specifying what graphs should be
                     generated.
    """

    def __init__(self, exp_output_root, exp_graph_root, targets):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets
        self.graph_queue = Queue()

    def generate(self):
        depth0_labels = ['fsm-collision',
                         'fsm-movement',
                         'block_trans',
                         'block_acq',
                         'block_manip',
                         'world_model']

        labels = depth0_labels
        print("-- Generating histograms {0}".format(self.exp_output_root))
        for target_set in [self.targets[x] for x in labels]:

            for target in target_set:
                self.graph_queue.put(target)

            for i in range(0, 8):
                t = multiprocessing.Process(target=IntraExpHistograms._process_queue, args=(self,))
                t.start()
                t.join()

    def _generate_graph_mt(self, target):
        """Generates a graph inside a thread from the specified dictionary of target attributes."""
        # print(target)
        for col in target['cols']:
            Histogram(input_fpath=os.path.join(self.exp_output_root,
                                               target['src_stem'] + '.csv'),
                      output_fpath=os.path.join(
                self.exp_graph_root,
                target['src_stem'] + '-' + col + '-hist.eps'),
                col=col,
                title=target['title'],
                xlabel=col,
                ylabel='Count').generate()

    def _process_queue(self):
        while not self.graph_queue.empty():
            target = self.graph_queue.get()
            self._generate_graph_mt(target)
