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


def method_xlabel(method):
    """
    Return the X-label of the method used for calculating the vcs value.
    """
    if method is None:
        return None
    labels = {
        "pcm": "Partial Curve Mapping",
        "area_between": "Area Between Curves",
        "frechet": "Frechet Distance w.r.t exp0",
        "curve_length": "Curve Length w.r.t exp0",
        "dtw": "Dynamic Time Warp w.r.t exp0"
    }
    return labels[method]


def compute_vcs(cmdopts, exp_num, max_exp):
    """
    Compute the Variance Curve Similar (VCS) measure between the ideal conditions of exp0 and the
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
    max_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                      "exp" + str(max_exp) + "/averaged-output",
                                      kTemporalVarCSV),
                         sep=';')
    exp_df = pd.read_csv(os.path.join(cmdopts["output_root"],
                                      "exp" + str(exp_num) + "/averaged-output",
                                      kTemporalVarCSV),
                         sep=';')
    attr = TemporalVarianceParser().parse(cmdopts["criteria_def"])

    max_sample = max(abs(max_df[attr["variance_csv_col"]].values -
                         ideal_df[attr["variance_csv_col"]].values))

    xlen = len(exp_df[attr["variance_csv_col"]].values)
    exp_data = np.zeros((xlen, 2))
    exp_data[:, 0] = exp_df["clock"].values
    exp_data[:, 1] = exp_df[attr["variance_csv_col"]].values

    ideal_data = np.zeros((xlen, 2))
    ideal_data[:, 0] = ideal_df["clock"].values
    ideal_data[:, 1] = ideal_df[attr["variance_csv_col"]].values

    if "pcm" == cmdopts["envc_cs_method"]:
        return sm.pcm(exp_data, ideal_data)
    elif "area_between" == cmdopts["envc_cs_method"]:
        return sm.area_between_two_curves(exp_data, ideal_data)
    elif "frechet" == cmdopts["envc_cs_method"]:
        return sm.frechet_dist(exp_data, ideal_data)
    elif "dtw" == cmdopts["envc_cs_method"]:
        # Don't use the sm version--waaayyyy too slow
        dist, path = fastdtw.fastdtw(exp_data, ideal_data)
        return (max_sample * xlen - dist) / (max_sample * xlen)
    elif "curve_length" == cmdopts["envc_cs_method"]:
        return sm.curve_length_measure(exp_data, ideal_data)
