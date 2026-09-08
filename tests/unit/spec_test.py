#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for ``sierra.core.experiment.spec`` scaffolding."""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.core.experiment import spec, definition
from sierra.core.variables import batch_criteria as bc


class _ScaffoldStub(bc.XVarBatchCriteria):
    """XVarBatchCriteria stub with caller-chosen changelist sizes."""

    def __init__(self, chgs=0, adds=0, rms=0):
        self.name = "stub"
        self._c, self._a, self._r = chgs, adds, rms
        self.criterias = []
        self.batch_input_root = pathlib.Path("/tmp/x")

    def gen_attr_changelist(self):
        return [
            definition.AttrChangeSet(definition.AttrChange(".//a", "v", str(i)))
            for i in range(self._c)
        ]

    def gen_element_addlist(self):
        return [
            definition.ElementAddList(
                definition.ElementAdd(".//p", "t", {"k": str(i)}, False)
            )
            for i in range(self._a)
        ]

    def gen_tag_rmlist(self):
        return [
            definition.ElementRmList(definition.ElementRm(".//p", f"t{i}"))
            for i in range(self._r)
        ]


# --- scaffold_spec_factory selection ----------------------------------------
class TestScaffoldSpecFactory:
    def test_chgs_only_is_simple(self):
        s = spec.scaffold_spec_factory(_ScaffoldStub(chgs=5))
        assert isinstance(s, spec.SimpleBatchScaffoldSpec)
        assert s.is_compound is False
        assert s.n_exps == 5
        assert len(s) == 5

    def test_adds_only_is_simple(self):
        s = spec.scaffold_spec_factory(_ScaffoldStub(adds=3))
        assert isinstance(s, spec.SimpleBatchScaffoldSpec)
        assert s.n_exps == 3

    def test_rms_only_is_simple(self):
        s = spec.scaffold_spec_factory(_ScaffoldStub(rms=4))
        assert isinstance(s, spec.SimpleBatchScaffoldSpec)
        assert s.n_exps == 4

    def test_chgs_and_adds_is_compound(self):
        s = spec.scaffold_spec_factory(_ScaffoldStub(chgs=5, adds=3))
        assert isinstance(s, spec.CompoundBatchScaffoldSpec)
        assert s.is_compound is True
        assert s.n_exps == 15  # 3 adds * 5 chgs

    def test_log_true_smoke(self):
        # log=True hits the info() branches; just assert it doesn't blow up and
        # still produces the right shape.
        s = spec.scaffold_spec_factory(_ScaffoldStub(chgs=2), log=True)
        assert s.n_exps == 2


# --- SimpleBatchScaffoldSpec ------------------------------------------------
class TestSimpleScaffoldSpec:
    def test_iter_yields_mods(self):
        s = spec.SimpleBatchScaffoldSpec(_ScaffoldStub(chgs=3))
        assert len(list(iter(s))) == 3

    def test_incompatible_combo_raises(self):
        # chgs AND adds is a compound shape; Simple must reject it.
        with pytest.raises(RuntimeError):
            spec.SimpleBatchScaffoldSpec(_ScaffoldStub(chgs=2, adds=2))


# --- CompoundBatchScaffoldSpec: three cases + error -------------------------
class TestCompoundScaffoldSpec:
    def test_case1_chgs_and_adds(self):
        s = spec.CompoundBatchScaffoldSpec(_ScaffoldStub(chgs=5, adds=3))
        assert s.n_exps == 15
        assert len(s.mods) == 15

    def test_case2_chgs_and_rms(self):
        s = spec.CompoundBatchScaffoldSpec(_ScaffoldStub(chgs=4, rms=2))
        assert s.n_exps == 8  # 2 rms * 4 chgs

    def test_case3_adds_and_rms(self):
        s = spec.CompoundBatchScaffoldSpec(_ScaffoldStub(adds=3, rms=2))
        assert s.n_exps == 6  # 2 rms * 3 adds

    def test_non_compound_shape_raises(self):
        # Only one changelist kind -> not a compound shape.
        with pytest.raises(RuntimeError):
            spec.CompoundBatchScaffoldSpec(_ScaffoldStub(chgs=2))

    def test_log_true_smoke(self):
        s = spec.CompoundBatchScaffoldSpec(_ScaffoldStub(chgs=2, adds=2), log=True)
        assert s.n_exps == 4
