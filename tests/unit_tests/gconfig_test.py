#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for up-front validation of ``graphs.yaml`` and the dispatch tables."""

# Core packages

# 3rd party packages
import pytest

# Project packages
from sierra.core.graphs import schema
from sierra.plugins.prod.graphs import intra
from sierra.core.graphs import gconfig


def _graph(**over):
    base = {
        "src": "src",
        "dest": "dst",
        "type": "histogram",
        "cols": ["a"],
    }
    base.update(over)
    return base


def _cfg(*graphs, section="intra-exp"):
    return {section: {"cat": list(graphs)}}


class TestValidate:
    def test_defaults_materialized(self):
        out = gconfig.validate(_cfg(_graph()))
        g = out["intra-exp"]["cat"][0]

        assert g["title"] == ""
        assert g["xlabel"] == ""
        # histogram's ylabel defaults to "Count" rather than "" -- the axis
        # always means the same thing, unlike the free-form x axis.
        assert g["ylabel"] == "Count"
        assert g["kind"] == "overlay"

    def test_keys_without_defaults_stay_absent(self):
        """Cmdline-derived keys must not be invented by the schema."""
        out = gconfig.validate(_cfg(_graph()))
        g = out["intra-exp"]["cat"][0]

        assert "backend" not in g
        assert "bins" not in g

    def test_unknown_type_rejected(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate(_cfg(_graph(type="hstgram")))

        assert "not supported in this section" in str(e.value)

    def test_missing_type_rejected(self):
        bad = _graph()
        del bad["type"]

        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate(_cfg(bad))

        assert "missing required key 'type'" in str(e.value)

    def test_unknown_section_rejected(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate({"intra-xp": {"cat": [_graph()]}})

        assert "unknown top-level section" in str(e.value)

    def test_missing_required_key_rejected(self):
        bad = _graph()
        del bad["cols"]

        with pytest.raises(gconfig.ConfigError):
            gconfig.validate(_cfg(bad))

    def test_all_problems_reported_together(self):
        """The whole file is checked, not just up to the first error.

        This is the point of validating up-front: a project with several bad
        definitions should be fixable in one pass rather than one run per
        problem.
        """
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate(
                _cfg(
                    _graph(type="bogus1"),
                    _graph(type="bogus2"),
                    _graph(kind="bogus3"),
                )
            )

        assert len(e.value.problems) == 3

    def test_problem_names_its_location(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate(_cfg(_graph(), _graph(type="nope")))

        assert "intra-exp/cat[1]" in str(e.value)

    def test_non_list_category_rejected(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate({"intra-exp": {"cat": _graph()}})

        assert "expected a list" in str(e.value)

    def test_both_sections_validated(self):
        out = gconfig.validate(
            {
                "intra-exp": {"cat": [_graph()]},
                "inter-exp": {"cat": [_graph()]},
            }
        )

        assert set(out) == {"intra-exp", "inter-exp"}

    def test_valid_config_passes_through_unchanged_shape(self):
        out = gconfig.validate(_cfg(_graph(), _graph()))

        assert list(out) == ["intra-exp"]
        assert list(out["intra-exp"]) == ["cat"]
        assert len(out["intra-exp"]["cat"]) == 2


class TestSection:
    def test_missing_section_returns_none(self):
        assert gconfig.section({"intra-exp": {}}, "inter-exp") is None

    def test_present_section_returned(self):
        cfg = {"inter-exp": {"cat": []}}
        assert gconfig.section(cfg, "inter-exp") == {"cat": []}


class TestDispatchTables:
    def test_every_schema_type_has_a_kind_or_is_deliberately_absent(self):
        """Every graph type either renders intra-exp, or is documented as not.

        Guards against a schema being added with no dispatch entry, which is
        how ``network`` came to be fully documented but never generated.
        """
        assert set(intra.KINDS) == set(schema.BY_TYPE) - {"summary_line"}, (
            "intra.KINDS and schema.BY_TYPE have drifted; summary_line is the "
            "only inter-exp-only type"
        )

    def test_each_kind_has_a_distinct_cli_flag(self):
        flags = [k.cli_flag for k in intra.KINDS.values()]
        assert len(flags) == len(set(flags))

    @pytest.mark.parametrize("gtype,kind", sorted(intra.KINDS.items()))
    def test_kwargs_builder_only_indexes_guaranteed_keys(self, gtype, kind):
        """Each kwargs builder works on a minimal validated definition.

        Catches a builder indexing a key which the schema marks optional
        without a default -- the ``loaded["title"]`` bug class.
        """
        minimal = {
            "src": "s",
            "dest": "d",
            "type": gtype,
        }
        if gtype == "histogram":
            minimal["cols"] = ["a"]

        validated = gconfig.validate(_cfg(minimal))["intra-exp"]["cat"][0]

        cmdopts = {
            "plot_log_yscale": False,
            "center": "mean",
            "spread": "none",
            "graphs_backend": "matplotlib",
            "plot_large_text": False,
        }

        # stacked_line's builder reaches for engine plumbing to compute xticks;
        # that is covered by the integration path, not here.
        if gtype == "stacked_line":
            pytest.skip("needs engine plugin machinery for xticks")

        kind.kwargs_fn(validated, cmdopts, None)
