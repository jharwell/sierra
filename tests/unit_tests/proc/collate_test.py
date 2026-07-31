#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for :mod:`sierra.plugins.proc.collate` config validation and
output-file resolution.

These cover the multi-file collation functionality: the two config spellings
(single-source ``file:`` and multi-source ``sources:``), per-source column
selection and renaming, collision detection, and the exact-match-relative-to-
output-root file resolution (including ambiguity errors and the death of the
old substring-fan-out behavior).

Config validation is exercised through :func:`cconfig.validate`, which takes the
whole (flat, list-shaped) ``collate.yaml`` and reports *every* problem together
rather than raising on the first. ``collate.yaml`` has no section wrapper:
collation is intra-experiment only.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.proc.collate import plugin, cconfig
from sierra.core.pipeline.stage3 import gather
from sierra.core.yaml.validate import ConfigError


def _one(entry):
    """Validate a one-target config and return the single CollateTarget."""
    targets = cconfig.validate([entry])
    assert len(targets) == 1
    return targets[0]


# ---------------------------------------------------------------------------
# validate: single-source spelling
# ---------------------------------------------------------------------------
class TestSingleSource:
    def test_basic(self):
        t = _one({"file": "blocks-collected.csv", "cols": ["n_collected", "n_dropped"]})
        assert t.is_single_source
        assert t.sources[0].output_cols == ["n_collected", "n_dropped"]

    def test_name_defaults_to_file_stem(self):
        """A single-source target with no explicit name uses the file stem, so
        historical output filenames are preserved byte-for-byte."""
        t = _one({"file": "blocks-collected.csv", "cols": ["x"]})
        assert t.name == "blocks-collected"
        assert not t.name_explicit

    def test_name_without_extension(self):
        t = _one({"file": "output1D", "cols": ["x"]})
        assert t.name == "output1D"

    def test_explicit_name_recorded(self):
        t = _one({"file": "output1D", "name": "renamed", "cols": ["x"]})
        assert t.name == "renamed"
        assert t.name_explicit

    def test_bare_cols_are_no_rename(self):
        t = _one({"file": "f.csv", "cols": ["a", "b"]})
        assert t.sources[0].col_map == (("a", "a"), ("b", "b"))


# ---------------------------------------------------------------------------
# validate: multi-source spelling
# ---------------------------------------------------------------------------
class TestMultiSource:
    def test_basic(self):
        t = _one(
            {
                "name": "efficiency",
                "sources": [
                    {"file": "blocks-collected.csv", "cols": ["n_collected"]},
                    {
                        "file": "energy-used.csv",
                        "cols": [{"name": "count", "as": "energy_count"}],
                    },
                ],
            }
        )
        assert not t.is_single_source
        assert t.name == "efficiency"
        assert t.name_explicit
        assert len(t.sources) == 2

    def test_rename_applied(self):
        t = _one(
            {
                "name": "j",
                "sources": [
                    {"file": "a.csv", "cols": [{"name": "count", "as": "count_a"}]},
                ],
            }
        )
        assert t.sources[0].col_map == (("count", "count_a"),)
        assert t.sources[0].output_cols == ["count_a"]

    def test_as_defaults_to_name(self):
        """A mapping with 'name' but no 'as' means "keep the name"."""
        t = _one(
            {"name": "j", "sources": [{"file": "a.csv", "cols": [{"name": "x"}]}]}
        )
        assert t.sources[0].col_map == (("x", "x"),)


