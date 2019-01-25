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

import fastdtw
import os
import pandas as pd
import numpy as np
import similaritymeasures as sm
from variables.temporal_variance_parser import TemporalVarianceParser

kTemporalVarCSV = "loop-temporal-variance.csv"
kPerfCSV = "block-transport.csv"


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
        "dtw": "DTW Distance To Ideal Conditions"
    }
    return labels[method]


def method_ylabel(method):
    """
    Return the Y-label of the method used for calculating the curve similarity.
    """
    if method is None:
        return None
    labels = {
        "pcm": "PCM Distance Between Variance and Performance Curves",
        "area_between": "Area Between Variance and Performance Curves",
        "frechet": "Frechet Distance Between Variance and Performance Curves",
        "curve_length": "Curve Length Difference Between Variance and Performance Curves",
        "dtw": "DTW Distance Between Variance and Performance Curves"
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

    def __call__(self):
        ideal_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                            "exp0/averaged-output",
                                            kTemporalVarCSV),
                               sep=';')
        exp_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                          "exp" + str(self.exp_num) + "/averaged-output",
                                          kTemporalVarCSV),
                             sep=';')
        attr = TemporalVarianceParser().parse(self.cmdopts["criteria_def"])

        xlen = len(exp_df[attr["variance_csv_col"]].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = exp_df["clock"].values
        exp_data[:, 1] = exp_df[attr["variance_csv_col"]].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_df["clock"].values
        ideal_data[:, 1] = ideal_df[attr["variance_csv_col"]].values

        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["envc_cs_method"])


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

    def __init__(self, cmdopts, exp_num):
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def __call__(self):
        exp0_perf_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                                "exp0/averaged-output",
                                                kPerfCSV),
                                   sep=';')
        expx_perf_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                                "exp" + str(self.exp_num) + "/averaged-output",
                                                kPerfCSV),
                                   sep=';')
        expx_var_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                               "exp" + str(self.exp_num) + "/averaged-output",
                                               kTemporalVarCSV),
                                  sep=';')

        exp0_var_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                               "exp0/averaged-output",
                                               kTemporalVarCSV),
                                  sep=';')

        # IMPORTANT! The simulation clock starts at 1, but indexing starts at 0, so you need to
        # subtract 1 from the clock to use it as the index when subsampling to avoid getting NaN in
        # the result.
        expx_var_df = expx_var_df.reindex(index=expx_perf_df['clock'] - 1, columns=[c for c in expx_var_df.columns
                                                                                    if c != 'clock'])
        exp0_var_df = exp0_var_df.reindex(index=expx_perf_df['clock'] - 1, columns=[c for c in exp0_var_df.columns
                                                                                    if c != 'clock'])

        tv_attr = TemporalVarianceParser().parse(self.cmdopts["criteria_def"])

        var_col = tv_attr["variance_csv_col"]
        perf_col = "int_collected"

        exp0_var_df = exp0_var_df.reset_index(drop=True)
        expx_var_df = expx_var_df.reset_index(drop=True)

        ideal_df = pd.DataFrame(index=exp0_var_df.index, columns=[perf_col])

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
        for i in exp0_perf_df[perf_col].index:
            if exp0_var_df.loc[i, var_col] > expx_var_df.loc[i, var_col]:
                ideal_df.loc[i, perf_col] = exp0_perf_df.loc[i, perf_col] * \
                    (exp0_var_df.loc[i, var_col] / expx_var_df.loc[i, var_col])
            elif exp0_var_df.loc[i, var_col] < expx_var_df.loc[i, var_col]:
                ideal_df.loc[i, perf_col] = exp0_perf_df.loc[i, perf_col]
            else:
                ideal_df.loc[i, perf_col] = expx_perf_df.loc[i, perf_col]

        xlen = len(exp0_var_df[var_col].values)

        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df["clock"].values
        exp_data[:, 1] = expx_perf_df[perf_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_df.index.values
        ideal_data[:, 1] = ideal_df[perf_col].values

        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["reactivity_cs_method"])


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

    def __init__(self, cmdopts, exp_num):
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def __call__(self):
        perf_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                           "exp" + str(self.exp_num) + "/averaged-output",
                                           kPerfCSV),
                              sep=';')
        var_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                          "exp" + str(self.exp_num) + "/averaged-output",
                                          kTemporalVarCSV),
                             sep=';')
        # IMPORTANT! The simulation clock starts at 1, but indexing starts at 0, so you need to
        # subtract 1 from the clock to use it as the index when subsampling to avoid getting NaN in
        # the result.
        var_df = var_df.reindex(index=perf_df['clock'] - 1, columns=[c for c in var_df.columns
                                                                     if c != 'clock'])

        tv_attr = TemporalVarianceParser().parse(self.cmdopts["criteria_def"])

        perf_max = perf_df['int_collected'].max()
        perf_min = perf_df['int_collected'].min()
        comp_var = _comparable_exp_variance(var_df, tv_attr, perf_max, perf_min)

        xlen = len(var_df[tv_attr["variance_csv_col"]].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = perf_df["clock"].values
        exp_data[:, 1] = perf_df['int_collected'].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = var_df.index.values
        ideal_data[:, 1] = comp_var

        return _compute_vcs_raw(exp_data, ideal_data, self.cmdopts["reactivity_cs_method"])


def _comparable_exp_variance(var_df, tv_attr, perf_max, perf_min):
    """
    Return the applied variance for an experiment that is directly comparable to the performance
    curves for the experiment via inversion. Not all curve similarity measures are scaling
    invariant, so we need to scale the variance waveform to within the min/max bounds of the
    performance curve we will be comparing against.
    """
    # The applied variance needs to be inverted in order to calculate curve similarity, because
    # the applied variance is a penalty, and as the penalties go UP, performance goes DOWN. Not
    # inverting the variance would therefore be unlikely to provide any correlation, and any it
    # did provide would be ridiculously counter intuitive. Inversion makes it comparable to observed
    # performance curves.
    #
    # So, invert the variance waveform by subtracting its y offset, reflecting it about the x-axis,
    # and then re-adding the y offset.
    #
    xlen = len(var_df[tv_attr["variance_csv_col"]].values)
    midpoint = sum(var_df[tv_attr["variance_csv_col"]].values) / xlen

    reflected = -(var_df[tv_attr["variance_csv_col"]].values - midpoint) + midpoint
    r_max = reflected.max()
    r_min = reflected.min()

    return (perf_max - perf_min) * (reflected - r_min) / (r_max - r_min) + perf_min


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
