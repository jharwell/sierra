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
import math
import copy
import numpy as np
import pandas as pd
import utils
from variables.swarm_size import SwarmSize


class ProjectivePerformanceCalculatorUnivar:

    # Calculates the following measure for each experiment in a univariate batched experiment:
    #
    # .. math::
    #     \frac{Performance(exp i)}{Distance(exp i, exp i-1) * Performance(exp i)}
    #
    # Domain: [0, inf)
    #
    # If things are X amount better/worse (in terms of increasing/decreasing the swarm's potential for
    # performance) than they were for exp0 (baseline for comparison), then we *should* see a
    # corresponding increase/decrease in the level of observed performance.
    #
    # Only valid for exp i, i > 0 (you are comparing with a projected performance value of exp0 after
    # all).


    def __init__(self, cmdopts, inter_perf_csv, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def __call__(self, batch_criteria):
        path = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_df = pd.read_csv(path, sep=';')
        exp_dirs = batch_criteria.gen_exp_dirnames(self.cmdopts)
        exp0_dir = exp_dirs[0]
        scale_cols = [c for c in perf_df.columns if c not in [exp0_dir]]
        proj_df = pd.DataFrame(columns=scale_cols, index=[0])

        xvals = batch_criteria.graph_xticks(self.cmdopts)

        for exp_num in range(1, len(scale_cols) + 1):
            exp_col = exp_dirs[exp_num]
            exp_prev_col = exp_dirs[exp_num - 1]

            obs = perf_df.tail(1)[exp_col].values[0]
            obs_prev = perf_df.tail(1)[exp_prev_col].values[0]
            similarity = float(xvals[exp_num]) / float(xvals[exp_num - 1])

            if self.projection_type == 'positive':
                proj_df[exp_col] = ProjectivePerformanceCalculatorUnivar.__calc_positive(obs,
                                                                                         obs_prev,
                                                                                         similarity)
            elif self.projection_type == 'negative':
                proj_df[exp_col] = ProjectivePerformanceCalculatorUnivar.__calc_negative(obs,
                                                                                         obs_prev,
                                                                                         similarity)
        return proj_df

    @staticmethod
    def __calc_positive(observed, exp0, similarity):
        return observed / (exp0 * similarity)

    @staticmethod
    def __calc_negative(observed, exp0, similarity):
        return observed / (exp0 * (1.0 - similarity))


class ProjectivePerformanceCalculatorBivar:

    # Calculates the following measure for each experiment in a bivariate batched experiment. One of
    # the variables must be swarm size.
    #
    # .. math::
    #     \frac{Performance(exp i)}{Distance(exp i, exp i-1) * Performance(exp i)}
    #
    # Domain: [0, inf)
    #
    # If things are X amount better/worse (in terms of increasing/decreasing the swarm's potential for
    # performance) than they were for exp0 (baseline for comparison), then we *should* see a
    # corresponding increase/decrease in the level of observed performance.
    #
    # Only valid for exp i, i > 0 (you are comparing with a projected performance value of exp0 after
    # all).


    def __init__(self, cmdopts, inter_perf_csv, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def __call__(self, batch_criteria):
        path = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_df = pd.read_csv(path, sep=';')

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        if isinstance(batch_criteria.criteria1, SwarmSize):
            return self.__project_vals_row(perf_df, batch_criteria)
        else:
            return self.__project_vals_col(perf_df, batch_criteria)

    def __project_vals_col(self, perf_df, batch_criteria):
        proj_df = pd.DataFrame(columns=perf_df.columns[1:], index=perf_df.index)
        yvals = batch_criteria.graph_yticks(self.cmdopts)

        for i in range(0, len(proj_df.index)):
            for j in range(0, len(proj_df.columns)):
                similarity = float(yvals[j]) / float(yvals[j - 1])
                obs = csv_3D_value_iloc(perf_df, i, j, slice(-1, None))
                prev_obs = csv_3D_value_iloc(perf_df, i, j - 1, slice(-1, None))

                if self.projection_type == 'positive':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_positive(obs,
                                                                                              prev_obs,
                                                                                              similarity)
                elif self.projection_type == 'negative':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_negative(obs,
                                                                                              prev_obs,
                                                                                              similarity)
        return proj_df

    def __project_vals_row(self, perf_df, batch_criteria):
        proj_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index[1:])
        xvals = batch_criteria.graph_xticks(self.cmdopts)

        for i in range(0, len(proj_df.index)):
            for j in range(0, len(proj_df.columns)):
                similarity = float(xvals[i]) / float(xvals[i - 1])
                obs = csv_3D_value_iloc(perf_df, i, j, slice(-1, None))
                prev_obs = csv_3D_value_iloc(perf_df, i - 1, j, slice(-1, None))

                if self.projection_type == 'positive':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_positive(obs,
                                                                                              prev_obs,
                                                                                              similarity)
                elif self.projection_type == 'negative':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_negative(obs,
                                                                                              prev_obs,
                                                                                              similarity)

        return proj_df

    @staticmethod
    def __calc_positive(obs, prev_obs, similarity):
        return obs / (prev_obs * similarity)

    @staticmethod
    def __calc_negative(obs, prev_obs, similarity):
        return obs / (prev_obs * (1.0 - similarity))


class FractionalLosses:

    # Calculates the fractional performance losses of a swarm across a range of swarm sizes (i.e. how
    # much performance is maintained as the swarm size increases) in a batched
    # experiment. The swarm sizes are assumed to be powers of 2.


    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv, batch_criteria):
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.ca_in_stem = ca_in_csv.split('.')[0]

        # Just need to get # timesteps per simulation which is the same for all
        # simulations/experiments, so we pick exp0 for simplicity to calculate
        exp_def = utils.unpickle_exp_def(os.path.join(cmdopts["generation_root"],
                                                      batch_criteria.gen_exp_dirnames(
                                                          self.cmdopts)[0],
                                                      "exp_def.pkl"))

        # Integers always seem to be pickled as floats, so you can't convert directly without an
        # exception.
        for path, attr, value in exp_def:
            if path == './/experiment' and attr == 'length':
                length = int(float(value))
            elif path == './/experiment'and attr == 'ticks_per_second':
                ticks = int(float(value))
        self.duration = length * ticks


