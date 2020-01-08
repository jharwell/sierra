# Copyright 2019, John Harwell, All rights reserved.
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
import re
import typing as tp
import pandas as pd

from core.variables.flexibility_parser import FlexibilityParser
from core.variables.batch_criteria import BatchCriteria
import core.perf_measures.vcs as vcs


class FlexibilityPlotsCSVGenerator:
    """
    Generates the ``.csv`` definitions for flexibility linegraphs to include with the rest of the
    intra-experiment graphs for stage 4. Very useful to verify the inter-experiment graphs are
    correct/make sense and that my waveform comparison calculations are doing what I think they
    are.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of commandline arguments used during intra-experiment graph
                 generation.
        perf_csv_col: The column within the intra-experiment performance .csv file to use as the
                      source of the performance waveforms to generate definitions for.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.perf_csv_col = main_config['sierra']['perf']['intra_perf_col']

    def __call__(self, batch_criteria: BatchCriteria):
        tv_attr = FlexibilityParser()(batch_criteria.def_str)

        # @BUG This will not work with any batch exp directory naming that is not expX
        res = re.search("exp[0-9]+", self.cmdopts['output_root'])
        assert res is not None, "FATAL: Unexpected experiment output dir name '{0}'".format(
            self.cmdopts['output_root'])

        # The output root we have here is our averaged output directory in the output root for the
        # *current* experiment. Since adaptability/reactivity are generally inter-experiment
        # measures, we need to 'reset' the output root we pass to the output root for the batched
        # experiment.
        output_root = self.cmdopts['output_root']
        self.cmdopts['output_root'] = self.cmdopts['output_root'].split(res.group())[0]
        exp_num = int(res.group()[3:])
        adaptability = vcs.AdaptabilityCS(self.main_config, self.cmdopts, batch_criteria, exp_num)
        reactivity = vcs.ReactivityCS(self.main_config, self.cmdopts, batch_criteria, exp_num)

        expx_perf = vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                batch_criteria,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['sierra']['perf']['intra_perf_csv'],
                                                exp_num)[self.perf_csv_col].values
        expx_var = vcs.DataFrames.expx_var_df(self.cmdopts,
                                              batch_criteria,
                                              self.main_config['sierra']['avg_output_leaf'],
                                              self.main_config['sierra']['perf']['tv_flexibility_csv'],
                                              exp_num)[tv_attr['variance_csv_col']].values
        comp_expx_var = self._comparable_exp_variance(expx_var,
                                                      tv_attr,
                                                      expx_perf.max(),
                                                      expx_perf.min())

        df = pd.DataFrame(
            {
                'clock': vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                     batch_criteria,
                                                     self.main_config['sierra']['avg_output_leaf'],
                                                     self.main_config['sierra']['perf']['intra_perf_csv'],
                                                     exp_num)['clock'].values,
                'expx_perf': vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                         batch_criteria,
                                                         self.main_config['sierra']['avg_output_leaf'],
                                                         self.main_config['sierra']['perf']['intra_perf_csv'],
                                                         exp_num)[self.perf_csv_col].values,
                'expx_var': comp_expx_var,
                'exp0_perf': vcs.DataFrames.exp0_perf_df(self.cmdopts,
                                                         batch_criteria,
                                                         self.main_config['sierra']['avg_output_leaf'],
                                                         self.main_config['sierra']['perf']['intra_perf_csv'])[self.perf_csv_col].values,
                'exp0_var': vcs.DataFrames.exp0_var_df(self.cmdopts,
                                                       batch_criteria,
                                                       self.main_config['sierra']['avg_output_leaf'],
                                                       self.main_config['sierra']['perf']['tv_flexibility_csv'])[tv_attr['variance_csv_col']].values,
                'ideal_reactivity': reactivity.calc_waveforms()[0][:, 1],
                'ideal_adaptability': adaptability.calc_waveforms()[0][:, 1]
            }
        )
        df.to_csv(os.path.join(output_root, 'tv-plots.csv'), sep=';', index=False)

    def _comparable_exp_variance(self, var_df, tv_attr, perf_max, perf_min):
        """
        Return the applied variance for an experiment that is directly comparable to the performance
        curves for the experiment via inversion. Not all curve similarity measures are scaling
        invariant, so we need to scale the variance waveform to within the min/max bounds of the
        performance curve we will be comparing against.
        """
        # The applied variance needs to be inverted in order to calculate curve similarity, because
        # the applied variance is a penalty, and as the penalties go UP, performance goes DOWN. Not
        # inverting the variance would therefore be unlikely to provide any correlation, and any it
        # did provide would be ridiculously counter intuitive. Inversion makes it comparable to
        # observed performance curves.
        #
        # So, invert the variance waveform by subtracting its y offset, reflecting it about the
        # x-axis, and then re-adding the y offset.
        #
        return (perf_max - perf_min) * (var_df - var_df.min()) / (var_df.max() - var_df.min()) + perf_min


class FlexibilityPlotsDefinitionsGenerator():
    """
    Generate plot definitions in a nested list/dictionary format, just as if they had been read
    from a YAML file.
    """

    def __call__(self):
        return [
            {'src_stem': 'tv-plots',
             'dest_stem': 'tv-plots-reactivity',
             'cols': ['exp0_var', 'expx_var', 'exp0_perf', 'expx_perf', 'ideal_reactivity'],
             'title': 'Observed vs. Ideal Reactivity Curves',
             'legend': ['Ideal Conditions Applied Variance',
                        'Experimental Conditions Applied Variance',
                        'Ideal Conditions Performance',
                        'Experimental Performance',
                        'Ideal Reactivity'],
             'xlabel': 'Interval',
             'ylabel': 'Swarm Performance (# Blocks collected)',
             'styles': ['-', '-', '-', '--', '-'],
             'dashes': [(1000, 0), (1000, 0), (1000, 0), (1000, 0), (4, 5)]
             },
            {
                'src_stem': 'tv-plots',
                'dest_stem': 'tv-plots-adaptability',
                'cols': ['exp0_var', 'expx_var', 'exp0_perf', 'expx_perf', 'ideal_adaptability', ],
                'title': 'Observed vs. Ideal Adaptability Curves',
                'legend': ['Ideal Conditions Applied Variance',
                           'Experimental Conditions Applied Variance',
                           'Ideal Conditions Performance',
                           'Experimental Performance',
                           'Ideal Adaptability'],
                'xlabel': 'Interval',
                'ylabel': 'Swarm Performance (# Blocks collected)',
                'styles': ['-', '-', '-', '--', '-'],
                'dashes': [(1000, 0), (1000, 0), (1000, 0), (1000, 0), (4, 5)]
            },
        ]
