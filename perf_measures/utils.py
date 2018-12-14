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
import pickle

kCAInCumCSV = "ca-in-cum-avg.csv"
kBlocksGatheredCumCSV = "blocks-collected-cum.csv"


def prettify_scenario_labels(batch_criteria, scenarios):
    """
    batch_criteria(str): String of batch criteria passed on command line.
    scenarios(list): SORTED list of directories in sierra root representing the scenarios
    that each controller was tested on.

    Returns a sorted list of prettified labels suitable for scenario comparison graphs.

    """
    if "swarm_size" in batch_criteria:
        return [s[-4:] for s in scenarios]
    elif "swarm_density" in batch_criteria:
        return [s[-5:-2].replace('p', '.') for s in scenarios]


def sort_scenarios(batch_criteria, scenarios):
    """
    batch_criteria(str): String of batch criteria passed on command line.
    scenarios(list):  List of directories in sierra root representing the scenarios
    that each controller was tested on.

    Returns a sorted list of scenarios.

    """
    if "swarm_size" in batch_criteria:
        return scenarios  # No sorting needed
    elif "swarm_density" in batch_criteria:
        return sorted(scenarios, key=lambda s: float(s[-5:-2].replace('p', '.')))


def calc_swarm_sizes(batch_criteria, batch_generation_root, n_exp):
    """
    batch_criteria(str): String of batch criteria passed on command line.
    batch_generation_root(str): Root directory where experiment input files were generated.
    n_exp(int): How many experiments were run.
    """
    if "swarm_size" in batch_criteria:
        return [2**x for x in range(0, n_exp)]
    elif "swarm_density" in batch_criteria:
        sizes = []
        for i in range(0, n_exp):
            exp_def = unpickle_exp_def(os.path.join(
                batch_generation_root, "exp" + str(i), "exp_def.pkl"))
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))
        return sizes


def unpickle_exp_def(exp_def_fpath):
    """
    Read in all the different sets of parameter changes that were pickled to make
    crucial parts of the experiment definition easily accessible. I don't know how
    many there are, so go until you get an exception.
    """
    try:
        with open(exp_def_fpath, 'rb') as f:
            exp_def = set()
            while True:
                exp_def = exp_def | pickle.load(f)
    except EOFError:
        pass
    return exp_def


class FractionalLosses:
    """
    Calculates the fractional performance losses of a swarm across a range of swarm sizes (i.e. how
    much performance is maintained as the swarm size increases).
    """

    def __init__(self, batch_output_root, batch_generation_root):
        self.batch_output_root = batch_output_root

        exp_def = unpickle_exp_def(os.path.join(batch_generation_root, "exp0/exp_def.pkl"))

        # Integers always seem to be pickled as floats, so you can't convert directly without an
        # exception.
        for e in exp_def:
            if './/experiment' == e[0] and 'length' == e[1]:
                length = int(float(e[2]))
            elif './/experiment' == e[0] and 'ticks_per_second' == e[1]:
                ticks = int(float(e[2]))
        self.duration = length * ticks

    def calc(self):
        """Returns the calculated fractional performance losses for the experiment."""

        # First calculate the time lost per timestep for a swarm of size N due to collision
        # avoidance interference
        path = os.path.join(self.batch_output_root, kCAInCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        tlost_n = pd.DataFrame(columns=scale_cols, data=df.tail(1))

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
        path = os.path.join(self.batch_output_root, kBlocksGatheredCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        blocks = pd.read_csv(path, sep=';')

        plost_n = pd.DataFrame(columns=scale_cols)
        plost_n['exp0'] = blocks.tail(1)['exp0'] * (tlost_n['exp0'])

        for c in [c for c in scale_cols if c not in ['exp0']]:
            plost_n[c] = blocks.tail(1)[c] * \
                (tlost_n[c] - tlost_n['exp0'] * math.pow(2, int(c[3:]))) / \
                math.pow(2, int(c[3:]))

        # Finally, calculate fractional losses as:
        #
        # ( performance lost with N robots / performance with N robots )
        path = os.path.join(self.batch_output_root, kBlocksGatheredCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_n = pd.read_csv(path, sep=';').tail(1)

        df = pd.DataFrame(columns=scale_cols)
        for c in scale_cols:
            if (perf_n[c] == 0).any():
                df[c] = perf_n[c]
            else:
                df[c] = round(plost_n[c] / perf_n[c], 4)

        return df


class WeightUnifiedEstimate:
    """
    Calculates a single number for each controller in the input .csv representing its scalability
    across all experiments in the batch (i.e. on the same scenario) using the following equation:
        1
    -------------  * SUM(scalability experiment i * log(swarm size for experiment i))
    # experiments
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
