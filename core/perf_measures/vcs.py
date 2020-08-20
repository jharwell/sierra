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


import os
import typing as tp
import logging

import fastdtw
import pandas as pd
import numpy as np
import similaritymeasures as sm

from core.variables.batch_criteria import BatchCriteria
from core.variables.temporal_variance_parser import TemporalVarianceParser


def method_xlabel(method: str):
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
        "dtw": r'DTW($I_{{ec}}(t)$,$V_{{ec}}(t)$)'
    }
    return labels[method]


def method_ylabel(method: str, arg):
    """
    Return the Y-label of the method used for calculating the curve similarity.

    method: Method name.
    arg: An additional multi-purpose argument to pass to the function
    """
    if method is None:
        return None

    ideal_curve_names = {
        "adaptability": r'$P_{A^{*}}(N,\kappa,t)$',
        "reactivity": r'$P_{R^{*}}(N,\kappa,t)$',
        "robustness_saa": r'$P_{B_{saa}^{*}}(N,\kappa,t)$',
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

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of parsed commandline options.
        exp_num: Current experiment number to compute VCS for.
    """

    def __init__(self,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str],
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num
        self.main_config = main_config

    def __call__(self, criteria: BatchCriteria, exp_dirs: tp.List[str] = None):
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              criteria,
                                              exp_dirs,
                                              self.main_config['sierra']['avg_output_leaf'],
                                              self.main_config['perf']['tv_environment_csv'],
                                              0)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             criteria,
                                             exp_dirs,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['perf']['tv_environment_csv'],
                                             self.exp_num)

        attr = TemporalVarianceParser()(criteria.cli_arg)

        xlen = len(expx_var_df[attr["variance_csv_col"]].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_var_df["clock"].values
        exp_data[:, 1] = expx_var_df[attr["variance_csv_col"]].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_var_df["clock"].values
        ideal_data[:, 1] = ideal_var_df[attr["variance_csv_col"]].values
        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       method=self.cmdopts["envc_cs_method"])


class RawPerfCS():
    """
    Compute the Curve Similarity (CS) measure between the performance in ideal conditions of exp0
    and the performance in the specified experiment.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of parsed commandline options.
        exp_num: Current experiment number to compute VCS for.
    """

    def __init__(self,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str],
                 ideal_num: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.ideal_num = ideal_num
        self.exp_num = exp_num
        self.main_config = main_config

    def __call__(self, criteria: BatchCriteria, exp_dirs: tp.List[str] = None) -> float:
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                criteria,
                                                exp_dirs,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['perf']['intra_perf_csv'],
                                                self.ideal_num)
        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               criteria,
                                               exp_dirs,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['perf']['intra_perf_csv'],
                                               self.exp_num)

        intra_perf_col = self.main_config['perf']['intra_perf_col']

        xlen = len(expx_perf_df[intra_perf_col].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df["clock"].values
        exp_data[:, 1] = expx_perf_df[intra_perf_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_perf_df["clock"].values
        ideal_data[:, 1] = ideal_perf_df[intra_perf_col].values

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       maxval=self.__maxval_calc(ideal_perf_df, intra_perf_col),
                       method=self.cmdopts["rperf_cs_method"])

    def __maxval_calc(self, ideal_perf_df, intra_perf_col: str):
        if self.cmdopts['rperf_cs_method'] == 'dtw':
            # Max value is the maximum performance under ideal conditions (exp0) as compared with an
            # expx curve which is 0 at every point
            return ideal_perf_df[intra_perf_col].max() * len(ideal_perf_df[intra_perf_col])
        else:
            logging.warning('No maxval defined for method %s',
                            self.cmdopts['rperf_cs_method'])
            return None


class AdaptabilityCS():
    """
    Compute the adaptability of a controller/algorithm by comparing the observed performance curve
    for the current experiment, the performance curve for exp0, and the applied variance curve for
    the experiment.

    An algorithm that is maximally adaptive will have a performance curve that remains unchanged
    from the value at time t from the value in exp0 for all t. This corresponds to resisting the
    adverse AND beneficial conditions present in the current experiment.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of parsed commandline options.
        criteria: The batch criteria for the experiment.
        exp_num: Current experiment number to compute VCS for.

    """

    def __init__(self,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str],
                 criteria: BatchCriteria,
                 ideal_num: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        self.exp_num = exp_num
        self.ideal_num = ideal_num
        self.main_config = main_config

        self.perf_csv_col = main_config['perf']['intra_perf_col']
        self.var_csv_col = TemporalVarianceParser()(self.criteria.cli_arg)['variance_csv_col']

    def calc_waveforms(self, exp_dirs: tp.List[str] = None):
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['perf']['intra_perf_csv'],
                                                self.ideal_num)
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              self.criteria,
                                              exp_dirs,
                                              self.main_config['sierra']['avg_output_leaf'],
                                              self.main_config['perf']['tv_environment_csv'],
                                              self.ideal_num)
        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.criteria,
                                               exp_dirs,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['perf']['intra_perf_csv'],
                                               self.exp_num)

        ideal_df = pd.DataFrame(index=ideal_var_df.index, columns=[self.perf_csv_col])

        # The performance curve of an adaptable system should resist all changes in the
        # environment, and be the same as exp0
        ideal_df[self.perf_csv_col] = ideal_perf_df[self.perf_csv_col]

        xlen = len(ideal_var_df[self.var_csv_col].values)

        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df['clock'].values
        exp_data[:, 1] = expx_perf_df[self.perf_csv_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = expx_perf_df['clock'].values
        ideal_data[:, 1] = ideal_df[self.perf_csv_col].values
        return ideal_data, exp_data

    def __call__(self, exp_dirs: tp.List[str] = None):
        ideal_data, exp_data = self.calc_waveforms(exp_dirs)

        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['perf']['intra_perf_csv'],
                                                self.ideal_num)

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       maxval=self.__maxval_calc(ideal_perf_df),
                       method=self.cmdopts["adaptability_cs_method"])

    def __maxval_calc(self, ideal_perf_df):
        if self.cmdopts['adaptability_cs_method'] == 'dtw':
            # Max value is the maximum performance under ideal conditions (exp0) as compared with an
            # expx curve which is 0 at every point.
            return ideal_perf_df[self.perf_csv_col].max() * len(ideal_perf_df[self.perf_csv_col])
        else:
            logging.warning('No maxval defined for method %s',
                            self.cmdopts['adaptability_cs_method'])
            return None


class ReactivityCS():

    """
    Compute the Variance Curve Similarity (VCS) measure between the observed performance curve and
    the applied variance for the experiment. An algorithm that is maximally reactive will have
    a performance curve that:

    - Tracks the inverse of the applied variance very closely. If the value of the applied variance
      at a time t is BELOW the value at time t for exp0, then we should see a proportional
      INCREASE in observed performance for the current experiment, and vice versa.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary of parsed commandline options.
        exp_num: Current experiment number to compute VCS for.
    """

    def __init__(self,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str],
                 criteria: BatchCriteria,
                 ideal_num: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config

        self.ideal_num = ideal_num
        self.exp_num = exp_num
        self.perf_csv_col = self.main_config['perf']['intra_perf_col']
        self.var_csv_col = TemporalVarianceParser()(criteria.cli_arg)['variance_csv_col']
        self.criteria = criteria

    def __call__(self, exp_dirs: tp.List[str] = None) -> float:
        ideal_data, exp_data = self.calc_waveforms(exp_dirs)
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['perf']['intra_perf_csv'],
                                                self.ideal_num)

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       maxval=self.__maxval_calc(ideal_perf_df),
                       method=self.cmdopts["reactivity_cs_method"])

    def calc_waveforms(self, exp_dirs: tp.List[str] = None):
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.main_config['sierra']['avg_output_leaf'],
                                                self.main_config['perf']['intra_perf_csv'],
                                                self.ideal_num)
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              self.criteria,
                                              exp_dirs,
                                              self.main_config['sierra']['avg_output_leaf'],
                                              self.main_config['perf']['tv_environment_csv'],
                                              self.ideal_num)
        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.criteria,
                                               exp_dirs,
                                               self.main_config['sierra']['avg_output_leaf'],
                                               self.main_config['perf']['intra_perf_csv'],
                                               self.exp_num)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             self.criteria,
                                             exp_dirs,
                                             self.main_config['sierra']['avg_output_leaf'],
                                             self.main_config['perf']['tv_environment_csv'],
                                             self.exp_num)

        ideal_df = pd.DataFrame(index=ideal_var_df.index, columns=[self.perf_csv_col])

        # The performance curve of a reactive system should respond proportionally to both adverse
        # and beneficial changes in the environment.
        #
        # So, if the penalty imposed during the current experiment at timestep t is less than that
        # imposed during the ideal conditions experiment, then the performance curve should be
        # observed to increase by an amount proportional to that difference, as the system reacts
        # the drop in penalties. Vice versa for an increase penalty in the experiment for a timestep
        # t vs. the amount imposed during the ideal conditions experiment.
        for i in ideal_perf_df[self.perf_csv_col].index:
            if ideal_var_df.loc[i, self.var_csv_col] > expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = ideal_perf_df.loc[i, self.perf_csv_col] * \
                    (ideal_var_df.loc[i, self.var_csv_col] / expx_var_df.loc[i, self.var_csv_col])
            elif ideal_var_df.loc[i, self.var_csv_col] < expx_var_df.loc[i, self.var_csv_col]:
                ideal_df.loc[i, self.perf_csv_col] = ideal_perf_df.loc[i, self.perf_csv_col] * \
                    (ideal_var_df.loc[i, self.var_csv_col] / expx_var_df.loc[i, self.var_csv_col])
            else:
                ideal_df.loc[i, self.perf_csv_col] = expx_perf_df.loc[i, self.perf_csv_col]

        xlen = len(ideal_var_df[self.var_csv_col].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df['clock'].values
        exp_data[:, 1] = expx_perf_df[self.perf_csv_col].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = expx_var_df['clock'].values
        ideal_data[:, 1] = ideal_df[self.perf_csv_col].values

        return ideal_data, exp_data

    def __maxval_calc(self, ideal_perf_df):
        if self.cmdopts['reactivity_cs_method'] == 'dtw':
            # Max value is the maximum performance under ideal conditions (exp0) as compared with an
            # expx curve which is 0 at every point.
            return ideal_perf_df[self.perf_csv_col].max() * len(ideal_perf_df[self.perf_csv_col])
        else:
            logging.warning('No maxval defined for method %s',
                            self.cmdopts['reactivity_cs_method'])
            return None


class CSRaw():
    """
    Given two array-like objects representing ideal and non-ideal (experimental) conditions and a
    method for comparison, perform the comparison.
    """

    def __call__(self,
                 exp_data,
                 ideal_data,
                 method: str,
                 maxval: tp.Optional[float] = None):
        assert method is not None, "FATAL: Cannot compare curves without method"

        if method == "pcm":
            return sm.pcm(exp_data, ideal_data)
        elif method == "area_between":
            return sm.area_between_two_curves(exp_data, ideal_data)
        elif method == "frechet":
            return sm.frechet_dist(exp_data, ideal_data)
        elif method == "dtw":
            return CSRaw.__calc_dtw(exp_data, ideal_data, maxval)
        elif method == "curve_length":
            return sm.curve_length_measure(exp_data, ideal_data)
        else:
            return None

    @staticmethod
    def __scale_minmax(minval: float, maxval: float, val: float):
        """
        Scale values from range [minval, maxval] -> [-1,1]
        """
        return -1.0 + (val - minval) * (1 - (-1)) / (maxval - minval)

    @staticmethod
    def __calc_dtw(exp_data, ideal_data, maxval: tp.Optional[float]):
        # Don't use the sm version--waaayyyy too slow
        dist, _ = fastdtw.fastdtw(exp_data, ideal_data)

        if maxval is not None:
            # Normalize [0,infinity) into [0,1], where HIGHER values now are better (much more
            # intuitive this way)
            normalized = (maxval - dist) / maxval

            # Normalize into [-1,1] to be congruent with the other measures
            return CSRaw.__scale_minmax(0.0, 1.0, normalized)

        return dist


class DataFrames:
    @staticmethod
    def expx_var_df(cmdopts: tp.Dict[str, str],
                    criteria: BatchCriteria,
                    exp_dirs: tp.Optional[tp.List[str]],
                    avg_output_leaf: str,
                    tv_environment_csv: str,
                    exp_num: int):
        if exp_dirs is None:
            dirs = criteria.gen_exp_dirnames(cmdopts)
        else:
            dirs = exp_dirs

        try:
            path = os.path.join(cmdopts['output_root'],
                                dirs[exp_num],
                                avg_output_leaf,
                                tv_environment_csv)
            return pd.read_csv(path, sep=';')
        except (FileNotFoundError, IndexError):
            logging.fatal("%s does not exist for exp num %s",
                          path,
                          exp_num)

    @staticmethod
    def expx_perf_df(cmdopts: tp.Dict[str, str],
                     criteria: BatchCriteria,
                     exp_dirs: tp.Optional[tp.List[str]],
                     avg_output_leaf: str,
                     intra_perf_csv: str,
                     exp_num: int):
        if exp_dirs is None:
            dirs = criteria.gen_exp_dirnames(cmdopts)
        else:
            dirs = exp_dirs

        try:
            path = os.path.join(cmdopts['output_root'],
                                dirs[exp_num],
                                avg_output_leaf,
                                intra_perf_csv)
            return pd.read_csv(path, sep=';')
        except (FileNotFoundError, IndexError):
            logging.fatal("%s does not exist for exp num %s",
                          path,
                          exp_num)


__api__ = [
    'EnvironmentalCS',
    'RawPerfCS',
    'AdaptabilityCS',
    'ReactivityCS',
    'CSRaw',
]
