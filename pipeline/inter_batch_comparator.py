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
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.bar_graph import BarGraph

import perf_measures.utils as pm_utils
import batch_utils as butils
import copy
import yaml
import perf_measures.vcs


def intra_scenario_measures(reactivity_cs_method, adaptability_cs_method):
    return [
        {
            'src_stem': 'pm-pp-comp-positive',
            'dest_stem': 'cc-pm-pp-comp-positive',
            'title': 'Swarm Projective Performance Comparison (positive)',
            'ylabel': 'Observed-Projected Ratio',
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-pp-comp-negative',
            'dest_stem': 'cc-pm-pp-comp-negative',
            'title': 'Swarm Projective Performance Comparison (Negative)',
            'ylabel': 'Observed-Projected Ratio',
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-scalability-fl',
            'dest_stem': 'cc-pm-scalability-fl',
            'title': 'Swarm Scalability (Sub-Linear Fractional Losses)',
            'ylabel': 'Scalability Value',
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-scalability-norm',
            'dest_stem': 'cc-pm-scalability-norm',
            'title': 'Swarm Scalability (Normalized)',
            'ylabel': 'Scalability Value',
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-self-org',
            'dest_stem': 'cc-pm-self-org',
            'title': 'Swarm Self Organization',
            'ylabel': 'Self Organization Value',
            'n_exp_corr': 1
        },
        {
            'src_stem': 'pm-blocks-collected',
            'dest_stem': 'cc-pm-blocks-collected',
            'title': 'Swarm Performance',
            'ylabel': 'Total Blocks Collected',
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-karpflatt',
            'dest_stem': 'cc-pm-karpflatt',
            'title': 'Swarm Scalability (Karp-Flatt)',
            'ylabel': 'Karp-Flatt Value',
            'n_exp_corr': 1
        },
        {
            'src_stem': 'pm-reactivity',
            'dest_stem': 'cc-pm-reactivity',
            'title': r'Swarm Reactivity $R(N,\kappa)$',
            'ylabel': perf_measures.vcs.method_ylabel(reactivity_cs_method, 'reactivity'),
            'n_exp_corr': 0
        },
        {
            'src_stem': 'pm-adaptability',
            'dest_stem': 'cc-pm-adaptability',
            'title': r'Swarm Adaptability $A(N,\kappa)$',
            'ylabel': perf_measures.vcs.method_ylabel(adaptability_cs_method, 'adaptability'),
            'n_exp_corr': 1
        },
    ]


def inter_scenario_measures():
    return [
        {
            'src_stem': 'pm-scalability-fl',
            'dest_stem': 'sc-pm-scalability-fl',
            'title': 'Weight Unified Swarm Scalability (Sub-Linear Fractional Losses)',
        },
        {
            'src_stem': 'pm-scalability-norm',
            'dest_stem': 'sc-pm-scalability-norm',
            'title': 'Weight Unified Swarm Scalability (Normalized)',
        },
        {
            'src_stem': 'pm-self-org',
            'dest_stem': 'sc-pm-self-org',
            'title': 'Weight Unified Swarm Self Organization',
        },
        {
            'src_stem': 'pm-blocks-collected',
            'dest_stem': 'sc-pm-blocks-collected',
            'title': 'Weight Unified Blocks Collected',
        },
        {
            'src_stem': 'pm-adaptability',
            'dest_stem': 'sc-pm-adaptability',
            'title': 'Weight Unified Adaptability',
        },
        {
            'src_stem': 'pm-reactivity',
            'dest_stem': 'sc-pm-reactivity',
            'title': 'Weight Unified Reactivity',
        },


    ]