# ---------------------------------------------------------------------------
# validate: whole-file handling
# ---------------------------------------------------------------------------
class TestValidateWhole:
    def test_none_is_empty(self):
        assert cconfig.validate(None) == []

    def test_empty_list_is_empty(self):
        assert cconfig.validate([]) == []

    def test_multiple_targets(self):
        out = cconfig.validate(
            [
                {"file": "a.csv", "cols": ["x"]},
                {"file": "b.csv", "cols": ["y"]},
            ]
        )
        assert [t.name for t in out] == ["a", "b"]

    def test_non_list_top_level_rejected(self):
        # A mapping (e.g. the old section-wrapped shape) is no longer valid:
        # collate.yaml is a flat list of targets.
        with pytest.raises(ConfigError, match="expected a list"):
            cconfig.validate({"intra-exp": []})

    def test_error_message_names_collate_yaml(self):
        with pytest.raises(ConfigError, match="collate.yaml"):
            cconfig.validate([{"cols": ["x"]}])


# ---------------------------------------------------------------------------
# validate: collisions and malformed configs (single fault each)
# ---------------------------------------------------------------------------
class TestValidateErrors:
    def test_resolved_collision_ok(self):
        """Same source-column name from two files is fine once disambiguated
        with 'as'."""
        t = _one(
            {
                "name": "combo",
                "sources": [
                    {"file": "a.csv", "cols": [{"name": "count", "as": "count_a"}]},
                    {"file": "b.csv", "cols": [{"name": "count", "as": "count_b"}]},
                ],
            }
        )
        assert [s.output_cols for s in t.sources] == [["count_a"], ["count_b"]]

    def test_unresolved_collision_rejected(self):
        with pytest.raises(ConfigError, match="collision"):
            cconfig.validate(
                [
                    {
                        "name": "combo",
                        "sources": [
                            {"file": "a.csv", "cols": ["count"]},
                            {"file": "b.csv", "cols": ["count"]},
                        ],
                    }
                ]
            )

    def test_both_spellings_rejected(self):
        with pytest.raises(ConfigError, match="both"):
            cconfig.validate([{"file": "a.csv", "cols": ["x"], "sources": []}])

    def test_neither_spelling_rejected(self):
        with pytest.raises(ConfigError, match="either"):
            cconfig.validate([{"cols": ["x"]}])

    def test_multi_source_without_name_rejected(self):
        # 'sources' present but no 'name': fails the multi_source schema (name
        # is required there).
        with pytest.raises(ConfigError, match="name|non-conformant"):
            cconfig.validate([{"sources": [{"file": "a.csv", "cols": ["x"]}]}])

    def test_duplicate_col_within_source_rejected(self):
        with pytest.raises(ConfigError, match="[Dd]uplicate"):
            cconfig.validate([{"file": "a.csv", "cols": ["x", "x"]}])

    def test_source_missing_file_rejected(self):
        with pytest.raises(ConfigError, match="file|non-conformant"):
            cconfig.validate([{"name": "j", "sources": [{"cols": ["x"]}]}])

    def test_source_missing_cols_rejected(self):
        with pytest.raises(ConfigError, match="cols|non-conformant"):
            cconfig.validate([{"name": "j", "sources": [{"file": "a.csv"}]}])

    def test_unknown_key_rejected(self):
        """strictyaml's default strictness rejects unknown keys -- validation
        the old imperative normalizer did not do."""
        with pytest.raises(ConfigError, match="non-conformant|unexpected key"):
            cconfig.validate([{"file": "a.csv", "cols": ["x"], "bogus": 1}])


# ---------------------------------------------------------------------------
# validate: ALL problems reported together (the point of up-front validation)
# ---------------------------------------------------------------------------
class TestErrorAggregation:
    def test_all_faults_reported_together(self):
        with pytest.raises(ConfigError) as exc:
            cconfig.validate(
                [
                    {"file": "a.csv", "cols": ["x"], "sources": []},  # both
                    {"cols": ["x"]},  # neither
                    {"file": "b.csv", "cols": ["x", "x"]},  # dup cols
                    {
                        "name": "c",  # cross-source collision
                        "sources": [
                            {"file": "d.csv", "cols": ["k"]},
                            {"file": "e.csv", "cols": ["k"]},
                        ],
                    },
                ]
            )
        # Four independent faults -> four problems, not a first-failure abort.
        assert len(exc.value.problems) == 4

    def test_problem_locators_identify_entries(self):
        with pytest.raises(ConfigError) as exc:
            cconfig.validate(
                [
                    {"file": "ok.csv", "cols": ["x"]},  # valid
                    {"cols": ["x"]},  # invalid -> collate[1]
                ]
            )
        assert len(exc.value.problems) == 1
        assert "collate[1]" in exc.value.problems[0]


