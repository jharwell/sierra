#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for the ARGoS constant-density batch-criteria base + parser.

Pure-logic coverage for ``plugins/engine/argos/variables/constant_density.py``,
which reads 0% in the coverage report because it is only ever reached through
the full factory (which needs a project's scenario generator). The two pieces
worth pinning without that machinery are:

* ``parse`` -- the ``<c>p<m>.I<inc>.C<card>`` spec grammar (mirrors the
  variable-density parse tests in ``bc_parse_test.py``).
* ``ConstantDensity.exp_scenario_name`` -- pure string formatting over a
  hand-built ``dimensions`` list; no I/O, no project.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.engine.argos.variables import constant_density as cd
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D


# --- parse: <char>p<mantissa>.I<inc>.C<cardinality> -------------------------
class TestConstantDensityParse:
    def test_basic_spec(self):
        # "1p0.I16.C4" -> density 1.0, arena increment 16, cardinality 4.
        out = cd.parse("population_constant_density.1p0.I16.C4")
        assert out["target_density"] == pytest.approx(1.0)
        assert out["arena_size_inc"] == 16
        assert out["cardinality"] == 4

    def test_mantissa_parsed(self):
        # 2p5 -> 2.5.
        out = cd.parse("population_constant_density.2p5.I8.C3")
        assert out["target_density"] == pytest.approx(2.5)

    def test_increment_and_cardinality_are_ints(self):
        out = cd.parse("population_constant_density.5p0.I10.C7")
        assert isinstance(out["arena_size_inc"], int)
        assert isinstance(out["cardinality"], int)
        assert out["arena_size_inc"] == 10
        assert out["cardinality"] == 7

    def test_missing_increment_raises(self):
        # No I<inc> section -> regex fails to match -> AssertionError.
        with pytest.raises(AssertionError):
            cd.parse("population_constant_density.1p0.C4")

    def test_missing_cardinality_raises(self):
        with pytest.raises(AssertionError):
            cd.parse("population_constant_density.1p0.I16")

    def test_garbage_spec_raises(self):
        with pytest.raises(AssertionError):
            cd.parse("population_constant_density.not-a-spec")


# --- ConstantDensity.exp_scenario_name / computable flag --------------------
#
# Construct the base directly with a hand-built dimensions list so we never
# touch the factory (which needs a project scenario generator).
def _make(dims, tag="RN", cli="population_constant_density.1p0.I16.C4"):
    return cd.ConstantDensity(
        cli_arg=cli,
        main_config={},
        batch_input_root=pathlib.Path("/tmp/does-not-matter"),
        target_density=1.0,
        dimensions=dims,
        scenario_tag=tag,
    )


class TestConstantDensityScenarioName:
    def test_computable_flag_true(self):
        crit = _make([ArenaExtent(Vector3D(10, 10, 2))])
        assert crit.computable_exp_scenario_name() is True

    def test_scenario_name_format(self):
        # "<tag>.<x>x<y>x<z>" for the extent at exp_num.
        crit = _make([ArenaExtent(Vector3D(10, 5, 2))], tag="RN")
        assert crit.exp_scenario_name(0) == "RN.10x5x2"

    def test_scenario_name_indexes_dimensions(self):
        dims = [
            ArenaExtent(Vector3D(10, 10, 2)),
            ArenaExtent(Vector3D(20, 20, 2)),
            ArenaExtent(Vector3D(30, 30, 2)),
        ]
        crit = _make(dims, tag="SS")
        assert crit.exp_scenario_name(1) == "SS.20x20x2"
        assert crit.exp_scenario_name(2) == "SS.30x30x2"

    def test_attr_changes_seeded_from_arena_shape(self):
        # __init__ builds attr_changes via ArenaShape(dimensions); one
        # changeset per extent.
        dims = [ArenaExtent(Vector3D(10, 10, 2)), ArenaExtent(Vector3D(20, 20, 2))]
        crit = _make(dims)
        assert len(crit.attr_changes) == 2
