# Copyright 2019 John Harwell, All rights reserved.
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

"""
Classes for collating data from all :term:`Simulation` across all :term:`Experiment` for all
experiments in a :term:`Batch Experiment`. This is needed to correctly calculate summary statistics
for performance measures in stage 4: you can't just run the calculated stddev through the
calculations for flexibility (for example) because comparing curves of stddev is not
meaningful. Stage 4 needs access to raw-(er) simulation data to construct a `distribution` of
performance measure values to then calculate the summary statistics (such as stddev) over.
"""

# Core packages
import os
import multiprocessing as mp
import typing as tp
import queue
import logging

# 3rd party packages
import pandas as pd

# Project packages
import core.utils
import core.variables.batch_criteria as bc
import core.config


class SimulationParallelCollator:
    """
    Gathers .csv output files from each simulation in each experiment for calculating performance
    measures in stage 4 in parallel.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, tp.Any]):
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        if self.cmdopts['serial_processing']:
            n_gatherers = 1
            n_processors = 1
        else:
            n_gatherers = int(mp.cpu_count() * 0.25)
            n_processors = int(mp.cpu_count() * 0.75)

        pool = mp.Pool(processes=n_gatherers + n_processors)

        m = mp.Manager()
        gatherq = m.Queue()
        processq = m.Queue()

        for exp in os.listdir(self.cmdopts['batch_output_root']):
            gatherq.put((self.cmdopts['batch_output_root'], exp))

        for _ in range(0, n_gatherers):
            pool.apply_async(SimulationParallelCollator._gather_worker,
                             (gatherq,
                              processq,
                              self.main_config))

        for _ in range(0, n_processors):
            pool.apply_async(SimulationParallelCollator._process_worker,
                             (processq,
                              self.main_config,
                              self.cmdopts['batch_stat_collate_root']))
        pool.close()
        pool.join()

    @staticmethod
    def _gather_worker(gatherq: mp.Queue,
                       processq: mp.Queue,
                       main_config: dict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                batch_output_root, exp = gatherq.get(True, 3)
                SimulationCSVGatherer(main_config, batch_output_root, exp, processq)()
                gatherq.task_done()

            except queue.Empty:
                break

    @staticmethod
    def _process_worker(processq: mp.Queue,
                        main_config: dict,
                        batch_stat_pm_root: str) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                item = processq.get(True, 3)

                exp_leaf = list(item.keys())[0]
                gathered_sims, gathered_dfs = item[exp_leaf]
                SimulationCollator(main_config,
                                   batch_stat_pm_root,
                                   exp_leaf,
                                   gathered_sims,
                                   gathered_dfs)()
                processq.task_done()
            except queue.Empty:
                break


class SimulationCSVGatherer:
    """
    Gather necessary :term:`Output .csv` files all :term:`Simulations<Simulation>` within a
    single :term:`Experiment` so that performance measures can be generated during stage 4.
    """

    def __init__(self,
                 main_config: dict,
                 batch_output_root: str,
                 exp_leaf: str,
                 processq: mp.Queue) -> None:
        self.processq = processq

        self.exp_leaf = exp_leaf
        self.exp_output_root = os.path.join(batch_output_root, exp_leaf)
        self.main_config = main_config

        self.sim_metrics_leaf = main_config['sim']['sim_metrics_leaf']

        self.logger = logging.getLogger(__name__)

    def __call__(self):
        self.logger.info('Gathering .csvs: %s...', self.exp_leaf)

        simulations = sorted(os.listdir(self.exp_output_root))

        gathered = []
        for sim in simulations:
            gathered.append(self._gather_csvs_from_sim(sim))

        self.processq.put({self.exp_leaf: (simulations, gathered)})

    def _gather_csvs_from_sim(self, sim: str) -> tp.Dict[tp.Tuple[str, str], pd.DataFrame]:
        intra_perf_leaf = self.main_config['perf']['intra_perf_csv'].split('.')[0]
        intra_interference_leaf = self.main_config['perf']['intra_interference_csv'].split('.')[0]

        intra_perf_col = self.main_config['perf']['intra_perf_col']
        intra_interference_col = self.main_config['perf']['intra_interference_col']

        sim_output_root = os.path.join(self.exp_output_root, sim, self.sim_metrics_leaf)

        perf_df = core.utils.pd_csv_read(os.path.join(sim_output_root, intra_perf_leaf + '.csv'),
                                         index_col=False)

        interference_df = core.utils.pd_csv_read(os.path.join(sim_output_root,
                                                              intra_interference_leaf + '.csv'),
                                                 index_col=False)

        return {
            (intra_perf_leaf, intra_perf_col): perf_df[intra_perf_col],
            (intra_interference_leaf, intra_interference_col): interference_df[intra_interference_col]
        }


class SimulationCollator:
    """Collate gathered .csvs together gathered from N simulations together into a single .csv per
    experiment with 1 column per simulation
    """

    def __init__(self,
                 main_config: dict,
                 batch_stat_collate_root: str,
                 exp_leaf: str,
                 gathered_sims: tp.List[str],
                 gathered_dfs: tp.List[tp.Dict[tp.Tuple[str, str], pd.DataFrame]]) -> None:
        self.exp_leaf = exp_leaf
        self.gathered_sims = gathered_sims
        self.gathered_dfs = gathered_dfs

        self.main_config = main_config
        self.batch_stat_collate_root = batch_stat_collate_root

        # To support inverted performance measures where smaller is better
        self.invert_perf = main_config['perf']['inverted']
        self.intra_perf_csv = main_config['perf']['intra_perf_csv']

        core.utils.dir_create_checked(self.batch_stat_collate_root, exist_ok=True)

    def __call__(self):
        collated = {}

        for sim in self.gathered_sims:
            sim_dfs = self.gathered_dfs[self.gathered_sims.index(sim)]
            for csv_leaf, col in sim_dfs.keys():
                csv_df = sim_dfs[(csv_leaf, col)]
                if self.invert_perf and csv_leaf in self.intra_perf_csv:
                    csv_df = 1.0 / csv_df

                if (csv_leaf, col) not in collated:
                    collated[(csv_leaf, col)] = pd.DataFrame(index=csv_df.index,
                                                             columns=self.gathered_sims)
                collated[(csv_leaf, col)][sim] = csv_df

        for (csv_leaf, col) in collated.keys():

            core.utils.pd_csv_write(collated[(csv_leaf, col)],
                                    os.path.join(self.batch_stat_collate_root,
                                                 self.exp_leaf + '-' + csv_leaf + '-' + col + '.csv'),
                                    index=False)