# ---------------------------------------------------------------------------
# _file_matches: exact match relative to output root
# ---------------------------------------------------------------------------
class TestFileMatches:
    ROOT = pathlib.Path("/out")

    def _item(self, rel):
        return self.ROOT / rel

    def test_bare_name_matches_root_file(self):
        assert plugin._file_matches("output1D", self._item("output1D.csv"), self.ROOT)

    def test_bare_name_does_not_match_nested(self):
        """The core anti-surprise rule: a bare name is rooted, so it does NOT
        reach into subdirectories."""
        assert not plugin._file_matches(
            "output1D", self._item("subdir1/subdir2/output1D.csv"), self.ROOT
        )

    def test_path_qualified_matches_nested(self):
        assert plugin._file_matches(
            "subdir1/subdir2/output1D",
            self._item("subdir1/subdir2/output1D.csv"),
            self.ROOT,
        )

    def test_extension_optional(self):
        assert plugin._file_matches(
            "output1D.csv", self._item("output1D.csv"), self.ROOT
        )
        assert plugin._file_matches(
            "output1D", self._item("output1D.csv"), self.ROOT
        )

    def test_no_substring_bleed(self):
        """The footgun that started all this: 'output1D' must NOT match
        'output1D_extended.csv'."""
        assert not plugin._file_matches(
            "output1D", self._item("output1D_extended.csv"), self.ROOT
        )
        assert not plugin._file_matches(
            "output1D", self._item("raw_output1D.csv"), self.ROOT
        )


# ---------------------------------------------------------------------------
# ExpDataGatherer._resolve_sources / calc_gather_items: resolution + ambiguity
#
# These drive the real gatherer against an on-disk output tree. df_read is never
# reached (resolution happens before any file is read), so no storage stubbing
# is needed.
# ---------------------------------------------------------------------------
@pytest.fixture
def make_run(tmp_path, monkeypatch):
    """Build a run output tree and a gatherer wired to a collate.yaml.

    Returns a factory: make_run(files, cfg) -> (gatherer, run_path, exp_name).
    """
    import yaml as _yaml

    class _Plugin:
        @staticmethod
        def supports_output(_df):
            return True

        @staticmethod
        def supports_input(suffix):
            return suffix in (".csv", ".tsv")

    # calc_gather_items resolves the storage plugin via
    # pm.pipeline.get_plugin_module; point it at our stub so any supported
    # extension is eligible and the pl.DataFrame support check passes.
    monkeypatch.setattr(
        plugin.pm.pipeline,
        "get_plugin_module",
        lambda *a, **k: _Plugin(),
        raising=False,
    )

    def _factory(files, cfg, exp_name="c1-exp0"):
        run = tmp_path / "run0"
        out = run / "output"
        out.mkdir(parents=True, exist_ok=True)
        for rel in files:
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("col1,col2\n1,3\n2,4\n")
        cfg_root = tmp_path / "config"
        cfg_root.mkdir(exist_ok=True)
        (cfg_root / "collate.yaml").write_text(_yaml.safe_dump(cfg))

        g = plugin.ExpDataGatherer.__new__(plugin.ExpDataGatherer)
        g.gather_opts = {
            "storage": "csv",
            "project_config_root": str(cfg_root),
            "template_input_leaf": "template",
        }
        g.run_output_leaf = "output"
        import logging

        g.logger = logging.getLogger("collate_test")
        return g, run, exp_name

    return _factory


def _matched_paths(specs):
    return sorted({str(s.sources[0].item_stem_path) for s in specs})


