# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for gathering :term:`Experimental Run Data`  files in a batch.
"""

# Core packages
import re
import multiprocessing as mp
import typing as tp
import time
import datetime
import logging
import pathlib

# 3rd party packages
import pandas as pd
import psutil

# Project packages
from sierra.core import types, utils, storage
import sierra.core.plugin_manager as pm


class GatherSpec:
    """
    Data class for specifying files to gather from an :term:`Experiment`.
    """

    def __init__(self,
                 exp_name: str,
                 path: pathlib.Path):
        self.exp_name = exp_name
        self.path = path

    def __repr__(self) -> str:
        return f"{self.exp_name}: {self.path}"


class BaseGatherer:
    """Gather a set of output files from all runs in an experiment.

    "Gathering" in this context means creating a dictionary mapping which files
    came from where, so that later processing can be both across and within
    experiments in the batch.
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 gather_opts: tp.Dict[str, str],
                 processq: mp.Queue) -> None:
        self.processq = processq
        self.gather_opts = gather_opts

        # Will get the main name and extension of the config file (without the
        # full absolute path).
        self.template_input_fname = self.gather_opts['template_input_leaf']

        self.main_config = main_config

        self.run_metrics_leaf = main_config['sierra']['run']['run_metrics_leaf']

        self.logger = logging.getLogger(__name__)

    def __call__(self, exp_output_root: pathlib.Path) -> None:
        """Process the output files found in the output save path."""
        if not self.gather_opts['df_skip_verify']:
            self._verify_exp_outputs(exp_output_root)

        self.logger.info('Gathering raw outputs from %s...', exp_output_root.name)

        pattern = "{}_run{}_output".format(re.escape(self.gather_opts['template_input_leaf']),
                                           r'\d+')

        runs = list(exp_output_root.iterdir())
        assert (all(re.match(pattern, r.name) for r in runs)), \
            f"Extra files/not all dirs in '{exp_output_root}' are exp runs"

        # Maps (unique stem, optional parent dir) to the averaged dataframe
        to_gather = self.calc_gather_items(runs[0], exp_output_root.name)

        for item in to_gather:
            self._wait_for_memory()
            gathered = self._gather_item_from_sims(exp_output_root, item, runs)

            # Put gathered .csv list  in the process queue
            self.processq.put(gathered)

        self.logger.debug("Enqueued %s items from %s for processing",
                          len(to_gather),
                          exp_output_root.name)

    def _gather_item_from_sims(self,
                               exp_output_root: pathlib.Path,
                               item: GatherSpec,
                               runs: tp.List[pathlib.Path]) -> tp.Dict[GatherSpec,
                                                                       tp.List[pd.DataFrame]]:
        gathered = {}  # type: tp.Dict[GatherSpec, pd.DataFrame]

        for run in runs:
            reader = storage.DataFrameReader(self.gather_opts['storage'])
            df = reader(item.path, index_col=False)

            # 2025-05-02 [JRH]: This column dropping is in here temporarily to
            # enable me to process data from starling. It will be removed before
            # merging to devel.

            # if df.dtypes.iloc[0] == 'object':
            # df[df.columns[0]] = df[df.columns[0]].apply(lambda x: float(x))
            for c in df.columns:
                df[c] = df[c].replace(r'(m|rad|°)', '', regex=True)

            cols = df.select_dtypes(include='object').columns.tolist()
            df = df.drop(cols, axis=1)

            if item not in gathered:
                gathered[item] = []

            gathered[item].append(df)

        return gathered

    def _wait_for_memory(self) -> None:
        while True:
            mem = psutil.virtual_memory()
            avail = mem.available / mem.total
            free_percent = avail * 100
            free_limit = 100 - self.gather_opts['processing_mem_limit']

            if free_percent >= free_limit:
                return

            self.logger.info("Waiting for memory: avail=%s,min=%s",
                             free_percent,
                             free_limit)
            time.sleep(1)

    def _verify_exp_outputs(self, exp_output_root: pathlib.Path) -> None:
        """
        Verify the integrity of all runs in an experiment.

        Specifically:

        - All runs produced all CSV files.

        - All runs CSV files with the same name have the same # rows and
          columns.

        - No CSV files contain NaNs.
        """
        experiments = exp_output_root.iterdir()

        self.logger.info('Verifying results in %s...', str(exp_output_root))

        start = time.time()

        for exp1 in experiments:
            csv_root1 = exp1 / self.run_metrics_leaf

            for exp2 in experiments:
                csv_root2 = exp2 / self.run_metrics_leaf

                if not csv_root2.is_dir():
                    continue

                self._verify_exp_outputs_pairwise(csv_root1, csv_root2)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Done verifying results in %s: %s",
                         exp_output_root,
                         sec)

    def _verify_exp_outputs_pairwise(self,
                                     csv_root1: pathlib.Path,
                                     csv_root2: pathlib.Path) -> None:
        for csv in csv_root2.iterdir():
            path1 = csv
            path2 = csv_root2 / csv.name

            # .csvs for rendering that we don't verify
            if path1.is_dir() or path2.is_dir():
                self.logger.debug("Not verifying '%s': contains data for imagizing",
                                  str(path1))
                continue

            assert (utils.path_exists(path1) and utils.path_exists(path2)), \
                f"Either {path1} or {path2} does not exist"

            # Verify both dataframes have same # columns, and that
            # column sets are identical
            reader = storage.DataFrameReader(self.gather_opts['storage'])
            df1 = reader(path1)
            df2 = reader(path2)

            assert (len(df1.columns) == len(df2.columns)), \
                (f"Dataframes from {path1} and {path2} do not have "
                 "the same # columns")
            assert (sorted(df1.columns) == sorted(df2.columns)), \
                f"Columns from {path1} and {path2} not identical"

            # Verify the length of all columns in both dataframes is the same
            for c1 in df1.columns:
                assert (all(len(df1[c1]) == len(df1[c2]) for c2 in df1.columns)), \
                    f"Not all columns from {path1} have same length"

                assert (all(len(df1[c1]) == len(df2[c2]) for c2 in df1.columns)), \
                    (f"Not all columns from {path1} and {path2} have "
                     "the same length")


