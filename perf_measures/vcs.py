# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
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


import fastdtw
import os
import pandas as pd
import numpy as np
import yaml
import similaritymeasures as sm
from variables.temporal_variance_parser import TemporalVarianceParser
import utils


def method_xlabel(method):
    """
    Return the X-label of the method used for calculating the curve similarity.
    """
    if method is None:
        return None
    labels = {
        "pcm": "Partial Curve Mapping Distance To Ideal Conditions",
        "area_between": "Area Difference For Experiment and Ideal Conditions Variance Curves",
        "frechet": "Experiment Frechet Distance To Ideal Conditions",
        "curve_length": "Curve Length Difference To Ideal Conditions",
        "dtw": r'DTW($I_{ec}(t)$,$V_{ec}(t)$)'
    }
    return labels[method]


def method_ylabel(method, arg):
    """
    Return the Y-label of the method used for calculating the curve similarity.

    method(str): Method name.
    arg(str): An additional multi-purpose argument to pass to the function
    """
    if method is None:
        return None

    ideal_curve_names = {
        "adaptability": r'$P_{A^{*}}(N,\kappa,t)$',
        "reactivity": r'$P_{R^{*}}(N,\kappa,t)$',
    }

    labels = {
        "pcm": "PCM Distance Between Variance and Performance Curves",
        "area_between": "Area Between Variance and Performance Curves",
        "frechet": "Frechet Distance Between Variance and Performance Curves",
        "curve_length": "Curve Length Difference Between Variance and Performance Curves",
        "dtw": r'DTW(' + ideal_curve_names[arg] + ',' + r'$P(N,\kappa,t)$)'
    }
    return labels[method]


class EnvironmentalCS():
    """
    Compute the Variance Curve Similarity (VCS) measure between the ideal conditions of exp0 and the
    specified experiment.

    cmdopts(dict): Dictionary of parsed commandline options.
    exp_num(int): Current experiment number to compute VCS for.
    """

    def __init__(self, cmdopts, exp_num):
        self.cmdopts = cmdopts
        self.exp_num = exp_num
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

    def __call__(self, batch_criteria, exp_dirs=None):
        if exp_dirs is None:
            dirs = batch_criteria.gen_exp_dirnames(self.cmdopts)
        else:
            dirs = exp_dirs

        ideal_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                            dirs[0],
                                            self.main_config['sierra']['avg_output_leaf'],
                                            self.main_config['sierra']['perf']['temporal_var_csv']),
                               sep=';')
        exp_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                          dirs[self.exp_num],
                                          self.main_config['sierra']['avg_output_leaf'],
                                          self.main_config['sierra']['perf']['temporal_var_csv']),
                             sep=';')
        attr = TemporalVarianceParser().parse(batch_criteria.cli_arg)

        xlen = len(exp_df[attr["variance_csv_col"]].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = exp_df["clock"].values
        exp_data[:, 1] = exp_df[attr["variance_csv_col"]].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_df["clock"].values
        ideal_data[:, 1] = ideal_df[attr["variance_csv_col"]].values

        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["envc_cs_method"])


class DataFrames:
    @staticmethod
    def expx_var_df(cmdopts, batch_criteria, avg_output_leaf, temporal_var_csv, exp_num):
        return pd.read_csv(os.path.join(cmdopts['output_root'],
                                        batch_criteria.gen_exp_dirnames(cmdopts)[exp_num],
                                        avg_output_leaf,
                                        temporal_var_csv),
                           sep=';')

    @staticmethod
    def expx_perf_df(cmdopts, batch_criteria, avg_output_leaf, intra_perf_csv, exp_num):
        return pd.read_csv(os.path.join(cmdopts['output_root'],
                                        batch_criteria.gen_exp_dirnames(cmdopts)[exp_num],
                                        avg_output_leaf,
                                        intra_perf_csv),
                           sep=';')

    @staticmethod
    def exp0_perf_df(cmdopts, batch_criteria, avg_output_leaf, intra_perf_csv):
        return pd.read_csv(os.path.join(cmdopts['output_root'],
                                        batch_criteria.gen_exp_dirnames(cmdopts)[0],
                                        avg_output_leaf,
                                        intra_perf_csv),
                           sep=';')

    @staticmethod
    def exp0_var_df(cmdopts, batch_criteria, avg_output_leaf, temporal_var_csv):
        return pd.read_csv(os.path.join(cmdopts['output_root'],
                                        batch_criteria.gen_exp_dirnames(cmdopts)[0],
                                        avg_output_leaf,
                                        temporal_var_csv),
                           sep=';')