class TestResolution:
    def test_bare_name_root_only(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv", "subdir1/subdir2/output1D.csv"],
            [{"file": "output1D", "cols": ["col1"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert _matched_paths(specs) == ["output1D.csv"]
        assert len(specs) == 1

    def test_path_qualified_reaches_nested(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv", "subdir1/subdir2/output1D.csv"],
            [{"file": "subdir1/subdir2/output1D", "cols": ["col1"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert _matched_paths(specs) == ["subdir1/subdir2/output1D.csv"]
        assert specs[0].output_stem == "output1D"

    def test_no_substring_bleed(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv", "output1D_extended.csv", "raw_output1D.csv"],
            [{"file": "output1D", "cols": ["col1"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert _matched_paths(specs) == ["output1D.csv"]

    def test_extension_in_config(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv"],
            [{"file": "output1D.csv", "cols": ["col1"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert _matched_paths(specs) == ["output1D.csv"]

    def test_missing_file_contributes_nothing(self, make_run):
        g, run, exp = make_run(
            ["present.csv"],
            [{"file": "absent", "cols": ["col1"]}],
        )
        assert g.calc_gather_items(run, exp) == []

    def test_one_spec_per_output_column(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv"],
            [{"file": "output1D", "cols": ["col1", "col2"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert sorted(s.collate_col for s in specs) == ["col1", "col2"]
        assert all(s.output_stem == "output1D" for s in specs)

    def test_explicit_name_used_as_output_stem(self, make_run):
        g, run, exp = make_run(
            ["output1D.csv"],
            [{"file": "output1D", "name": "renamed", "cols": ["col1"]}],
        )
        specs = g.calc_gather_items(run, exp)
        assert specs[0].output_stem == "renamed"

    def test_ambiguous_bare_name_is_hard_error(self, make_run):
        """The only way exact-match ambiguity arises: a stem shared across two
        supported storage extensions."""
        g, run, exp = make_run(
            ["output1D.csv", "output1D.tsv"],
            [{"file": "output1D", "cols": ["col1"]}],
        )
        with pytest.raises(ValueError, match="[Aa]mbiguous"):
            g.calc_gather_items(run, exp)


class TestMultiSourceResolution:
    def test_join_resolves_each_source(self, make_run):
        g, run, exp = make_run(
            ["blocks.csv", "energy.csv"],
            [
                {
                    "name": "efficiency",
                    "sources": [
                        {"file": "blocks", "cols": ["col1"]},
                        {
                            "file": "energy",
                            "cols": [{"name": "col2", "as": "energy_col2"}],
                        },
                    ],
                }
            ],
        )
        specs = g.calc_gather_items(run, exp)
        # one spec per output column: col1 + energy_col2
        assert sorted(s.collate_col for s in specs) == ["col1", "energy_col2"]
        assert all(len(s.sources) == 2 for s in specs)
        assert all(s.output_stem == "efficiency" for s in specs)
        srcfiles = sorted(str(x.item_stem_path) for x in specs[0].sources)
        assert srcfiles == ["blocks.csv", "energy.csv"]

    def test_ambiguous_join_source_is_hard_error(self, make_run):
        g, run, exp = make_run(
            ["blocks.csv", "blocks.tsv", "energy.csv"],
            [
                {
                    "name": "j",
                    "sources": [
                        {"file": "blocks", "cols": ["col1"]},
                        {"file": "energy", "cols": ["col2"]},
                    ],
                }
            ],
        )
        with pytest.raises(ValueError, match="[Aa]mbiguous"):
            g.calc_gather_items(run, exp)

    def test_join_missing_one_source_contributes_nothing(self, make_run):
        g, run, exp = make_run(
            ["blocks.csv"],  # energy.csv absent
            [
                {
                    "name": "j",
                    "sources": [
                        {"file": "blocks", "cols": ["col1"]},
                        {"file": "energy", "cols": ["col2"]},
                    ],
                }
            ],
        )
        assert g.calc_gather_items(run, exp) == []
