#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Fixture-free unit tests for the N-D ``XVarBatchCriteria`` machinery.

``bc_test.py`` drives the factory end-to-end and needs the external
``sierra-sample-project`` checkout plus a pipeline run. The engine-agnostic
combinatorial logic in ``XVarBatchCriteria`` -- experiment-name cross products,
attr/add/rm changelist products, the ``n_agents`` stride decomposition, and
``exp_scenario_name`` delegation -- needs none of that. Here we build the
criteria from tiny in-process stubs and pin exactly the branches the coverage
report flags as missing (batch_criteria.py lines ~533-612).
"""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.experiment import definition


class _StubCriteria(bc.UnivarBatchCriteria):
    """A minimal univariate criteria with a caller-chosen cardinality.

    Implements just enough of the interface for XVarBatchCriteria to combine
    it: an attr changelist of length ``n``, matching exp names.
    """

    def __init__(self, name, n, *, adds=0, rms=0):
        bc.BaseBatchCriteria.__init__(self, name, {}, pathlib.Path("/tmp/x"))
        self._n = n
        self._adds = adds
        self._rms = rms

    def gen_attr_changelist(self):
        return [
            definition.AttrChangeSet(definition.AttrChange(".//a", "v", str(i)))
            for i in range(self._n)
        ]

    def gen_exp_names(self):
        return [f"c1-exp{i}" for i in range(self._n)]

    def gen_element_addlist(self):
        return [
            definition.ElementAddList(
                definition.ElementAdd(".//p", "t", {"k": str(i)}, False)
            )
            for i in range(self._adds)
        ]

    def gen_tag_rmlist(self):
        return [
            definition.ElementRmList(definition.ElementRm(".//p", f"t{i}"))
            for i in range(self._rms)
        ]


class _StubCriteria2(_StubCriteria):
    """A minimal univariate criteria with a caller-chosen cardinality.

    Implements just enough of the interface for XVarBatchCriteria to combine
    it: an attr changelist of length ``n``, matching exp names, and (optionally)
    element add/rm lists and n_agents.
    """

    def __init__(self, name, n, agents, adds=0, rms=0):
        _StubCriteria.__init__(self, name, n)
        self._agents = agents

    def n_agents(self, exp_num):
        return self._agents[exp_num]


class _ScenarioCriteria(_StubCriteria):
    """A stub that additionally defines exp_scenario_name (like constant density).

    Mirrors the real ConstantDensity contract: a criteria that can compute a
    scenario name overrides BOTH computable_exp_scenario_name() (to True) and
    exp_scenario_name(). Overriding only the latter is not enough -- the bivar's
    computable flag is the OR of its sub-criteria's flags.
    """

    def computable_exp_scenario_name(self):
        return True

    def exp_scenario_name(self, exp_num):
        return f"scenario{exp_num}"


# --- cardinality + exp-name cross product -----------------------------------
class TestBivarNames:
    def test_cardinality_is_number_of_criteria(self):
        x = bc.XVarBatchCriteria([_StubCriteria("a", 5), _StubCriteria("b", 4)])
        assert x.cardinality() == 2

    def test_exp_names_cross_product(self):
        x = bc.XVarBatchCriteria([_StubCriteria("a", 5), _StubCriteria("b", 4)])
        names = x.gen_exp_names()
        assert len(names) == 20
        assert names[0] == "c1-exp0+c2-exp0"
        assert names[-1] == "c1-exp4+c2-exp3"

    def test_name_is_plus_joined(self):
        x = bc.XVarBatchCriteria(
            [_StubCriteria("max_speed", 2), _StubCriteria("fuel", 2)]
        )
        assert x.name == "max_speed+fuel"


# --- changelist / addlist / rmlist products ---------------------------------
class TestBivarProducts:
    def test_attr_changelist_product_size(self):
        x = bc.XVarBatchCriteria([_StubCriteria("a", 5), _StubCriteria("b", 4)])
        assert len(x.gen_attr_changelist()) == 20

    def test_element_addlist_product_size(self):
        x = bc.XVarBatchCriteria(
            [_StubCriteria("a", 3, adds=3), _StubCriteria("b", 2, adds=2)]
        )
        assert len(x.gen_element_addlist()) == 6  # 3 * 2

    def test_tag_rmlist_product_size(self):
        x = bc.XVarBatchCriteria(
            [_StubCriteria("a", 3, rms=3), _StubCriteria("b", 2, rms=2)]
        )
        assert len(x.gen_tag_rmlist()) == 6  # 3 * 2


# --- n_agents stride decomposition ------------------------------------------
class TestBivarNAgents:
    def test_first_axis_stride(self):
        c1 = _StubCriteria2("a", 5, agents=[10, 20, 30, 40, 50])
        c2 = _StubCriteria("b", 4)
        x = bc.XVarBatchCriteria([c1, c2])
        assert x.n_agents(0) == 10
        assert x.n_agents(4) == 20
        assert x.n_agents(7) == 20
        assert x.n_agents(19) == 50


# --- exp_scenario_name delegation + error path ------------------------------
class TestBivarScenarioName:
    def test_delegates_to_scenario_defining_criteria(self):
        # c1 defines exp_scenario_name; delegation divides exp_num by the size
        # of c1's attr changelist (5) -> int(8/5) == 1.
        x = bc.XVarBatchCriteria([_ScenarioCriteria("cd", 5), _StubCriteria("fuel", 4)])
        assert x.computable_exp_scenario_name() is True
        assert x.exp_scenario_name(8) == "scenario1"

    def test_raises_when_no_criteria_defines_it(self):
        # NOTE: _StubCriteria does NOT define exp_scenario_name, so the bivar
        # falls through to the documented RuntimeError. (See smell note: the
        # base class exposes n_agents on every criteria via hasattr, but not
        # exp_scenario_name, so this branch is reachable.)
        x = bc.XVarBatchCriteria([_StubCriteria("a", 5), _StubCriteria("b", 4)])
        with pytest.raises(RuntimeError):
            x.exp_scenario_name(0)


# --- set_batch_input_root propagation ---------------------------------------
class TestSetBatchInputRoot:
    def test_propagates_to_subcriteria(self):
        c1 = _StubCriteria("a", 2)
        c2 = _StubCriteria("b", 2)
        x = bc.XVarBatchCriteria([c1, c2])
        new_root = pathlib.Path("/tmp/new-root")
        x.set_batch_input_root(new_root)
        assert x.batch_input_root == new_root
        assert c1.batch_input_root == new_root
        assert c2.batch_input_root == new_root
