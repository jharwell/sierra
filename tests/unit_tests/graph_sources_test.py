#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for multi-source intra-experiment graph inputs.

Covers the ``src`` vs ``sources`` discriminator and its semantic checks in
:mod:`sierra.core.graphs.gconfig`, and the per-statistic join performed by
:func:`sierra.plugins.prod.graphs.intra._materialize_sources`.

A graph may name its input either with a single ``src`` (the common case)
or with a ``sources`` list drawing columns from several files, joined per
experiment. ``sources`` is intra-experiment only, and requires an explicit
``dest``.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest
import polars as pl

# Project packages
from sierra.core.graphs import gconfig, schema, sections
from sierra.plugins.prod.graphs import intra


@pytest.fixture(autouse=True)
def _register_sections():
    """Register intra/inter sections (idempotent) and reset afterwards."""
    sections.register(
        sections.Section(
            name="intra-exp",
            shape=sections.Shape.CATEGORIZED,
            by_type=schema.BY_TYPE,
            owner="prod.graphs",
        )
    )
    sections.register(
        sections.Section(
            name="inter-exp",
            shape=sections.Shape.CATEGORIZED,
            by_type=schema.BY_TYPE,
            owner="prod.graphs",
        )
    )
    yield


def _intra(graph):
    return {"intra-exp": {"cat": [graph]}}


def _inter(graph):
    return {"inter-exp": {"cat": [graph]}}


# ---------------------------------------------------------------------------
# gconfig: the src vs sources discriminator
# ---------------------------------------------------------------------------
class TestInputDiscriminator:
    def test_src_single_source_ok(self):
        gconfig.validate(
            _intra({"src": "output1D", "type": "stacked_line", "cols": ["c1"]})
        )

    def test_sources_multi_source_ok(self):
        gconfig.validate(
            _intra(
                {
                    "dest": "combined",
                    "type": "stacked_line",
                    "sources": [
                        {"file": "a", "cols": ["c1"]},
                        {"file": "b", "cols": [{"name": "c1", "as": "c1_b"}]},
                    ],
                }
            )
        )

    def test_both_spellings_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="both"):
            gconfig.validate(
                _intra(
                    {
                        "src": "x",
                        "type": "stacked_line",
                        "sources": [{"file": "a", "cols": ["c"]}],
                    }
                )
            )

    def test_neither_spelling_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="either"):
            gconfig.validate(_intra({"type": "stacked_line", "cols": ["c"]}))


# ---------------------------------------------------------------------------
# gconfig: sources-specific semantic rules
# ---------------------------------------------------------------------------
class TestSourcesSemantics:
    def test_sources_rejected_in_inter_exp(self):
        """Multi-file input is intra-experiment only: inter-exp collation
        consumes single already-joined files."""
        with pytest.raises(gconfig.ConfigError, match="intra-experiment"):
            gconfig.validate(
                _inter(
                    {
                        "dest": "z",
                        "type": "stacked_line",
                        "sources": [{"file": "a", "cols": ["c"]}],
                    }
                )
            )

    def test_dest_required_for_multi_source(self):
        with pytest.raises(gconfig.ConfigError, match="dest"):
            gconfig.validate(
                _intra(
                    {
                        "type": "stacked_line",
                        "sources": [{"file": "a", "cols": ["c"]}],
                    }
                )
            )

    def test_top_level_cols_conflicts_with_sources(self):
        with pytest.raises(gconfig.ConfigError, match="cannot be combined"):
            gconfig.validate(
                _intra(
                    {
                        "dest": "z",
                        "type": "stacked_line",
                        "cols": ["c"],
                        "sources": [{"file": "a", "cols": ["c"]}],
                    }
                )
            )

    def test_unresolved_collision_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="collision"):
            gconfig.validate(
                _intra(
                    {
                        "dest": "z",
                        "type": "stacked_line",
                        "sources": [
                            {"file": "a", "cols": ["k"]},
                            {"file": "b", "cols": ["k"]},
                        ],
                    }
                )
            )

    def test_resolved_collision_ok(self):
        gconfig.validate(
            _intra(
                {
                    "dest": "z",
                    "type": "stacked_line",
                    "sources": [
                        {"file": "a", "cols": [{"name": "k", "as": "k_a"}]},
                        {"file": "b", "cols": [{"name": "k", "as": "k_b"}]},
                    ],
                }
            )
        )

    def test_duplicate_col_within_source_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="[Dd]uplicate"):
            gconfig.validate(
                _intra(
                    {
                        "dest": "z",
                        "type": "stacked_line",
                        "sources": [{"file": "a", "cols": ["k", "k"]}],
                    }
                )
            )

    def test_histogram_also_supports_sources(self):
        gconfig.validate(
            _intra(
                {
                    "dest": "h",
                    "type": "histogram",
                    "sources": [{"file": "a", "cols": ["c1"]}],
                }
            )
        )