class AdaptabilityCS():
    """
    Compute the adaptability of a controller/algorithm by comparing the observed performance curve
    for the current experiment, the performance curve for exp0, and the applied variance curve for
    the experiment. An algorithm that is maximally adaptive will have a performance curve that:

    - Tracks the inverse of the applied variance very closely if the value of the applied variance
      at a time t is BELOW the value at time t for exp0. In that case we should see a proportional
      INCREASE in observed performance for the current experiment.

    - Remain unchanged from the value at time t for exp0 if the value of the applied variance is
      ABOVE the value at time t for exp0. This corresponds to resisting the adverse conditions
      present in the current experiment.

    Assumes exp0 is "ideal" conditions.

    cmdopts(dict): Dictionary of parsed commandline options.
    exp_num(int): Current experiment number to compute VCS for.
    """

    def __init__(self, cmdopts, batch_criteria, exp_num):
        self.cmdopts = cmdopts
        self.batch_criteria = batch_criteria
        self.exp_num = exp_num

        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'], 'main.yaml')))
        self.perf_csv_col = 'cum_avg_collected'
        self.var_csv_col = TemporalVarianceParser().parse(
            self.batch_criteria.cli_arg)['variance_csv_col']

    def calc_waveforms(self):
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """
        exp0_perf_df = DataFrames.exp0_perf_df(self.cmdopts,
                                               self.batch_criteria,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['sierra']['perf']['intra_perf_csv'])
        exp0_var_df = DataFrames.exp0_var_df(self.cmdopts,
                                             self.batch_criteria,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['sierra']['perf']['temporal_var_csv'])
        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.batch_criteria,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['sierra']['perf']['intra_perf_csv'],
                                               self.exp_num)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             self.batch_criteria,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['sierra']['perf']['temporal_var_csv'],
                                             self.exp_num)

        ideal_df = pd.DataFrame(index=exp0_var_df.index, columns=[self.perf_csv_col])

        # The performance curve of an adaptable system should resist adverse changes in the
        # environment, and should exploit beneficial changes in the environment.
        #
        # So, if the penalty imposed during the current experiment at timestep t is more than that
        # imposed during the ideal conditions experiment (exp0), then the performance curve should
        # exactly resemble the one for ideal conditions (for a maximally adaptable system). If the
        # penalty imposed during the current experiment at timestep t is less than that imposed
        # during the ideal conditions experiment, then the performance curve should be observed to
        # increase by an amount proportional to that difference, as the system exploits the drop in
        # penalties.
        for i in exp0_perf_df[self.perf_csv_col].index:
            if exp0_var_df.loc[i, self.var_csv_col] > expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = exp0_perf_df.loc[i, self.perf_csv_col] * \
                    (exp0_var_df.loc[i, self.var_csv_col] / expx_var_df.loc[i, self.var_csv_col])
            elif exp0_var_df.loc[i, self.var_csv_col] < expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = exp0_perf_df.loc[i, self.perf_csv_col]
            else:
                ideal_df.loc[i, self.perf_csv_col] = expx_perf_df.loc[i, self.perf_csv_col]

        xlen = len(exp0_var_df[self.var_csv_col].values)

        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df["clock"].values
        exp_data[:, 1] = expx_perf_df[self.perf_csv_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_df.index.values
        ideal_data[:, 1] = ideal_df[self.perf_csv_col].values
        return ideal_data, exp_data

    def __call__(self):
        ideal_data, exp_data = self.calc_waveforms()
        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["adaptability_cs_method"])


class ReactivityCS():

    """
    Compute the Variance Curve Similarity (VCS) measure between the observed performance curve and
    the applied variance for the experiment. An algorithm that is maximally reactive will have
    a performance curve that:

    - Tracks the inverse of the applied variance very closely. If the value of the applied variance
      at a time t is BELOW the value at time t for exp0, then we should see a proportional
      INCREASE in observed performance for the current experiment, and vice versa.

    Assumes exp0 is "ideal" conditions.

    cmdopts(dict): Dictionary of parsed commandline options.
    exp_num(int): Current experiment number to compute VCS for.
    """

    def __init__(self, cmdopts, batch_criteria, exp_num):
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

        self.exp_num = exp_num
        self.perf_csv_col = 'cum_avg_collected'
        self.var_csv_col = TemporalVarianceParser().parse(
            batch_criteria.cli_arg)['variance_csv_col']
        self.batch_criteria = batch_criteria

    def calc_waveforms(self):
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """
        exp0_perf_df = DataFrames.exp0_perf_df(self.cmdopts,
                                               self.batch_criteria,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['sierra']['perf']['intra_perf_csv'])
        exp0_var_df = DataFrames.exp0_var_df(self.cmdopts,
                                             self.batch_criteria,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['sierra']['perf']['temporal_var_csv'])
        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.batch_criteria,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['sierra']['perf']['intra_perf_csv'],
                                               self.exp_num)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             self.batch_criteria,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['sierra']['perf']['temporal_var_csv'],
                                             self.exp_num)

        ideal_df = pd.DataFrame(index=exp0_var_df.index, columns=[self.perf_csv_col])

        # The performance curve of a reactive system should respond proportionally to both adverse
        # and beneficial changes in the environment.
        #
        # So, if the penalty imposed during the current experiment at timestep t is less than that
        # imposed during the ideal conditions experiment, then the performance curve should be
        # observed to increase by an amount proportional to that difference, as the system reacts
        # the drop in penalties. Vice versa for an increase penalty in the experiment for a timestep
        # t vs. the amount imposed during the ideal conditions experiment.
        for i in exp0_perf_df[self.perf_csv_col].index:
            if exp0_var_df.loc[i, self.var_csv_col] > expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = exp0_perf_df.loc[i, self.perf_csv_col] * \
                    (exp0_var_df.loc[i, self.var_csv_col] / expx_var_df.loc[i, self.var_csv_col])
            elif exp0_var_df.loc[i, self.var_csv_col] < expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = exp0_perf_df.loc[i, self.perf_csv_col] * \
                    (exp0_var_df.loc[i, self.var_csv_col] / expx_var_df.loc[i, self.var_csv_col])
            else:
                ideal_df.loc[i, self.perf_csv_col] = expx_perf_df.loc[i, self.perf_csv_col]

        xlen = len(exp0_var_df[self.var_csv_col].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df["clock"].values
        exp_data[:, 1] = expx_perf_df[self.perf_csv_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = expx_var_df.index.values
        ideal_data[:, 1] = ideal_df[self.perf_csv_col].values

        return ideal_data, exp_data

    def __call__(self):
        ideal_data, exp_data = self.calc_waveforms()
        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["reactivity_cs_method"])


def _compute_vcs_raw(exp_data, ideal_data, method):
    if "pcm" == method:
        return sm.pcm(exp_data, ideal_data)
    elif "area_between" == method:
        return sm.area_between_two_curves(exp_data, ideal_data)
    elif "frechet" == method:
        return sm.frechet_dist(exp_data, ideal_data)
    elif "dtw" == method:
        # Don't use the sm version--waaayyyy too slow
        dist, path = fastdtw.fastdtw(exp_data, ideal_data)
        return dist
    elif "curve_length" == method:
        return sm.curve_length_measure(exp_data, ideal_data)
