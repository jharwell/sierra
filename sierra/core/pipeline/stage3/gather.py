# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for gathering :term:`Raw Output Data`  files in a batch.
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
import psutil
import pandas as pd

# Project packages
from sierra.core import types, utils, storage


class GatherSpec:
    """
    Data class for specifying files to gather from an :term:`Experiment`.

    Attributes:
        item_stem_path: The name of the file to gather from all runs in an
                        experiment, relative to the output root for the run (to
                        support nested outputs).

         exp_name: The name of the parent experiment.


         collate-col: The name of the column associated with the file, as
                      configured. Will be None for statistics generation, and
                      non-None for collation.
    """

    def __init__(
        self,
        exp_name: str,
        item_stem_path: pathlib.Path,
        collate_col: tp.Union[str, None],
    ):
        self.exp_name = exp_name
        self.item_stem_path = item_stem_path
        self.collate_col = collate_col

    def __repr__(self) -> str:
        return f"{self.exp_name}: {self.item_stem_path}"


class ProcessSpec:
    """
    Data class for specifying how to Process :term:`Raw Output Files`.

    Attributes:
        gather_spec: The specification for how the files were gathered.

        exp_run_names: The names of the parent experimental runs.

        dfs: The gathered dataframes. Indices match those in ``exp_run_names``.

    """

    def __init__(self, gather: GatherSpec) -> None:
        self.gather = gather
        self.exp_run_names = []  # type: tp.List[str]
        self.dfs = []  # type: tp.List[pd.DataFrame]


