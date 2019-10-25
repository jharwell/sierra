# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#


import os
import copy
import yaml

from .intra_exp_linegraphs import IntraExpLinegraphs
from .intra_exp_heatmaps import IntraExpHeatmaps
from .temporal_variance_plot_defs import TemporalVariancePlotDefs


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
        cmdopts(dict): Dictionary of commandline arguments used during intra-experiment graph
                     generation.
    """

    def __init__(self, main_config, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config

        self.cmdopts["output_root"] = os.path.join(self.cmdopts["output_root"],
                                                   self.main_config['sierra']['avg_output_leaf'])

        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)
        self.linegraph_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                            'intra-graphs-line.yaml')),
                                          yaml.FullLoader)
        self.hm_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                     'intra-graphs-hm.yaml')),
                                   yaml.FullLoader)

        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                             'controllers.yaml')),
                                           yaml.FullLoader)

    def __call__(self, batch_criteria):
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
                if self.cmdopts['gen_vc_plots']:  # optional
                    extra_graphs = TemporalVariancePlotDefs(self.cmdopts)(batch_criteria,
                                                                          self.main_config)

        filtered_keys = [k for k in self.linegraph_config if k in keys]
        targets = [self.linegraph_config[k] for k in filtered_keys]
        targets.append({'graphs': extra_graphs})

        print("-- Enabled linegraph categories: {0}".format(filtered_keys))

        IntraExpLinegraphs(self.cmdopts["output_root"],
                           self.cmdopts["graph_root"],
                           targets).generate()

        filtered_keys = [k for k in self.hm_config if k in keys]
        targets = [self.hm_config[k] for k in filtered_keys]

        print("-- Enabled heatmap categories: {0}".format(filtered_keys))
        IntraExpHeatmaps(self.cmdopts["output_root"],
                         self.cmdopts["graph_root"],
                         targets).generate()
