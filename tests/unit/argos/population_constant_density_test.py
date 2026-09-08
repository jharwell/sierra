#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for ``PopulationConstantDensity`` (ARGoS, 0% in coverage report).

These construct the criterion directly (bypassing ``factory``, which needs a
project scenario generator) with a hand-built ``dimensions`` list, and exercise
the engine-agnostic-ish logic:

* ``n_agents`` -- ``int(target_density/100 * area)`` arithmetic.
* ``gen_attr_changelist`` -- one ``quantity`` AttrChange added per extent, the
  clamp-to-1 branch for sub-1 populations, and the ``already_added`` idempotency
  guard.

See the note on ``test_n_agents_vs_changelist_disagree_on_clamp`` for a behavior
mismatch this pins.
"""

# Core packages
import pathlib
import logging

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.engine.argos.variables import population_constant_density as pcd
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D


def _make(dims, density, cli="population_constant_density.1p0.I16.C4"):
    """Build a PopulationConstantDensity without the factory/project."""
    return pcd.PopulationConstantDensity(
        cli, {}, pathlib.Path("/tmp/does-not-matter"), density, dims, "RN"
    )


def _quantities(changelist):
    """Extract every ``quantity`` attr value across all changesets."""
    return [
        chg.value
        for cs in changelist
        for chg in cs
        if getattr(chg, "attr", None) == "quantity"
    ]


# --- n_agents: int(density/100 * area) --------------------------------------
class TestNAgents:
    @pytest.mark.parametrize(
        "x,y,density,expected",
        [
            (10, 10, 1.0, 1),    # 1/100 * 100 = 1
            (20, 20, 1.0, 4),    # 1/100 * 400 = 4
            (10, 10, 10.0, 10),  # 10/100 * 100 = 10
            (30, 30, 5.0, 45),   # 5/100 * 900 = 45
        ],
    )
    def test_value(self, x, y, density, expected):
        crit = _make([ArenaExtent(Vector3D(x, y, 1))], density)
        assert crit.n_agents(0) == expected

    def test_truncates_toward_zero(self):
        # 1/100 * 150 = 1.5 -> int() truncates to 1.
        crit = _make([ArenaExtent(Vector3D(15, 10, 1))], 1.0)
        assert crit.n_agents(0) == 1

    def test_indexes_dimensions(self):
        dims = [ArenaExtent(Vector3D(10, 10, 1)), ArenaExtent(Vector3D(20, 20, 1))]
        crit = _make(dims, 1.0)
        assert crit.n_agents(0) == 1
        assert crit.n_agents(1) == 4


# --- gen_attr_changelist: quantity injection + clamp + idempotency ----------
class TestGenAttrChangelist:
    def test_one_quantity_per_extent(self):
        dims = [ArenaExtent(Vector3D(10, 10, 1)), ArenaExtent(Vector3D(20, 20, 1))]
        crit = _make(dims, 1.0)
        cl = crit.gen_attr_changelist()
        assert len(cl) == 2
        assert _quantities(cl) == ["1", "4"] or sorted(_quantities(cl)) == ["1", "4"]

    def test_clamp_to_one_for_subunit_population(self, caplog):
        # 0.01/100 * 4 = 0.0004 -> int() == 0 -> clamped to 1 (ARGoS needs >=1).
        crit = _make([ArenaExtent(Vector3D(2, 2, 1))], 0.01)
        with caplog.at_level(logging.WARNING):
            cl = crit.gen_attr_changelist()
        assert _quantities(cl) == ["1"]

    def test_idempotent_no_double_add(self):
        # Calling twice must not append a second quantity change (already_added).
        crit = _make([ArenaExtent(Vector3D(10, 10, 1))], 1.0)
        crit.gen_attr_changelist()
        second = crit.gen_attr_changelist()
        assert len(_quantities(second)) == 1
        assert crit.already_added is True

    def test_n_agents_and_changelist_agree_on_clamp(self):
        # Both paths go through the shared _agents_for() helper, so a sub-1
        # population is clamped to 1 consistently: n_agents() and the generated
        # quantity attribute agree. (Previously n_agents() returned the raw,
        # unclamped 0 while the changelist wrote 1 -- fixed.)
        crit = _make([ArenaExtent(Vector3D(2, 2, 1))], 0.01)
        assert crit.n_agents(0) == 1
        assert _quantities(crit.gen_attr_changelist()) == ["1"]