class BaseGatherer:
    """Gather a set of output files from all runs in an experiment.

    "Gathering" in this context means creating a dictionary mapping which files
    came from where, so that later processing can be both across and within
    experiments in the batch.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        gather_opts: types.SimpleDict,
        processq: mp.Queue,
    ) -> None:
        self.processq = processq
        self.gather_opts = gather_opts

        # Will get the main name and extension of the config file (without the
        # full absolute path).
        self.template_input_fname = self.gather_opts["template_input_leaf"]
        self.main_config = main_config
        self.run_metrics_leaf = main_config["sierra"]["run"]["run_metrics_leaf"]

        self.logger = logging.getLogger(__name__)

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[GatherSpec]:
        raise NotImplementedError

    def __call__(self, exp_output_root: pathlib.Path) -> None:
        """Process the output files found in the output save path."""
        if self.gather_opts["df_verify"]:
            self._verify_exp_outputs(exp_output_root)

        self.logger.info(
            "Gathering raw outputs from %s...",
            exp_output_root.relative_to(exp_output_root.parent.parent),
        )

        pattern = "{}_run{}_output".format(
            re.escape(str(self.gather_opts["template_input_leaf"])), r"\d+"
        )

        runs = list(exp_output_root.iterdir())
        assert all(re.match(pattern, r.name) for r in runs), (
            f"Extra files/not all dirs in '{exp_output_root}' are exp "
            "run output dirs"
        )

        to_gather = []
        for run in runs:
            from_run = self.calc_gather_items(run, exp_output_root.name)
            self.logger.trace(
                "Calculated %s items from %s for gathering", len(from_run), run.name
            )
            to_gather.extend(from_run)
        self.logger.trace("Gathering all items...")

        for spec in to_gather:
            self._wait_for_memory()
            to_process = self._gather_item_from_runs(exp_output_root, spec, runs)
            n_gathered_from = len(to_process.dfs)
            if n_gathered_from != len(runs):
                self.logger.warning(
                    (
                        "Data not gathered for %s from all experimental runs "
                        "in %s: %s runs != %s (--n-runs)"
                    ),
                    spec.item_stem_path,
                    exp_output_root.relative_to(exp_output_root.parent.parent),
                    n_gathered_from,
                    len(runs),
                )

            # Put gathered files in the process queue
            self.processq.put(to_process)

        self.logger.debug(
            "Enqueued %s items from %s for processing",
            len(to_gather),
            exp_output_root.name,
        )

    def _gather_item_from_runs(
        self,
        exp_output_root: pathlib.Path,
        spec: GatherSpec,
        runs: list[pathlib.Path],
    ) -> ProcessSpec:
        to_process = ProcessSpec(gather=spec)

        for _, run in enumerate(runs):
            path = run / self.run_metrics_leaf / spec.item_stem_path
            if path.exists() and path.stat().st_size > 0:
                df = storage.df_read(
                    path,
                    self.gather_opts["storage"],
                    run_output_root=run,
                    index_col=False,
                )
                if nonumeric := df.select_dtypes(exclude="number").columns.tolist():
                    self.logger.warning(
                        "Non-numeric columns only support mean aggregation via mode(): %s from %s",
                        nonumeric,
                        path.relative_to(exp_output_root),
                    )

                # Indices here must match so that the appropriate data from each
                # run are matched with the name of the run in collated
                # performance data.
                to_process.exp_run_names.append(run.name)
                to_process.dfs.append(df)

        return to_process

    def _wait_for_memory(self) -> None:
        while True:
            mem = psutil.virtual_memory()
            avail = mem.available / mem.total
            free_percent = avail * 100
            free_limit = 100 - self.gather_opts["processing_mem_limit"]

            if free_percent >= free_limit:
                return

            self.logger.info(
                "Waiting for memory: avail=%s%%,min=%s%%", free_percent, free_limit
            )
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

        self.logger.info("Verifying results in %s...", exp_output_root.name)

        start = time.time()

        for exp1 in experiments:
            csv_root1 = exp1 / str(self.run_metrics_leaf)

            for exp2 in experiments:
                csv_root2 = exp2 / self.run_metrics_leaf

                if not csv_root2.is_dir():
                    continue

                self._verify_exp_outputs_pairwise(exp_output_root, csv_root1, csv_root2)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info(
            "Done verifying results in <batch_output_root>/%s: %s",
            exp_output_root.name,
            sec,
        )

    def _verify_exp_outputs_pairwise(
        self,
        exp_output_root: pathlib.Path,
        ofile_root1: pathlib.Path,
        ofile_root2: pathlib.Path,
    ) -> None:
        for ofile in ofile_root1.rglob("*"):
            path1 = ofile
            path2 = ofile_root2 / ofile.name

            # If either path is a directory, that directory MIGHT container
            # imagizing data. We use the following heuristic:
            #
            # If the directory only contains files AND all the files have the
            # same extension AND all the files contain the directory name, we
            # conclude that the directory contains imagizing data and skip it.
            #
            # Otherwise, check it, as projects/engines can output their data in
            # a directory tree, and we want to verify that.
            if (
                path1.is_dir()
                and path2.is_dir()
                and all(f.is_file() and path1.name in f.name for f in path1.iterdir())
                and all(f.is_file() and path2.name in f.name for f in path2.iterdir())
            ):
                self.logger.debug(
                    (
                        "Not verifying {<exp_output_root>/%s,<exp_output_root>/%s} pairwise: "
                        "contains data for imagizing"
                    ),
                    path1.relative_to(exp_output_root),
                    path2.relative_to(exp_output_root),
                )
                continue

            if path1.is_dir() or path2.is_dir():
                continue

            if path1.parent.name in path1.name or path2.parent.name in path2.name:
                self.logger.trace(
                    (
                        "Not verifying {<exp_output_root>/%s,<exp_output_root>/%s} pairwise: "
                        "imagizing data"
                    ),
                    path1.relative_to(exp_output_root),
                    path2.relative_to(exp_output_root),
                )
                continue

            assert utils.path_exists(path1) and utils.path_exists(
                path2
            ), f"Either {path1} or {path2} does not exist"

            # Verify both dataframes have same # columns, and that
            # column sets are identical
            df1 = storage.df_read(path1, self.gather_opts["storage"])
            df2 = storage.df_read(path2, self.gather_opts["storage"])

            assert len(df1.columns) == len(
                df2.columns
            ), f"Dataframes from {path1} and {path2} do not have the same # columns"
            assert sorted(df1.columns) == sorted(
                df2.columns
            ), f"Columns from {path1} and {path2} not identical"

            # Verify the length of all columns in both dataframes is the same
            for c1 in df1.columns:
                assert all(
                    len(df1[c1]) == len(df1[c2]) for c2 in df1.columns
                ), f"Not all columns from {path1} have same length"

                assert all(
                    len(df1[c1]) == len(df2[c2]) for c2 in df1.columns
                ), f"Not all columns from {path1} and {path2} have the same length"


__all__ = ["BaseGatherer", "GatherSpec"]