class FractionalLossesUnivar(FractionalLosses):

    # Calculates the percentage of performance which is lost with N interacting robots vs. N
    # independently acting robots which do not interfer with each other. Does not require  the
    # variable to be swarm size, but the metric will (probably) not be of much value if that is not
    # the case.


    def calculate(self, batch_criteria):
        ca_in_path = os.path.join(self.batch_output_root, self.ca_in_stem + '.csv')
        assert(os.path.exists(ca_in_path)), "FATAL: {0} does not exist".format(ca_in_path)
        ca_in_df = pd.read_csv(ca_in_path, sep=';')

        calc_stddev = True
        ca_in_path_stddev = os.path.join(self.batch_output_root, self.ca_in_stem + '.stddev')
        ca_in_df_stddev = None
        if (os.path.exists(ca_in_path_stddev)):
            ca_in_df_stddev = pd.read_csv(ca_in_path_stddev, sep=';')
        else:
            calc_stddev = False

        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        #print(perf_path)
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        perf_path_stddev = os.path.join(self.batch_output_root, self.inter_perf_stem + '.stddev')
        perf_df_stddev = None
        if (os.path.exists(perf_path_stddev) and calc_stddev):
            perf_df_stddev = pd.read_csv(perf_path_stddev, sep=';')
        else:
            calc_stddev = False

        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]
        scale_cols = [c for c in ca_in_df.columns if c not in [exp0_dirname]]


        # Calculate plost for all swarm sizes
        plost_n = FractionalLossesUnivar.__calc_plost_n(ca_in_df, perf_df, batch_criteria)
        plost_n_stddev = None
        if calc_stddev:
            plost_n_stddev = FractionalLossesUnivar.__calc_plost_n(ca_in_df_stddev, perf_df_stddev, batch_criteria)
        #print(scale_cols_stddev, exp0_dirname)

        # Calculate fractional losses for al swarm sizes
        fl_df = FractionalLossesUnivar.__calc_fl(perf_df, plost_n, scale_cols)
        fl_df_stddev = None
        if calc_stddev:
            fl_df_stddev = FractionalLossesUnivar.__calc_fl(perf_df_stddev, plost_n_stddev, scale_cols)

        # By definition, no fractional losses with 1 robot, or any stddev
        #print("CA IN DF:", ca_in_df)
        #print("CA IN STDDEV DF:", ca_in_df_stddev)
        fl_df.insert(0, exp0_dirname, 0.0)
        fl_df_stddev.insert(0, exp0_dirname, 0.0)
        #print(fl_df,fl_df_stddev)
        return fl_df, fl_df_stddev, calc_stddev

    @staticmethod
    def __calc_plost_n(ca_in_df, perf_df, batch_criteria):

    #    Calculated as follows for all swarm sizes N in the batch:

        #cum blocks gathered * tlost_1 (for exp0)

        # Calculated as follows for all swarm sizes N in the batch:
        #
        # cum blocks gathered * tlost_1 (for exp0)
        #
        # cum blocks gathered * (tlost_N - N * tlost_1) / N (else)
        #
        # This gives how much MORE performance was lost in the entire simulation as a result of a
        # swarm of size N, as opposed to a group of N robots that do not interact with each other,
        # only the arena walls.

        plost_n = pd.DataFrame(columns=perf_df.columns)
        exp0_dir = perf_df.columns[0]
        scale_cols = [c for c in ca_in_df.columns if c not in [exp0_dir]]

        plost_n[exp0_dir] = perf_df.tail(1)[exp0_dir] * (ca_in_df.tail(1)[exp0_dir])

        for c in [c for c in scale_cols]:
            n_robots = math.pow(2, list(plost_n.columns).index(c))

            if perf_df.tail(1)[c].values[0] == 0:
                plost_n[c] = math.inf
            else:
                plost_n[c] = perf_df.tail(1)[c] * (ca_in_df.tail(1)[c] -
                                                   ca_in_df.tail(1)[exp0_dir] * n_robots) / n_robots
        return plost_n

    @staticmethod
    def __calc_fl(perf_df, plost_n, scale_cols):

        #Calculate fractional losses as:


        fl_df = pd.DataFrame(columns=scale_cols,index=[0])
        for c in scale_cols:
            # print("COL:", c)
            # print((perf_df.tail(1)[c] == 0.0).any())
            #fl_df.loc[0,c] = 1.0
            if (perf_df.tail(1)[c] == 0).any(axis=None):
                fl_df.loc[0,c] = 1.0
            else:
                val = (plost_n[c] / perf_df.tail(1)[c]).values[0]
            #    if val != 0:
                fl_df.loc[0,c] = val
                #print(val)
                #print("CULPRIT:",perf_df)
            #print(fl_df)
        return fl_df


