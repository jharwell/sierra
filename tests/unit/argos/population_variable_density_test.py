#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for ``PopulationVariableDensity`` (ARGoS, 0% in coverage report).

Constructed directly with a fixed ``extent`` and an explicit ``densities`` list
(the factory needs a project scenario generator, so it is bypassed). Covers:

* ``n_agents`` -- ``int(area * density/100)``.
* ``gen_attr_changelist`` -- one ``quantity`` AttrChange per density, the
  clamp-to-1 branch, and the ``already_added`` idempotency guard.

The same ``n_agents`` vs changelist clamp disagreement noted for
constant-density is pinned here too.
"""

# Core packages
import pathlib
import logging

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.engine.argos.variables import population_variable_density as pvd
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D


def _make(densities, extent=None, cli="population_variable_density.1p0.9p0.C3"):
    if extent is None:
        extent = ArenaExtent(Vector3D(10, 10, 1))  # area 100
    return pvd.PopulationVariableDensity(
        cli, {}, pathlib.Path("/tmp/does-not-matter"), densities, extent
    )


def _quantities(changelist):
    return [
        chg.value
        for cs in changelist
        for chg in cs
        if getattr(chg, "attr", None) == "quantity"
    ]


# --- n_agents: int(area * density/100) --------------------------------------
class TestNAgents:
    @pytest.mark.parametrize(
        "density,expected",
        [(1.0, 1), (5.0, 5), (9.0, 9), (10.0, 10)],  # area fixed at 100
    )
    def test_value(self, density, expected):
        crit = _make([density])
        assert crit.n_agents(0) == expected

    def test_truncates_toward_zero(self):
        # 100 * 1.5/100 = 1.5 -> int() -> 1.
        crit = _make([1.5])
        assert crit.n_agents(0) == 1

    def test_indexes_densities(self):
        crit = _make([1.0, 5.0, 9.0])
        assert [crit.n_agents(i) for i in range(3)] == [1, 5, 9]


# --- gen_attr_changelist -----------------------------------------------------
class TestGenAttrChangelist:
    def test_one_quantity_per_density(self):
        crit = _make([1.0, 5.0, 9.0])
        cl = crit.gen_attr_changelist()
        assert len(cl) == 3
        assert _quantities(cl) == ["1", "5", "9"]

    def test_clamp_to_one_for_subunit_population(self, caplog):
        # 4 * 0.001/100 ~= 0 -> clamped to 1.
        crit = _make([0.001], extent=ArenaExtent(Vector3D(2, 2, 1)))
        with caplog.at_level(logging.WARNING):
            cl = crit.gen_attr_changelist()
        assert _quantities(cl) == ["1"]

    def test_idempotent_no_double_add(self):
        crit = _make([1.0, 5.0])
        crit.gen_attr_changelist()
        second = crit.gen_attr_changelist()
        assert len(_quantities(second)) == 2
        assert crit.already_added is True

    def test_n_agents_and_changelist_agree_on_clamp(self):
        # Shared _agents_for() helper: n_agents() and the generated quantity
        # both clamp a sub-1 population to 1 and agree. (Previously n_agents()
        # returned the raw, unclamped 0 -- fixed.)
        crit = _make([0.001], extent=ArenaExtent(Vector3D(2, 2, 1)))
        assert crit.n_agents(0) == 1
        assert _quantities(crit.gen_attr_changelist()) == ["1"]
