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
import math
import copy
import utils


class ProjectivePerformance:
    """
    Calculates the following measure for each experiment in a batch (N does not have to be a power
    of 2):

    Performance(exp i)
    --------------------
    Distance(exp i, exp 0) * Performance(exp 0)

    Domain: [0, inf)

    If things are X amount better/worse (in terms of increasing/decreasing the swarm's potential for
    performance) than they were for exp0 (baseline for comparison), then we *should* see a
    corresponding increase/decrease in the level of observed performance.

    Only valid for exp i, i > 0 (you are comparing with a projected performance value of exp0 after
    all).
    """

    def __init__(self, cmdopts, blocks_collected_csv, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def calculate(self, batch_criteria):
        path = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]
        scale_cols = [c for c in df.columns if c not in ['clock', exp0_dirname]]
        df_new = pd.DataFrame(columns=scale_cols, index=[0])

        self.cmdopts["n_exp"] = len(df.columns)
        xvals = batch_criteria.graph_xvals(self.cmdopts)

        for exp_num in range(1, len(scale_cols) + 1):
            exp_col = batch_criteria.gen_exp_dirnames(self.cmdopts)[exp_num]
            exp_prev_col = batch_criteria.gen_exp_dirnames(self.cmdopts)[exp_num - 1]
            similarity = float(xvals[exp_num]) / float(xvals[exp_num - 1])

            if "positive" == self.projection_type:
                df_new[exp_col] = ProjectivePerformance._calc_positive(df.tail(1)[exp_col].values[0],
                                                                       df.tail(1)[
                    exp_prev_col].values[0],
                    similarity)
            elif "negative" == self.projection_type:
                df_new[exp_col] = ProjectivePerformance._calc_negative(df.tail(1)[exp_col].values[0],
                                                                       df.tail(1)[
                    exp_prev_col].values[0],
                    similarity)
        return df_new

    def _calc_positive(observed, exp0, similarity):
        return observed / (exp0 * similarity)

    def _calc_negative(observed, exp0, similarity):
        return observed / (exp0 * (1.0 - similarity))


class FractionalLosses:
    """
    Calculates the fractional performance losses of a swarm across a range of swarm sizes (i.e. how
    much performance is maintained as the swarm size increases). The swarm sizes are assumed to be
    powers of 2.
    """

    def __init__(self, cmdopts, blocks_collected_csv, ca_in_csv, batch_criteria):
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]
        self.ca_in_stem = ca_in_csv.split('.')[0]

        # Just need to get # timesteps per simulation which is the same for all
        # simulations/experiments, so we pick exp0 for simplicity to calculate
        exp_def = utils.unpickle_exp_def(os.path.join(cmdopts["generation_root"],
                                                      batch_criteria.gen_exp_dirnames(
            self.cmdopts)[0],
            "exp_def.pkl"))

        # Integers always seem to be pickled as floats, so you can't convert directly without an
        # exception.
        for e in exp_def:
            if './/experiment' == e[0] and 'length' == e[1]:
                length = int(float(e[2]))
            elif './/experiment' == e[0] and 'ticks_per_second' == e[1]:
                ticks = int(float(e[2]))
        self.duration = length * ticks

    def calc(self, batch_criteria):
        """Returns the calculated fractional performance losses for the experiment."""

        # First calculate the time lost per timestep for a swarm of size N due to collision
        # avoidance interference
        path = os.path.join(self.batch_output_root, self.ca_in_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]
        scale_cols = [c for c in df.columns if c not in ['clock', exp0_dirname]]
        all_cols = [c for c in df.columns if c not in ['clock']]
        tlost_n = pd.DataFrame(columns=all_cols, data=df.tail(1))

        # Next get the performance lost per timestep, calculated as:
        #
        # cum blocks gathered * tlost_1
        #
        # for exp0 and as
        #
        # cum blocks gathered * (tlost_N - N * tlost_1) / N
        #
        # This gives how much MORE performance was lost in the entire simulation as a result of a
        # swarm of size N, as opposed to a group of N robots that do not interact with each other,
        # only the arena walls.
        #
        path = os.path.join(self.batch_output_root, self.blocks_collected_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        blocks = pd.read_csv(path, sep=';')

        plost_n = pd.DataFrame(columns=scale_cols)
        plost_n[exp0_dirname] = blocks.tail(1)[exp0_dirname] * (tlost_n[exp0_dirname])

        for c in [c for c in scale_cols]:
            if blocks.tail(1)[c].values[0] == 0:
                plost_n[c] = math.inf
            else:
                plost_n[c] = blocks.tail(1)[c] * \
                    (tlost_n[c] - tlost_n[exp0_dirname] * math.pow(2, batch_criteria.exp_dir2num(self.cmdopts, c)) /
                     math.pow(2, batch_criteria.exp_dir2num(self.cmdopts, c)))

        # Finally, calculate fractional losses as:
        #
        # ( performance lost with N robots / performance with N robots )
        path = os.path.join(self.batch_output_root, self.blocks_collected_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_n = pd.read_csv(path, sep=';').tail(1)
        perf_n.tail(1)[exp0_dirname] = 0.0

        df = pd.DataFrame(columns=scale_cols)

        for c in scale_cols:
            if (perf_n[c] == 0).any():
                df[c] = 1.0
            else:
                df[c] = round(plost_n[c] / perf_n[c], 4)

        # By definition, no fractional losses with 1 robot
        df.insert(0, exp0_dirname, 0.0)
        return df


class WeightUnifiedEstimate:
    """
    Calculates a single number for each controller in the input .csv representing its scalability
    across all experiments in the batch (i.e. on the same scenario) using the following equation:
        1
    -------------  * SUM(scalability experiment i * log(swarm size for experiment i))
    # experiments

    Assumes that the swarm sizes are a power of 2.
    """

    def __init__(self, input_csv_fpath, swarm_sizes):
        self.input_csv_fpath = input_csv_fpath
        self.swarm_sizes = swarm_sizes

    def calc(self):
        df = pd.read_csv(self.input_csv_fpath, sep=';')
        val = 0
        for i in range(0, len(df.columns)):
            val += df.iloc[0, i] * math.log2(self.swarm_sizes[i])
        val = val / float(len(self.swarm_sizes))

        return val
