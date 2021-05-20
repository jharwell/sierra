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
"""
Classes and functions for computing the similarity between various temporal curves.
"""

# Core packages
import os
import typing as tp
import logging

# 3rd party packages
import fastdtw
import pandas as pd
import numpy as np
import similaritymeasures as sm

# Project packages
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
from sierra.core.variables.temporal_variance_parser import TemporalVarianceParser
from sierra.core.variables.temporal_variance import TemporalVariance


def method_xlabel(method: str) -> str:
    """
    Return the X-label of the method used for calculating the curve similarity.
    """
    labels = {
        "pcm": "Partial Curve Mapping Distance To Ideal Conditions",
        "area_between": "Area Difference For Experiment and Ideal Conditions Variance Curves",
        "frechet": "Experiment Frechet Distance To Ideal Conditions",
        "curve_length": "Curve Length Difference To Ideal Conditions",
        "dtw": r'DTW($I_{{ec}}(t)$,$V_{{ec}}(t)$)'
    }
    return labels[method]


def method_ylabel(method: str, arg: tp.Any) -> str:
    """
    Return the Y-label of the method used for calculating the curve similarity.

    method: Method name.
    arg: An additional multi-purpose argument to pass to the function
    """
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
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num
        self.main_config = main_config

    def __call__(self,
                 criteria: TemporalVariance,
                 exp_dirs: tp.Optional[tp.List[str]] = None) -> float:
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              criteria,
                                              exp_dirs,
                                              self.main_config['perf']['intra_tv_environment_csv'],
                                              0)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             criteria,
                                             exp_dirs,
                                             self.main_config['perf']['intra_tv_environment_csv'],
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
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any]) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config

    def from_batch(self, ideal_perf_df: pd.DataFrame, expx_perf_df: pd.DataFrame) -> float:

        xlen = len(expx_perf_df.index)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = expx_perf_df.index
        exp_data[:, 1] = expx_perf_df.values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_perf_df.index
        ideal_data[:, 1] = ideal_perf_df.values

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       method=self.cmdopts["rperf_cs_method"],
                       normalize=self.cmdopts['pm_flexibility_normalize'],
                       normalize_method=self.cmdopts['pm_normalize_method'])


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
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 criteria: TemporalVariance) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        self.main_config = main_config

        self.perf_csv_col = main_config['perf']['intra_perf_col']
        self.var_csv_col = TemporalVarianceParser()(self.criteria.cli_arg)['variance_csv_col']
        self.perf_leaf = self.main_config['perf']['intra_perf_csv'].split('.')[0]
        self.tv_env_leaf = self.main_config['perf']['intra_tv_environment_csv'].split('.')[0]

    def from_batch(self,
                   ideal_num: int,
                   ideal_perf_df: pd.DataFrame,
                   expx_perf_df: pd.DataFrame,
                   exp_dirs: tp.Optional[tp.List[str]] = None) -> float:
        ideal_data, exp_data = self._waveforms_from_batch(ideal_num,
                                                          ideal_perf_df,
                                                          expx_perf_df,
                                                          exp_dirs)

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       method=self.cmdopts["adaptability_cs_method"],
                       normalize=self.cmdopts['pm_flexibility_normalize'],
                       normalize_method=self.cmdopts['pm_normalize_method'])

    def waveforms_for_example_plots(self,
                                    ideal_num: int,
                                    exp_num: int,
                                    exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:
        # This function was called for generating plots, and we can safely operate on averaged
        # performance data.
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.perf_leaf +
                                                sierra.core.config.kStatsExtensions['mean'],
                                                ideal_num)

        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.criteria,
                                               exp_dirs,
                                               self.perf_leaf +
                                               sierra.core.config.kStatsExtensions['mean'],
                                               exp_num)

        return self._calc_waveforms(ideal_num, ideal_perf_df, expx_perf_df, exp_dirs)

    def _waveforms_from_batch(self,
                              ideal_num: int,
                              ideal_perf_df: pd.DataFrame,
                              expx_perf_df: pd.DataFrame,
                              exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:

        return self._calc_waveforms(ideal_num, ideal_perf_df, expx_perf_df, exp_dirs)

    def _calc_waveforms(self,
                        ideal_num: int,
                        ideal_perf_df: pd.DataFrame,
                        expx_perf_df: pd.DataFrame,
                        exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """

        # Variance can always be read from the averaged outputs, because the same variance was
        # applied to all simulations.
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              self.criteria,
                                              exp_dirs,
                                              self.tv_env_leaf +
                                              sierra.core.config.kStatsExtensions['mean'],
                                              ideal_num)

        ideal_df = pd.DataFrame(index=ideal_var_df.index, columns=[self.perf_csv_col])

        # The performance curve of an adaptable system should resist all changes in the
        # environment, and be the same as exp0
        ideal_df = ideal_perf_df

        xlen = len(ideal_var_df[self.var_csv_col].values)

        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = ideal_var_df['clock'].values
        exp_data[:, 1] = expx_perf_df.values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_var_df['clock'].values
        ideal_data[:, 1] = ideal_df.values
        return ideal_data, exp_data


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
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 criteria: TemporalVariance,
                 ideal_num: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.criteria = criteria
        self.ideal_num = ideal_num
        self.exp_num = exp_num

        self.perf_csv_col = self.main_config['perf']['intra_perf_col']
        self.var_csv_col = TemporalVarianceParser()(criteria.cli_arg)['variance_csv_col']
        self.perf_leaf = self.main_config['perf']['intra_perf_csv'].split('.')[0]
        self.tv_env_leaf = self.main_config['perf']['intra_tv_environment_csv'].split('.')[0]

    def from_batch(self,
                   ideal_perf_df: pd.DataFrame,
                   expx_perf_df: pd.DataFrame,
                   exp_dirs: tp.Optional[tp.List[str]] = None) -> float:
        ideal_data, exp_data = self._waveforms_from_batch(ideal_perf_df,
                                                          expx_perf_df,
                                                          exp_dirs)

        return CSRaw()(exp_data=exp_data,
                       ideal_data=ideal_data,
                       method=self.cmdopts["reactivity_cs_method"],
                       normalize=self.cmdopts['pm_flexibility_normalize'],
                       normalize_method=self.cmdopts['pm_normalize_method'])

    def waveforms_for_example_plots(self,
                                    exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:
        # This function was called for generating plots, and we can safely operate on averaged
        # performance data.
        ideal_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                                self.criteria,
                                                exp_dirs,
                                                self.perf_leaf +
                                                sierra.core.config.kStatsExtensions['mean'],
                                                self.ideal_num)

        expx_perf_df = DataFrames.expx_perf_df(self.cmdopts,
                                               self.criteria,
                                               exp_dirs,
                                               self.perf_leaf +
                                               sierra.core.config.kStatsExtensions['mean'],
                                               self.exp_num)

        return self._calc_waveforms(ideal_perf_df[self.perf_csv_col],
                                    expx_perf_df[self.perf_csv_col],
                                    exp_dirs)

    def _waveforms_from_batch(self,
                              ideal_perf_df: pd.DataFrame,
                              expx_perf_df: pd.DataFrame,
                              exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:

        return self._calc_waveforms(ideal_perf_df, expx_perf_df, exp_dirs)

    def _calc_waveforms(self,
                        ideal_perf_df: pd.DataFrame,
                        expx_perf_df: pd.DataFrame,
                        exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.Tuple[np.ndarray, np.ndarray]:
        """
        Calculates the (ideal performance, experimental performance) comparable waveforms for the
        experiment. Returns NP arrays rather than dataframes, because that is what the curve
        similarity measure calculator needs as input.
        """

        # Variance can always be read from the averaged outputs, because the same variance was
        # applied to all simulations.
        ideal_var_df = DataFrames.expx_var_df(self.cmdopts,
                                              self.criteria,
                                              exp_dirs,
                                              self.tv_env_leaf +
                                              sierra.core.config.kStatsExtensions['mean'],
                                              self.ideal_num)
        expx_var_df = DataFrames.expx_var_df(self.cmdopts,
                                             self.criteria,
                                             exp_dirs,
                                             self.tv_env_leaf +
                                             sierra.core.config.kStatsExtensions['mean'],
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
        for i in ideal_perf_df.index:
            ideal_var = ideal_var_df.loc[i, self.var_csv_col]
            expx_var = expx_var_df.loc[i, self.var_csv_col]
            ideal_perf = ideal_perf_df.iloc[i]

            scale_factor = self.criteria.calc_reactivity_scaling(ideal_var, expx_var)

            ideal_df.loc[i, self.perf_csv_col] = ideal_perf * scale_factor

        xlen = len(ideal_var_df[self.var_csv_col].values)
        exp_data = np.zeros((xlen, 2))
        exp_data[:, 0] = ideal_var_df['clock'].values
        exp_data[:, 1] = expx_perf_df.iloc[:].values

        ideal_data = np.zeros((xlen, 2))
        ideal_data[:, 0] = ideal_var_df['clock'].values
        ideal_data[:, 1] = ideal_df.loc[:, self.perf_csv_col].values

        return ideal_data, exp_data


class CSRaw():
    """
    Given two array-like objects representing ideal and non-ideal (experimental) conditions and a
    method for comparison, perform the comparison.
    """

    def __call__(self,
                 exp_data: np.ndarray,
                 ideal_data: np.ndarray,
                 method: str,
                 normalize: tp.Optional[bool] = False,
                 normalize_method: tp.Optional[str] = None) -> float:
        assert method is not None, "FATAL: Cannot compare curves without method"

        if method == "pcm":
            return sm.pcm(exp_data, ideal_data)  # type: ignore
        elif method == "area_between":
            return sm.area_between_two_curves(exp_data, ideal_data)  # type: ignore
        elif method == "frechet":
            return sm.frechet_dist(exp_data, ideal_data)  # type: ignore
        elif method == "dtw":
            return CSRaw._calc_dtw(exp_data, ideal_data, normalize, normalize_method)
        elif method == "curve_length":
            return sm.curve_length_measure(exp_data, ideal_data)  # type: ignore
        else:
            assert False, "Bad method {0}".format(method)

    @staticmethod
    def _calc_dtw(exp_data,
                  ideal_data,
                  normalize: tp.Optional[bool],
                  normalize_method: tp.Optional[str]) -> float:
        # Don't use the sm version--waaayyyy too slow
        dist, _ = fastdtw.fastdtw(exp_data, ideal_data)

        if normalize is None or not normalize:
            # You can't normalize [0,infinity) into [0,1], where HIGHER values now are better (even
            # if it is more intuitive this way), because the maxval can be different for different
            # controllers, resulting in apples to oranges comparisons in stage 5.
            return dist  # type: ignore
        else:
            if normalize_method == 'sigmoid':
                # Lower distance is better, so invert the usual sigmoid signs to normalize into
                # [-1,1], where higher values are better.
                return sierra.core.utils.Sigmoid(-dist)() - sierra.core.utils.Sigmoid(dist)()
            raise NotImplementedError


class DataFrames:
    @staticmethod
    def expx_var_df(cmdopts: tp.Dict[str, tp.Any],
                    criteria: TemporalVariance,
                    exp_dirs: tp.Optional[tp.List[str]],
                    tv_environment_csv: str,
                    exp_num: int) -> pd.DataFrame:
        if exp_dirs is None:
            dirs = criteria.gen_exp_dirnames(cmdopts)
        else:
            dirs = exp_dirs

        path = os.path.join(cmdopts['batch_stat_root'],
                            dirs[exp_num],
                            tv_environment_csv)
        try:
            return sierra.core.utils.pd_csv_read(path)
        except (FileNotFoundError, IndexError):
            logging.fatal("%s does not exist for exp num %s",
                          path,
                          exp_num)

    @staticmethod
    def expx_perf_df(cmdopts: tp.Dict[str, tp.Any],
                     criteria: TemporalVariance,
                     exp_dirs: tp.Optional[tp.List[str]],
                     intra_perf_csv: str,
                     exp_num: int) -> pd.DataFrame:
        if exp_dirs is None:
            dirs = criteria.gen_exp_dirnames(cmdopts)
        else:
            dirs = exp_dirs

        path = os.path.join(cmdopts['batch_stat_root'],
                            dirs[exp_num],
                            intra_perf_csv)
        try:
            return sierra.core.utils.pd_csv_read(path)
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
