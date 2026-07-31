#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for :mod:`sierra.plugins.proc.statistics.plugin` graph-driven file
resolution.

Statistics gathers a raw output file iff some graph in ``graphs.yaml`` names it.
These tests pin the resolution rule -- now shared with the collation plugin via
:func:`sierra.core.pipeline.stage3.gather.file_matches`: a graph ``src``
names exactly one file, rooted at the output root, path-qualified for nesting,
and does *not* substring-match. The former substring behavior silently gathered
every file whose path merely contained the stem (nested copies,
``output1D_extended``, ...).
"""

# Core packages

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.proc.statistics import plugin


@pytest.fixture
def make_run(tmp_path, monkeypatch):
    """Build a run output tree + a DataGatherer wired to a graphs.yaml config.

    Returns a factory: make_run(files, graphs_cfg) -> (gatherer, run, exp_name).
    """

    class _Plugin:
        @staticmethod
        def supports_output(_df):
            return True

        @staticmethod
        def supports_input(suffix):
            return suffix in (".csv", ".tsv")

    monkeypatch.setattr(
        plugin.pm.pipeline,
        "get_plugin_module",
        lambda *a, **k: _Plugin(),
        raising=False,
    )

    def _factory(files, graphs_cfg, exp_name="c1-exp0"):
        run = tmp_path / "run0"
        out = run / "output"
        out.mkdir(parents=True, exist_ok=True)
        for rel in files:
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("col1,col2\n1,3\n2,4\n")

        g = plugin.DataGatherer.__new__(plugin.DataGatherer)
        import logging

        logger = logging.getLogger("statistics_test")
        # sierra installs a custom TRACE level (logger.trace); stub it so the
        # gather loop's trace calls work under a plain stdlib logger.
        if not hasattr(logger, "trace"):
            logger.trace = lambda *a, **k: None
        g.logger = logger
        g.run_output_leaf = "output"
        g.gather_opts = {"storage": "csv"}
        g.config = graphs_cfg
        return g, run, exp_name

    return _factory


def _gathered(specs):
    return sorted(str(s.sources[0].item_stem_path) for s in specs)


def _graph(src, **over):
    base = {"src": src, "dest": "d", "type": "stacked_line"}
    base.update(over)
    return base


class TestStatisticsResolution:
    def test_bare_stem_matches_root_only(self, make_run):
        """'output1D' names the root file, not nested same-named copies."""
        g, run, exp = make_run(
            ["output1D.csv", "subdir1/subdir2/output1D.csv", "subdir3/output1D.csv"],
            {"intra-exp": {"cat": [_graph("output1D")]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == ["output1D.csv"]

    def test_path_qualified_stems_select_each_copy(self, make_run):
        """The real sample-project pattern: three path-qualified stems select
        exactly their three files, not a fan-out."""
        g, run, exp = make_run(
            ["output1D.csv", "subdir1/subdir2/output1D.csv", "subdir3/output1D.csv"],
            {
                "intra-exp": {
                    "cat": [
                        _graph("output1D"),
                        _graph("subdir1/subdir2/output1D"),
                        _graph("subdir3/output1D"),
                    ]
                }
            },
        )
        assert _gathered(g.calc_gather_items(run, exp)) == [
            "output1D.csv",
            "subdir1/subdir2/output1D.csv",
            "subdir3/output1D.csv",
        ]

    def test_multi_source_graph_gathers_all_its_sources(self, make_run):
        """A multi-source graph (sources: [...]) has no 'src'; statistics must
        gather every file named in its sources, not KeyError on 'src'.

        Regression: _cat_matches assumed g['src'] existed, which crashed on the
        multi-source graph spelling.
        """
        multi = {
            "dest": "combined-noise",
            "type": "stacked_line",
            "sources": [
                {
                    "file": "subdir3/output1D",
                    "cols": [{"name": "col1", "as": "nested-col1"}],
                },
                {
                    "file": "subdir1/subdir2/output1D",
                    "cols": [{"name": "col1", "as": "deep-nested-col1"}],
                },
            ],
        }
        g, run, exp = make_run(
            ["output1D.csv", "subdir1/subdir2/output1D.csv", "subdir3/output1D.csv"],
            {"intra-exp": {"cat": [multi]}},
        )
        # Both source files are gathered; the unreferenced root output1D is not.
        assert _gathered(g.calc_gather_items(run, exp)) == [
            "subdir1/subdir2/output1D.csv",
            "subdir3/output1D.csv",
        ]

    def test_mixed_single_and_multi_source_graphs(self, make_run):
        """Single-source and multi-source graphs coexisting in one config both
        contribute their files."""
        multi = {
            "dest": "combined",
            "type": "stacked_line",
            "sources": [{"file": "subdir3/output1D", "cols": ["col1"]}],
        }
        g, run, exp = make_run(
            ["output1D.csv", "subdir3/output1D.csv"],
            {"intra-exp": {"cat": [_graph("output1D"), multi]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == [
            "output1D.csv",
            "subdir3/output1D.csv",
        ]

    def test_no_substring_bleed(self, make_run):
        """'output1D' must not gather 'output1D_extended' or 'raw_output1D'."""
        g, run, exp = make_run(
            ["output1D.csv", "output1D_extended.csv", "raw_output1D.csv"],
            {"intra-exp": {"cat": [_graph("output1D")]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == ["output1D.csv"]

    def test_no_prefix_bleed(self, make_run):
        """A stem that is a prefix of another output must not match it:
        'output1' does not gather 'output1D'."""
        g, run, exp = make_run(
            ["output1.csv", "output1D.csv"],
            {"intra-exp": {"cat": [_graph("output1")]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == ["output1.csv"]

    def test_stem_matches_regardless_of_extension(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv"],
            {"intra-exp": {"cat": [_graph("output1D")]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == ["output1D.csv"]

    def test_unreferenced_file_not_gathered(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv", "output2D.csv"],
            {"intra-exp": {"cat": [_graph("output1D")]}},
        )
        assert _gathered(g.calc_gather_items(run, exp)) == ["output1D.csv"]

    def test_inter_and_intra_both_consulted(self, make_run):
        """A file named only by an inter-exp graph is still gathered."""
        g, run, exp = make_run(
            ["output1D.csv", "output2D.csv"],
            {
                "intra-exp": {"cat": [_graph("output1D")]},
                "inter-exp": {"cat": [_graph("output2D")]},
            },
        )
        assert _gathered(g.calc_gather_items(run, exp)) == [
            "output1D.csv",
            "output2D.csv",
        ]

    def test_one_spec_per_file_no_duplicate_from_multiple_graphs(self, make_run):
        """Two graphs naming the same file must not gather it twice."""
        g, run, exp = make_run(
            ["output1D.csv"],
            {
                "intra-exp": {"cat": [_graph("output1D")]},
                "inter-exp": {"cat": [_graph("output1D")]},
            },
        )
        specs = g.calc_gather_items(run, exp)
        assert _gathered(specs) == ["output1D.csv"]
        assert len(specs) == 1

    def test_matches_any_graph_reports_category(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv", "output2D.csv"],
            {
                "intra-exp": {"cat": [_graph("output1D")]},
                "inter-exp": {"cat": [_graph("output2D")]},
            },
        )
        root = run / "output"
        assert g._matches_any_graph(root / "output1D.csv", root) == "intra"
        assert g._matches_any_graph(root / "output2D.csv", root) == "inter"
        # A file named in both categories reports intra/inter.
        g.config = {
            "intra-exp": {"cat": [_graph("output1D")]},
            "inter-exp": {"cat": [_graph("output1D")]},
        }
        assert g._matches_any_graph(root / "output1D.csv", root) == "intra/inter"
        assert g._matches_any_graph(root / "output2D.csv", root) is None
