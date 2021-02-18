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
"""
Utility classes for generating definitions and ``.csv`` files for per-experiment flexibility plots
by hooking into the intra-experiment graph generation.
"""

# Core packages
import os
import copy
import re

# 3rd party packages
import pandas as pd

# Project packages
from core.variables.temporal_variance_parser import TemporalVarianceParser
from core.variables.batch_criteria import BatchCriteria
import core.perf_measures.vcs as vcs
import core.utils
import core.config


class FlexibilityPlotsCSVGenerator:
    """
    Generates the ``.csv`` definitions for flexibility linegraphs to include with the rest of the
    intra-experiment graphs for stage 4. Very useful to verify the inter-experiment graphs are
    correct/make sense and that my waveform comparison calculations are doing what I think they
    are.

    Note: Only works for univariate batch criteria.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of commandline arguments used during intra-experiment graph
                 generation.
        perf_csv_col: The column within the intra-experiment performance .csv file to use as the
                      source of the performance waveforms to generate definitions for.
    """

    def __init__(self, main_config: dict, cmdopts: dict) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.perf_csv_col = main_config['perf']['intra_perf_col']

    def __call__(self, batch_criteria: BatchCriteria):
        tv_attr = TemporalVarianceParser()(batch_criteria.def_str)

        res = re.search("exp[0-9]+", self.cmdopts['exp_output_root'])
        assert res is not None, "FATAL: Unexpected experiment output dir name '{0}'".format(
            self.cmdopts['exp_output_root'])

        stat_root = self.cmdopts['exp_stat_root']
        exp_num = int(res.group()[3:])

        adaptability = vcs.AdaptabilityCS(self.main_config,
                                          self.cmdopts,
                                          batch_criteria,
                                          core.config.kStatsExtensions['mean'],
                                          0,
                                          exp_num)
        reactivity = vcs.ReactivityCS(self.main_config,
                                      self.cmdopts,
                                      batch_criteria,
                                      core.config.kStatsExtensions['mean'],
                                      0,
                                      exp_num)

        expx_perf = vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                batch_criteria,
                                                None,
                                                self.main_config['perf']['intra_perf_csv'],
                                                exp_num)[self.perf_csv_col].values

        exp0_var = vcs.DataFrames.expx_var_df(self.cmdopts,
                                              batch_criteria,
                                              None,
                                              self.main_config['perf']['tv_environment_csv'],
                                              0)[tv_attr['variance_csv_col']]
        # exp0_var = (exp0_var - exp0_var.min()) / (exp0_var.max(0) - exp0_var.min())

        expx_var = vcs.DataFrames.expx_var_df(self.cmdopts,
                                              batch_criteria,
                                              None,
                                              self.main_config['perf']['tv_environment_csv'],
                                              exp_num)[tv_attr['variance_csv_col']]
        # expx_var = (expx_var - expx_var.min()) / (expx_var.max() - expx_var.min())

        expx_perf = vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                batch_criteria,
                                                None,
                                                self.main_config['perf']['intra_perf_csv'],
                                                exp_num)[self.perf_csv_col]
        # expx_perf = (expx_perf - expx_perf.min()) / (expx_perf.max(0) - expx_perf.min())

        exp0_perf = vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                batch_criteria,
                                                None,
                                                self.main_config['perf']['intra_perf_csv'],
                                                0)[self.perf_csv_col]
        # exp0_perf = (exp0_perf - exp0_perf.min()) / (exp0_perf.max(0) - exp0_perf.min())

        df = pd.DataFrame(
            {
                'clock': vcs.DataFrames.expx_perf_df(self.cmdopts,
                                                     batch_criteria,
                                                     None,
                                                     self.main_config['perf']['intra_perf_csv'],
                                                     exp_num)['clock'].values,
                'expx_perf': expx_perf.values,
                'expx_var': expx_var.values,
                'exp0_perf': exp0_perf.values,
                'exp0_var': exp0_var.values,
                'ideal_reactivity': reactivity.calc_waveforms()[0][:, 1],
                'ideal_adaptability': adaptability.calc_waveforms()[0][:, 1]
            }
        )
        core.utils.pd_csv_write(df, os.path.join(stat_root, 'flexibility-plots.csv'), index=False)

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
            {'src_stem': 'flexibility-plots',
             'dest_stem': 'flexibility-plots-perf-curves',
             'cols': ['exp0_perf', 'expx_perf', 'ideal_reactivity', 'ideal_adaptability'],
             'title': 'Swarm Performance Curves',
             'legend': [r'$P_{ideal}(\mathcal{N},\kappa,t)$',
                        r'$P(\mathcal{N},\kappa,t)$',
                        r'$P_{R^*}(\mathcal{N},\kappa,t)$',
                        r'$P_{A^*}(\mathcal{N},\kappa,t)$'],
             'xlabel': 'Time Interval',
             'ylabel': 'Block Collection Rate',
             'styles': ['-', '--', '-', '--'],
             'dashes': [(1000, 0), (1000, 0), (4, 5), (8, 4)]
             },
            {'src_stem': 'flexibility-plots',
             'dest_stem': 'flexibility-plots-variance',
             'cols': ['exp0_var', 'expx_var'],
             'title': 'Environmental Variances',
             'legend': [r'$I_{ec}(t)$', '$V_{dev}(t)$'],
             'xlabel': 'Time Interval',
             'ylabel': 'Throttling Percent',
             'styles': ['-', '-'],
             'dashes': [(1000, 0), (1000, 0)]
             },
        ]
