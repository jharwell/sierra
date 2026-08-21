#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for the shared YAML validation harness
:mod:`sierra.core.yaml.validate`.

This is the per-entry strictyaml check and aggregating error type that both the
graphs config validator and the collation config validator build on.
"""

# 3rd party packages
import pytest
import strictyaml

# Project packages
from sierra.core.yaml.validate import ConfigError, validate_entry


_SCHEMA = strictyaml.Map(
    {
        "file": strictyaml.Str(),
        "cols": strictyaml.Seq(strictyaml.Str()),
    }
)


class TestValidateEntry:
    def test_valid_entry_returns_data(self):
        problems = []
        out = validate_entry(
            {"file": "a.csv", "cols": ["c1", "c2"]}, _SCHEMA, "e[0]", problems
        )
        assert out == {"file": "a.csv", "cols": ["c1", "c2"]}
        assert problems == []

    def test_non_mapping_appended(self):
        problems = []
        out = validate_entry(["not", "a", "map"], _SCHEMA, "e[1]", problems)
        assert out is None
        assert len(problems) == 1
        assert "e[1]" in problems[0]

    def test_missing_required_key_appended(self):
        problems = []
        out = validate_entry({"cols": ["c1"]}, _SCHEMA, "e[2]", problems)
        assert out is None
        assert len(problems) == 1
        assert "e[2]" in problems[0]

    def test_unknown_key_appended(self):
        """strictyaml rejects keys not in the schema by default."""
        problems = []
        out = validate_entry(
            {"file": "a.csv", "cols": ["c"], "bogus": "x"}, _SCHEMA, "e[3]", problems
        )
        assert out is None
        assert len(problems) == 1

    def test_problems_accumulate_across_calls(self):
        problems = []
        validate_entry({"cols": ["c"]}, _SCHEMA, "e[0]", problems)
        validate_entry({"file": "a.csv"}, _SCHEMA, "e[1]", problems)
        assert len(problems) == 2
        assert "e[0]" in problems[0] and "e[1]" in problems[1]


class TestConfigError:
    def test_carries_all_problems(self):
        err = ConfigError(["p1", "p2", "p3"], what="thing.yaml")
        assert err.problems == ["p1", "p2", "p3"]

    def test_message_includes_count_and_what(self):
        err = ConfigError(["only one"], what="thing.yaml")
        msg = str(err)
        assert "1 problem" in msg
        assert "thing.yaml" in msg
        assert "only one" in msg

    def test_default_what(self):
        err = ConfigError(["x"])
        assert "YAML config" in str(err)

    def test_is_runtime_error(self):
        assert isinstance(ConfigError(["x"]), RuntimeError)


class TestConfigErrorPickling:
    """ConfigError crosses the multiprocessing boundary (workers raise it, the
    parent re-raises). The default exception reconstruction would pass the
    formatted message string as ``problems`` and join() it character-by-
    character; ``__reduce__`` must prevent that.
    """

    def test_roundtrip_preserves_problems_as_list(self):
        import pickle

        err = ConfigError(["problem one", "problem two"], what="collate.yaml")
        out = pickle.loads(pickle.dumps(err))
        # The bug symptom: problems became a string and str(err) showed dozens
        # of single-character "problems".
        assert out.problems == ["problem one", "problem two"]
        assert out.what == "collate.yaml"

    def test_roundtrip_preserves_message(self):
        import pickle

        err = ConfigError(["a", "b"], what="x.yaml")
        out = pickle.loads(pickle.dumps(err))
        assert str(out) == str(err)

    def test_subclass_with_different_init_roundtrips(self):
        """A subclass whose __init__ takes only `problems` (like the graphs
        ConfigError) must also survive pickling."""
        import pickle

        # gconfig.ConfigError is the real such subclass.
        from sierra.core.graphs.gconfig import ConfigError as GraphsConfigError

        err = GraphsConfigError(["gp1", "gp2"])
        out = pickle.loads(pickle.dumps(err))
        assert out.problems == ["gp1", "gp2"]
        assert isinstance(out, ConfigError)
        assert type(out) is GraphsConfigError
        assert str(out) == str(err)