class InterBatchComparator:
    """
    Compares controllers on different criteria across/within different scenarios.
    """

    def __init__(self, controllers, cmdopts):
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))
        self.controllers = controllers

        self.cc_graph_root = os.path.join(self.cmdopts['sierra_root'], "cc-graphs")
        self.cc_csv_root = os.path.join(self.cmdopts['sierra_root'], "cc-csvs")
        self.sc_graph_root = os.path.join(self.cmdopts['sierra_root'], "sc-graphs")
        self.sc_csv_root = os.path.join(self.cmdopts['sierra_root'], "sc-csvs")

    def generate(self):
        self.generate_intra_scenario_graphs()
        self.generate_inter_scenario_graphs()

    def generate_inter_scenario_graphs(self):
        """
        Calculate weight unified estimates of:

        - Swarm scalability
        - Swarm self-organization

        ACROSS scenarios
        """

        for m in inter_scenario_measures():
            self._generate_inter_scenario_graph(src_stem=m['src_stem'],
                                                dest_stem=m['dest_stem'],
                                                title=m['title'])

    def _generate_inter_scenario_graph(self, src_stem, dest_stem, title):
        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        scenarios = butils.sort_scenarios(self.cmdopts['criteria_category'],
                                          os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                                  self.controllers[0])))

        swarm_sizes = []
        df = pd.DataFrame(columns=self.controllers, index=scenarios)

        for s in scenarios:
            cmdopts = copy.deepcopy(self.cmdopts)
            cmdopts['generation_root'] = os.path.join(self.cmdopts['sierra_root'],
                                                      self.controllers[0],
                                                      s,
                                                      "exp-inputs")
            cmdopts['n_exp'] = len(os.listdir(cmdopts['generation_root']))
            swarm_sizes = butils.swarm_sizes(cmdopts)
            for c in self.controllers:
                csv_ipath = os.path.join(self.cmdopts['sierra_root'],
                                         c,
                                         s,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'],
                                         src_stem + ".csv")

                # Some experiments might not generate the necessary performance measure .csvs for
                # graph generation, which is OK.
                if not os.path.exists(csv_ipath):
                    continue
                df.loc[s, c] = pm_utils.WeightUnifiedEstimate(input_csv_fpath=csv_ipath,
                                                              swarm_sizes=swarm_sizes).calc()

        csv_opath = os.path.join(self.sc_csv_root, 'sc-' +
                                 src_stem + "-wue.csv")
        df.to_csv(csv_opath, sep=';', index=False)

        scenarios = butils.prettify_scenario_labels(self.cmdopts['criteria_category'], scenarios)

        BarGraph(input_fpath=csv_opath,
                 output_fpath=os.path.join(self.sc_graph_root,
                                           dest_stem + '-wue.png'),
                 title=title,
                 xlabels=scenarios).generate()

    def generate_intra_scenario_graphs(self):
        """
        Calculate controller comparison metrics WITHIN a scenario:

        - Swarm scalability
        - Swarm self-organization
        """
        for m in intra_scenario_measures(self.cmdopts['reactivity_cs_method'],
                                         self.cmdopts['adaptability_cs_method']):
            self._generate_intra_scenario_graph(src_stem=m['src_stem'],
                                                dest_stem=m['dest_stem'],
                                                title=m['title'],
                                                ylabel=m['ylabel'],
                                                n_exp_corr=m['n_exp_corr'])

    def _generate_intra_scenario_graph(self, src_stem, dest_stem, title, ylabel, n_exp_corr):

        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        scenarios = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))

        # Different scenarios can have different #s of experiments within them, so we need to track
        # accordingly
        exp_counts = {}
        self._generate_intra_scenario_files(scenarios, src_stem, exp_counts, n_exp_corr)

        for s in scenarios:
            if s not in exp_counts:
                continue

            csv_stem_opath = os.path.join(self.cc_csv_root, 'cc-' + src_stem + "-" + s)

            # All scenarios are NOT guaranteed to have the same # of experiments, so we need to
            # overwrite key elements of the cmdopts in order to ensure proper processing.
            cmdopts = copy.deepcopy(self.cmdopts)
            batch_generation_root = os.path.join(self.cmdopts['sierra_root'],
                                                 self.controllers[0],
                                                 s,
                                                 "exp-inputs")
            batch_output_root = os.path.join(self.cmdopts['sierra_root'],
                                             self.controllers[0],
                                             s,
                                             "exp-outputs")
            cmdopts['generation_root'] = batch_generation_root
            cmdopts["n_exp"] = exp_counts[s]
            cmdopts['output_root'] = batch_output_root

            BatchRangedGraph(inputy_stem_fpath=csv_stem_opath,
                             output_fpath=os.path.join(self.cc_graph_root,
                                                       dest_stem) + '-' + s + ".png",
                             title=title,
                             xlabel=butils.graph_xlabel(cmdopts),
                             ylabel=ylabel,
                             xvals=butils.graph_xvals(cmdopts)[n_exp_corr:],
                             legend=self.controllers,
                             polynomial_fit=-1).generate()

    def _generate_intra_scenario_files(self, scenarios, src_stem, exp_counts, n_exp_corr):
        for s in scenarios:
            df = pd.DataFrame()
            stddev_df = pd.DataFrame()
            for c in self.controllers:
                csv_ipath = os.path.join(self.cmdopts['sierra_root'],
                                         c,
                                         s,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'],
                                         src_stem + ".csv")
                stddev_ipath = os.path.join(self.cmdopts['sierra_root'],
                                            c,
                                            s,
                                            'exp-outputs',
                                            self.main_config['sierra']['collate_csv_leaf'],
                                            src_stem + ".stddev")

                # Some experiments might not generate the necessary performance measure .csvs for
                # graph generation, which is OK.
                if not os.path.exists(csv_ipath):
                    continue

                df = df.append(pd.read_csv(csv_ipath, sep=';'))
                if os.path.exists(stddev_ipath):
                    stddev_df = stddev_df.append(pd.read_csv(stddev_ipath, sep=';'))

                exp_counts[s] = len(df.columns)

                # For some graphs, the .csv only contains entries for exp >=1, BUT we need to have
                # the full experiment count in order to get the axis labels to come out right.
                exp_counts[s] += n_exp_corr

            csv_opath_stem = os.path.join(self.cc_csv_root, 'cc-' +
                                          src_stem + "-" + s)
            df.to_csv(csv_opath_stem + '.csv', sep=';', index=False)
            if not stddev_df.empty:
                stddev_df.to_csv(csv_opath_stem + '.stddev', sep=';', index=False)
