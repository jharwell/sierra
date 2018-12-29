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
        "dtw": "Experiment Dynamic Time Warp (DTW) Distance To Ideal Conditions"
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


def compute_envc_cs(cmdopts, exp_num, max_exp):
    """
    Compute the Variance Curve Similarity (VCS) measure between the ideal conditions of exp0 and the
    specified experiment.

    cmdopts(dict): Dictionary of parsed commandline options.
    exp_num(int): Current experiment number to compute VCS for.
    max_exp(int): The experiment number of the experiment that has environmental conditions MOST
                  different from ideal/exp0.
    """

    ideal_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                        "exp0/averaged-output",
                                        kTemporalVarCSV),
                           sep=';')
    exp_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                      "exp" + str(exp_num) + "/averaged-output",
                                      kTemporalVarCSV),
                         sep=';')
    attr = TemporalVarianceParser().parse(cmdopts["criteria_def"])

    xlen = len(exp_df[attr["variance_csv_col"]].values)
    exp_data = np.zeros((xlen, 2))
    exp_data[:, 0] = exp_df["clock"].values
    exp_data[:, 1] = exp_df[attr["variance_csv_col"]].values

    ideal_data = np.zeros((xlen, 2))
    ideal_data[:, 0] = ideal_df["clock"].values
    ideal_data[:, 1] = ideal_df[attr["variance_csv_col"]].values

    return _compute_vcs_raw(exp_data, ideal_data, cmdopts["envc_cs_method"])


def compute_perf_cs(cmdopts, exp_num):
    """
    Compute the Variance Curve Similarity (VCS) measure between the observed performance curve and
    the applied variance for the experiment.

    cmdopts(dict): Dictionary of parsed commandline options.
    exp_num(int): Current experiment number to compute VCS for.
    """

    perf_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                       "exp" + str(exp_num) + "/averaged-output",
                                       kPerfCSV),
                          sep=';')
    var_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                      "exp" + str(exp_num) + "/averaged-output",
                                      kTemporalVarCSV),
                         sep=';')
    # IMPORTANT! The simulation clock starts at 1, but indexing starts at 0, so you need to subtract
    # 1 from the clock to use it as the index when subsampling to avoid getting NaN in the result.
    var_df = var_df.reindex(index=perf_df['clock'] - 1, columns=[c for c in var_df.columns
                                                                 if c != 'clock'])

    attr = TemporalVarianceParser().parse(cmdopts["criteria_def"])

    # The applied variance needs to be inverted in order to calculate curve similarity, because the
    # applied variance is a penalty, and as the penalties go UP, performance goes DOWN. Not
    # inverting the variance would therefore be unlikely to provide any correlation, and any it did
    # provide would be ridiculously counter intuitive.
    #
    # So, invert the variance waveform by subtracting its y offset, reflecting it about the x-axis,
    # and then re-adding the y offset.
    #
    xlen = len(var_df[attr["variance_csv_col"]].values)
    inv_var = _reflect_waveform(var_df[attr["variance_csv_col"]].values)

    exp_data = np.zeros((xlen, 2))
    exp_data[:, 0] = perf_df["clock"].values
    exp_data[:, 1] = perf_df['int_collected_' + attr["variance_csv_col"]].values

    ideal_data = np.zeros((xlen, 2))
    ideal_data[:, 0] = var_df.index.values
    ideal_data[:, 1] = inv_var

    return _compute_vcs_raw(exp_data, ideal_data, cmdopts["reactivity_cs_method"])


def _reflect_waveform(waveform):
    xlen = len(waveform)
    offset = sum(waveform) / xlen
    return -(waveform - offset) + offset


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