# ---------------------------------------------------------------------------
# gconfig: role-column types (confusion_matrix, heatmap)
# ---------------------------------------------------------------------------
class TestRoleColumnTypes:
    """Types that reference columns by named role (truth/predicted, x/y/z) must
    have those roles resolve to columns the joined sources produce."""

    def test_confusion_matrix_default_roles(self):
        # truth/predicted are the schema defaults; sources must produce them.
        gconfig.validate(
            _intra(
                {
                    "dest": "cm",
                    "type": "confusion_matrix",
                    "sources": [
                        {"file": "labels", "cols": [{"name": "actual", "as": "truth"}]},
                        {
                            "file": "model",
                            "cols": [{"name": "pred", "as": "predicted"}],
                        },
                    ],
                }
            )
        )

    def test_confusion_matrix_custom_roles(self):
        gconfig.validate(
            _intra(
                {
                    "dest": "cm",
                    "type": "confusion_matrix",
                    "truth_col": "a",
                    "predicted_col": "p",
                    "sources": [
                        {"file": "l", "cols": ["a"]},
                        {"file": "m", "cols": ["p"]},
                    ],
                }
            )
        )

    def test_confusion_matrix_missing_role_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="truth"):
            gconfig.validate(
                _intra(
                    {
                        "dest": "cm",
                        "type": "confusion_matrix",
                        "sources": [
                            {"file": "l", "cols": ["x"]},
                            {"file": "m", "cols": ["y"]},
                        ],
                    }
                )
            )

    def test_heatmap_xyz_present(self):
        gconfig.validate(
            _intra(
                {
                    "dest": "hm",
                    "type": "heatmap",
                    "sources": [
                        {"file": "fx", "cols": ["x"]},
                        {"file": "fy", "cols": ["y"]},
                        {"file": "fz", "cols": ["z"]},
                    ],
                }
            )
        )

    def test_heatmap_missing_z_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="'z'"):
            gconfig.validate(
                _intra(
                    {
                        "dest": "hm",
                        "type": "heatmap",
                        "sources": [
                            {"file": "fx", "cols": ["x"]},
                            {"file": "fy", "cols": ["y"]},
                        ],
                    }
                )
            )

    def test_single_source_role_types_unaffected(self):
        # With src, no role-vs-produced check applies (columns come from
        # the single file, resolved at plot time as before).
        gconfig.validate(_intra({"src": "grid", "type": "heatmap"}))
        gconfig.validate(_intra({"src": "preds", "type": "confusion_matrix"}))


# ---------------------------------------------------------------------------
# _materialize_sources: the per-statistic join
# ---------------------------------------------------------------------------
class TestMaterializeSources:
    @staticmethod
    def _write(d, name, df):
        df.write_csv(d / name)

    def test_joins_mean_family(self, tmp_path):
        self._write(tmp_path, "a.mean", pl.DataFrame({"c1": [1, 2, 3]}))
        self._write(
            tmp_path, "b.mean", pl.DataFrame({"c1": [10, 20, 30], "c2": [7, 8, 9]})
        )
        graph = {
            "dest": "combined",
            "sources": [
                {"file": "a", "cols": ["c1"]},
                {"file": "b", "cols": [{"name": "c1", "as": "c1_b"}, "c2"]},
            ],
        }
        stem = intra._materialize_sources(
            graph, tmp_path, "storage.csv", {"dist_stats": "none"}
        )
        assert stem == "combined"

        out = pl.read_csv(tmp_path / "combined.mean")
        assert out.columns == ["c1", "c1_b", "c2"]
        assert out.shape == (3, 3)

    def test_per_statistic_family(self, tmp_path):
        for ext in (".mean", ".stddev"):
            self._write(tmp_path, "a" + ext, pl.DataFrame({"c1": [1.0, 2.0]}))
            self._write(tmp_path, "b" + ext, pl.DataFrame({"c1": [3.0, 4.0]}))
        graph = {
            "dest": "j",
            "sources": [
                {"file": "a", "cols": ["c1"]},
                {"file": "b", "cols": [{"name": "c1", "as": "c1_b"}]},
            ],
        }
        intra._materialize_sources(
            graph, tmp_path, "storage.csv", {"dist_stats": "conf95"}
        )
        # Both the mean and the stddev families are joined.
        assert (tmp_path / "j.mean").is_file()
        assert (tmp_path / "j.stddev").is_file()
        assert pl.read_csv(tmp_path / "j.stddev").columns == ["c1", "c1_b"]

    def test_lenient_sparse_dispersion(self, tmp_path):
        """A dispersion stat covering a subset of the mean's columns joins only
        the columns it has -- mirroring the single-src path."""
        self._write(tmp_path, "a.mean", pl.DataFrame({"c1": [1, 2]}))
        self._write(tmp_path, "a.stddev", pl.DataFrame({"c1": [0.1, 0.2]}))
        self._write(tmp_path, "b.mean", pl.DataFrame({"c1": [3, 4], "c2": [5, 6]}))
        # b.stddev has c1 only -- no c2.
        self._write(tmp_path, "b.stddev", pl.DataFrame({"c1": [0.3, 0.4]}))
        graph = {
            "dest": "s",
            "sources": [
                {"file": "a", "cols": ["c1"]},
                {"file": "b", "cols": [{"name": "c1", "as": "c1_b"}, "c2"]},
            ],
        }
        intra._materialize_sources(
            graph, tmp_path, "storage.csv", {"dist_stats": "conf95"}
        )
        mean = pl.read_csv(tmp_path / "s.mean")
        stddev = pl.read_csv(tmp_path / "s.stddev")
        assert mean.columns == ["c1", "c1_b", "c2"]
        # c2 absent from b.stddev -> dropped leniently.
        assert stddev.columns == ["c1", "c1_b"]

    def test_missing_source_file_skips_extension(self, tmp_path):
        # Only the mean exists for both; stddev is absent entirely.
        self._write(tmp_path, "a.mean", pl.DataFrame({"c1": [1, 2]}))
        self._write(tmp_path, "b.mean", pl.DataFrame({"c1": [3, 4]}))
        graph = {
            "dest": "m",
            "sources": [
                {"file": "a", "cols": ["c1"]},
                {"file": "b", "cols": [{"name": "c1", "as": "c1_b"}]},
            ],
        }
        intra._materialize_sources(
            graph, tmp_path, "storage.csv", {"dist_stats": "conf95"}
        )
        assert (tmp_path / "m.mean").is_file()
        # stddev family absent -> no derived stddev written.
        assert not (tmp_path / "m.stddev").is_file()