class DataGatherer(BaseGatherer):
    """Gather :term:`Experimental Run Data` files from all runs.

    The configured output directory for each run is searched recursively for
    files to gather.  To be eligible for gathering and later processing, files
    must:

        - Be non-empty

        - Have a suffix which supported by the selected ``--storage`` plugin.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def calc_gather_items(self,
                          run_output_root: pathlib.Path,
                          exp_name: str) -> tp.List[GatherSpec]:
        to_gather = []
        sim_output_root = run_output_root / self.run_metrics_leaf
        storage = pm.pipeline.get_plugin_module(self.gather_opts['storage'])

        for item in sim_output_root.rglob("*"):
            if item.is_file() and any([s in storage.suffixes() for s in
                                       item.suffixes]) and item.stat().st_size > 0:
                to_gather.append(GatherSpec(exp_name=exp_name,
                                            path=item))
        return to_gather


class ImagizeInputGatherer(BaseGatherer):
    """Gather :term:`Experimental Run Data` files from all runs for imagizing.

    The configured output directory for each run is searched recursively for
    directories containing files to gather.  To be eligible for gathering and
    later processing, files must:

        - Be in a directory with the same name as the file, sans extension.

        - Be non-empty

        - Have a suffix which supported by the selected ``--storage`` plugin.

    Recursive nesting of files *within* a directory containing files to imagize
    is not supported--why would you do this anyway?
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 gather_opts: tp.Dict[str, str],
                 processq: mp.Queue) -> None:
        super().__init__(main_config, gather_opts, processq)
        self.logger = logging.getLogger(__name__)

    def calc_gather_items(self,
                          run_output_root: pathlib.Path,
                          exp_name: str) -> tp.List[GatherSpec]:
        to_gather = []
        run_output_root = run_output_root / self.run_metrics_leaf
        storage = pm.pipeline.get_plugin_module(self.gather_opts['storage'])

        for item in run_output_root.iterdir():
            if not item.is_dir():
                self.logger.debug(("Skip <run_output_root>/'%s' for imagizing "
                                   "gather: files must be in subdir"),
                                  item.name,
                                  item.relative_to(run_output_root))
                continue

            for imagizable in item.iterdir():
                if not imagizable.is_file():
                    self.logger.debug(("Skip subdir '%s/' of "
                                       "<run_output_root>/'%s' for imagizing "
                                       "gather: recursion not supported"),
                                      imagizable.name,
                                      imagizeable.relative_to(run_output_root))
                    continue

                if not any([s in storage.suffixes() for s in
                            imagizable.suffixes]) and imagizable.stat().st_size > 0:
                    continue

                if imagizable.name == item.name:
                    to_gather.append(GatherSpec(exp_name=exp_name, path=item))

        return to_gather


__all__ = [
    'GatherSpec',
    'BaseGatherer',
    'DataGatherer',
    'ImagizeInputGatherer'
]
