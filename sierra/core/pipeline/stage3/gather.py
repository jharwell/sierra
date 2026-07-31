# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for gathering :term:`Raw Output Data`  files in a batch.
"""

# Core packages
import re
import dataclasses
import queue
import typing as tp
import time
import datetime
import logging
import pathlib

# 3rd party packages
import psutil
import polars as pl

# Project packages
from sierra.core import types, utils, storage


@dataclasses.dataclass(frozen=True)
class GatherSource:
    """One source file contributing to a gathered item.

    A source names a single file (relative to the run output root, to support
    nested outputs) and, optionally, a selection+renaming of columns to pull
    from it.

    Attributes:

        item_stem_path: The file to gather from each run, relative to the run
                        output root.

        col_map: A mapping ``{source_col: output_col}`` selecting the columns to
                 pull from this file and the names to expose them under. When
                 empty/``None`` (e.g.,the statistics and imagize case), the
                 whole file is used unchanged. ``source_col == output_col``
                 means "no rename"; a differing ``output_col`` is how same-named
                 columns from different files are disambiguated (see
                 :class:`GatherSpec`). Stored as a tuple of pairs so the source
                 is hashable/picklable across the multiprocessing queue.

    """

    item_stem_path: pathlib.Path
    col_map: tp.Optional[tuple[tuple[str, str], ...]] = None

    def as_col_map(self) -> tp.Optional[dict[str, str]]:
        """Return the column map as a dict, or ``None`` for whole-file sources."""
        if self.col_map is None:
            return None
        return dict(self.col_map)


class GatherSpec:
    """Data class for specifying files to gather from an :term:`Experiment`.

    A spec names one *or more* source files whose (selected, possibly renamed)
    columns are joined horizontally into a single logical table per
    :term:`Experimental Run`.  The single-source case is a spec whose
    ``sources`` tuple has length 1 and is the common case: statistics/imagize
    plugins always use it, and collation uses it whenever a target draws from
    one file.

    Attributes:

        exp_name: The name of the parent experiment.

        sources: The source files to gather and join per run.  Length 1 is the
                 common case; length > 1 pulls columns from different files into
                 one table.

        collate_col: The (output) column to extract during collation, named in
                     the joined table's post-rename column space.  ``None`` for
                     statistics generation; non-``None`` for collation.

        output_stem: Optional output identity for collation. When set (collation
                     with an explicit target), it names the collated output
                     independent of any single source filename -- required for
                     multi-source targets, where there is no single file stem.
                     ``None`` for statistics/imagize.

    """

    def __init__(
        self,
        exp_name: str,
        sources: tp.Sequence[GatherSource],
        collate_col: tp.Union[str, None] = None,
        output_stem: tp.Union[str, None] = None,
    ):
        assert len(sources) >= 1, "GatherSpec requires at least one source"
        self.exp_name = exp_name
        self.sources = tuple(sources)
        self.collate_col = collate_col
        self.output_stem = output_stem

    @property
    def is_single_source(self) -> bool:
        return len(self.sources) == 1

    @property
    def primary_stem_path(self) -> pathlib.Path:
        """The sole source's path.

        For single-source specs (statistics, imagize, and single-file
        collation) this is the natural "the file this spec is about" accessor.
        Asserts single-source so that a consumer which does not understand
        multi-source specs fails loudly rather than silently ignoring extra
        sources.
        """
        assert self.is_single_source, (
            "primary_stem_path is only meaningful for single-source specs; "
            f"this spec has {len(self.sources)} sources"
        )
        return self.sources[0].item_stem_path

    def __hash__(self) -> int:
        return hash((self.exp_name, self.sources, self.collate_col, self.output_stem))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GatherSpec):
            return NotImplemented
        return (
            self.exp_name == other.exp_name
            and self.sources == other.sources
            and self.collate_col == other.collate_col
            and self.output_stem == other.output_stem
        )

    def __repr__(self) -> str:
        paths = ", ".join(str(s.item_stem_path) for s in self.sources)
        return f"{self.exp_name}: [{paths}]"


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
        self.dfs = []  # type: tp.List[pl.DataFrame]


def file_matches(
    configured: str, item: pathlib.Path, proj_output_root: pathlib.Path
) -> bool:
    """Whether an output file matches a configured name.

    Shared resolution rule for the proc plugins (collation's ``file`` and
    statistics' graph ``src_stem``): matching is exact against the file's path
    *relative to the run output root*, not a substring of its name or path.
    Consequences:

    - A bare name (``output1D``) is resolved relative to the output root, so it
      matches ``<output_root>/output1D.csv`` and *not* a same-named file nested
      in a subdirectory. What a config entry resolves to therefore does not
      depend on how deep the output tree happens to be.

    - A nested file is named by path-qualifying the value
      (``subdir1/subdir2/output1D``); this is the explicit way to name one of
      several same-named files in different directories.

    - The configured value may be written with or without the storage extension
      (both ``blocks-collected.csv`` and ``output1D`` are accepted); the file's
      final suffix is stripped before comparison.

    A configured value matching more than one eligible file is an ambiguous
    specification; callers treat that as a hard error rather than silently fan
    out. (The only way exact matching produces multiple matches is a stem shared
    across two supported storage extensions, e.g. ``output1D.csv`` and
    ``output1D.tsv``.)
    """
    rel_str = str(item.relative_to(proj_output_root))
    rel_no_ext = rel_str[: -len(item.suffix)] if item.suffix else rel_str
    return configured in (rel_str, rel_no_ext)


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
        processq: queue.Queue,
    ) -> None:
        self.processq = processq
        self.gather_opts = gather_opts

        # Will get the main name and extension of the config file (without the
        # full absolute path).
        self.template_input_fname = self.gather_opts["template_input_leaf"]
        self.main_config = main_config

        self.run_output_leaf = types.MainConfig.from_yaml(
            main_config
        ).sierra.run.output_leaf

        self.logger = logging.getLogger(__name__)

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[GatherSpec]:
        raise NotImplementedError

    def inspect_materialized_df(self, df: pl.DataFrame, spec: GatherSpec) -> None:
        """Inspect a materialized DataFrame.

        Mostly intended to enable derived classes to issue warnings if e.g.,
        non-numeric columns are present and the intended df usage involves
        numeric calculations.

        """

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
                    [str(s.item_stem_path) for s in spec.sources],
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
            df = self._read_and_combine_sources(exp_output_root, spec, run)

            # A run contributes only if *all* of the spec's sources were present
            # and non-empty for it; a partial multi-source table cannot be
            # correctly joined.  ``None`` signals "skip this run".
            if df is None:
                continue

            # Allow derived classes to look at the final dataframe, to emit
            # warnings/errors to help with triage and debugging when stuff
            # doesn't work.
            self.inspect_materialized_df(df, spec)

            # Indices here must match so that the appropriate data from each
            # run are matched with the name of the run in collated
            # performance data.
            to_process.exp_run_names.append(run.name)
            to_process.dfs.append(df)

        return to_process

    def _read_and_combine_sources(
        self,
        exp_output_root: pathlib.Path,
        spec: GatherSpec,
        run: pathlib.Path,
    ) -> tp.Optional[pl.DataFrame]:
        """Read and horizontally combine one run's source files into one table.

        Returns ``None`` if any required source is missing or empty for this run
        (the run is then skipped, matching the pre-existing behavior where a
        missing file simply meant the run did not contribute).

        For a single-source spec this returns the source DataFrame *unchanged*
        (subject only to explicit column selection/renaming) -- the combine step
        is a no-op at length 1.

        """
        per_source_dfs = []  # type: tp.List[pl.DataFrame]

        for source in spec.sources:
            path = run / self.run_output_leaf / source.item_stem_path
            if not (path.exists() and path.stat().st_size > 0):
                return None

            df = storage.df_read(
                path,
                str(self.gather_opts["storage"]),
                run_output_root=run,
            )

            # Apply per-source column selection + rename, if configured. Whole
            # file (col_map is None) is left exactly as read.
            col_map = source.as_col_map()
            if col_map is not None:
                missing = [c for c in col_map if c not in df.columns]
                assert not missing, (
                    f"Configured column(s) {missing} not found in "
                    f"{path.relative_to(exp_output_root)}; present: {df.columns}"
                )
                df = df.select(list(col_map.keys())).rename(col_map)

            per_source_dfs.append(df)

        return self._combine_run_sources(per_source_dfs, spec)

    def _combine_run_sources(
        self,
        per_source_dfs: list[pl.DataFrame],
        spec: GatherSpec,
    ) -> pl.DataFrame:
        """Combine one run's per-source DataFrames into a single table.

        INVARIANT: for a single source this returns that DataFrame untouched --
        no rename, no reorder, no copy semantics change. Everything that could
        alter data lives strictly below the length-1 early return.
        """
        if len(per_source_dfs) == 1:
            return per_source_dfs[0]

        # Multi-source only from here down.
        #
        # Guard the alignment that _verify_exp_outputs_pairwise does NOT check:
        # it only compares same-named files across runs, never file A against
        # file B. A horizontal join of differently-sized sources would otherwise
        # misalign rows (or raise an opaque polars shape error), so make it loud.
        heights = {df.height for df in per_source_dfs}
        assert len(heights) == 1, (
            f"Cross-file row count mismatch while gathering {spec!r}: "
            f"source heights={sorted(heights)}. Sources joined horizontally "
            "must share a row axis (same number of rows, row i meaning the same "
            "thing in each file)."
        )

        # Any post-rename column-name collision across sources is an
        # *unresolved* collision: the researcher has the tools (per-source column
        # renaming) to disambiguate and did not. Fail loudly rather than let
        # polars silently suffix, which would make output column names depend on
        # source order.
        seen = {}  # type: tp.Dict[str, pathlib.Path]
        for df, source in zip(per_source_dfs, spec.sources):
            for col in df.columns:
                if col in seen:
                    raise ValueError(
                        f"Unresolved column collision in {spec!r}: column "
                        f"'{col}' is contributed by both "
                        f"{seen[col]} and {source.item_stem_path}. Rename one "
                        "via the per-source column mapping (e.g. `as:`) in the "
                        "collation config."
                    )
                seen[col] = source.item_stem_path

        return pl.concat(per_source_dfs, how="horizontal")

    def _wait_for_memory(self) -> None:
        while True:
            mem = psutil.virtual_memory()
            avail = mem.available / mem.total
            free_percent = avail * 100
            free_limit = 100 - int(self.gather_opts["processing_mem_limit"])

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
            csv_root1 = exp1 / str(self.run_output_leaf)

            for exp2 in experiments:
                csv_root2 = exp2 / self.run_output_leaf

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
            df1 = storage.df_read(path1, str(self.gather_opts["storage"]))
            df2 = storage.df_read(path2, str(self.gather_opts["storage"]))

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


__all__ = [
    "BaseGatherer",
    "GatherSource",
    "GatherSpec",
    "ProcessSpec",
    "file_matches",
]