class FractionalLossesBivar(FractionalLosses):

    # Calculates the percentage of performance which is lost with N interacting robots vs. N
    # independently acting robots which do not interfer with each other. Does not require one of the
    # variables to be swarm size, but the metric will (probably) not be of much value if that is not
    # the case.


    def calculate(self, batch_criteria):
        ca_in_path = os.path.join(self.batch_output_root, self.ca_in_stem + '.csv')
        assert(os.path.exists(ca_in_path)), "FATAL: {0} does not exist".format(ca_in_path)
        ca_in_df = pd.read_csv(ca_in_path, sep=';')

        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        # Calculate plost for all swarm sizes
        plost_n = self.__calc_plost_n(ca_in_df, perf_df, batch_criteria)

        # Calculate fractional losses for al swarm sizes
        fl_df = self.__calc_fl(perf_df, plost_n)

        return fl_df

    def __calc_plost_n(self, ca_in_df, perf_df, batch_criteria):

        # Calculated as follows for all swarm sizes N in the batch:
        #
        # cum blocks gathered * tlost_1 (for exp0)
        #
        # cum blocks gathered * (tlost_N - N * tlost_1) / N (else)
        #
        # This gives how much MORE performance was lost in the entire simulation as a result of a
        # swarm of size N, as opposed to a group of N robots that do not interact with each other,
        # only the arena walls.

        plost_n = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]

        # Calc for exp(0,0)
        t_lost0 = csv_3D_value_loc(ca_in_df,
                                   0,  # exp0 = 1 robot
                                   exp0_dir,
                                   slice(-1, None))  # Last in temporal seq = cum avg
        perf0 = csv_3D_value_loc(perf_df,
                                 0,  # exp0 = 1 robot
                                 exp0_dir,
                                 slice(-1, None))  # Last in temporal seq = cum count

        plost_n.iloc[0, 0] = float(perf0) * float(t_lost0)

        # Calc for general case
        for i in range(0, len(plost_n.index)):
            for j in range(0, len(plost_n.columns)):
                if i == 0 and plost_n.columns[j] == exp0_dir:  # exp(0,0)
                    continue

                n_blocks = csv_3D_value_iloc(perf_df,
                                             i,
                                             j,
                                             slice(-1, None))

                if 0 == n_blocks:
                    plost_n.iloc[i, j] = math.inf
                else:
                    t_lostN = csv_3D_value_iloc(ca_in_df,
                                                # Last row = N robots
                                                len(ca_in_df.index) - 1,
                                                j,
                                                slice(-1, None))  # Last in temporal seq = cum avg

                    # We need to know which of the 2 variables was swarm size, in order to determine
                    # the correct dimension along which to compute the metric, which depends on
                    # performance between adjacent swarm sizes.
                    if isinstance(batch_criteria.criteria1, SwarmSize):
                        n_robots = math.pow(2, i)
                    else:
                        n_robots = math.pow(2, j)

                    plost_n.iloc[i, j] = n_blocks * \
                        (t_lostN - t_lost0 * float(n_robots)) / float(n_robots)
        return plost_n

    def __calc_fl(self, perf_df, plost_n):

        # Calculate fractional losses as:
        #
        # (performance lost with N robots / performance with N robots )


        fl_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]

        for i in range(0, len(fl_df.index)):
            for c in fl_df.columns:
                if i == 0 and c == exp0_dir:  # exp(0,0)
                    fl_df.loc[i, c] = 0.0  # By definition, no fractional losses in exp(0,0)
                    continue

                perf_N = csv_3D_value_loc(perf_df, i, c, slice(-1, None))
                if 0 == perf_N:
                    fl_df.loc[i, c] = 1.0
                else:
                    fl_df.loc[i, c] = round(plost_n.loc[i, c] / perf_N, 4)
        return fl_df


def csv_3D_value_loc(df, xslice, ycol, zslice):
    # When collated, the column of data is written as a numpy array to string, so we
    # have to reparse it as an actual array
    arr = np.fromstring(df.loc[xslice, ycol][1:-1], dtype=np.float, sep=' ')
    # The second index is an artifact of how numpy represents scalars (1 element arrays).
    return arr[zslice][0]


def csv_3D_value_iloc(df, xslice, yslice, zslice):
    # When collated, the column of data is written as a numpy array to string, so we
    # have to reparse it as an actual array
    arr = np.fromstring(df.iloc[xslice, yslice][1:-1], dtype=np.float, sep=' ')
    # The second index is an artifact of how numpy represents scalars (1 element arrays).
    return arr[zslice][0]
