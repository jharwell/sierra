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

from pipeline.intra_exp_graph_generator import IntraExpGraphGenerator
from pipeline.csv_collator import CSVCollator
from pipeline.batched_intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from pipeline.inter_exp_graph_generator import InterExpGraphGenerator
import yaml
import os
import matplotlib as mpl
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.use('Agg')


class PipelineStage4:

    """

    Implements stage 4 of the experimental pipeline:

    Generate a user-defined set of graphs based on the averaged results for each
    experiment, and across experiments for batches.
    """

    def __init__(self, cmdopts, batch_criteria):
        self.cmdopts = cmdopts
        self.batch_criteria = batch_criteria

        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                             'controllers.yaml')))
        self.linegraph_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                            'inter-graphs-line.yaml')))
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

    def run(self):
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            self._gen_intra_graphs()

        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            # Collation must be after intra-experiment graph generation, so that all .csv files to
            # be collated have been generated/modified according to parameters.
            targets = self._calc_linegraph_targets()
            CSVCollator(self.main_config, self.cmdopts, targets, self.batch_criteria)()
            self._gen_inter_graphs(targets)

    def _gen_inter_graphs(self, targets):
        if self.batch_criteria is not None:
            print("- Stage4: Generating inter-experiment graphs...")
            InterExpGraphGenerator(self.cmdopts, targets, self.batch_criteria)()
            print("- Stage4: Inter-experiment graph generation complete")

    def _gen_intra_graphs(self):
        if self.batch_criteria is not None:
            intra_exp = BatchedIntraExpGraphGenerator(self.cmdopts)
        else:
            intra_exp = IntraExpGraphGenerator(self.cmdopts)

        print("- Stage4: Generating intra-experiment graphs...")
        intra_exp()
        print("- Stage4: Intra-experiment graph generation complete")

    def _calc_linegraph_targets(self):
        """
        Use the parsed controller+inter-exp linegraph config to figure out what .csv files need to
        be collated/what graphs should be generated.
        """
        keys = []
        extra_graphs = []
        for category in list(self.controller_config.keys()):
            if category not in self.cmdopts['controller']:
                continue
            for controller in self.controller_config[category]['controllers']:
                if controller['name'] not in self.cmdopts['controller']:
                    continue

                # valid to specify no graphs, and only to inherit graphs
                keys = controller.get('graphs', [])
                if 'graphs_inherit' in controller:
                    [keys.extend(l) for l in controller['graphs_inherit']]  # optional

        filtered_keys = [k for k in self.linegraph_config if k in keys]
        targets = [self.linegraph_config[k] for k in filtered_keys]
        targets.append({'graphs': extra_graphs})

        print("- Enabled linegraph categories: {0}".format(filtered_keys))
        return targets
