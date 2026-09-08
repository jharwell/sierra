#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for pure helpers in ``sierra.core.utils``."""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.core import utils
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D


# --- activation functions / scaler ------------------------------------------
class TestMathHelpers:
    def test_sigmoid_midpoint(self):
        assert utils.Sigmoid(0)() == pytest.approx(0.5)

    def test_sigmoid_symmetry(self):
        # f(-x) == 1 - f(x); also exercises the numerically-stable negative
        # branch.
        assert utils.Sigmoid(-3)() == pytest.approx(1.0 - utils.Sigmoid(3)())

    def test_relu_clamps_negatives(self):
        assert utils.ReLu(-5)() == 0
        assert utils.ReLu(0)() == 0
        assert utils.ReLu(5)() == 5

    def test_scale_minmax_endpoints_and_mid(self):
        assert utils.scale_minmax(0, 10, 0) == pytest.approx(-1.0)
        assert utils.scale_minmax(0, 10, 10) == pytest.approx(1.0)
        assert utils.scale_minmax(0, 10, 5) == pytest.approx(0.0)


# --- ArenaExtent formatting -------------------------------------------------
class TestArenaExtentStr:
    def test_str_is_dims_at_origin(self):
        e = ArenaExtent(Vector3D(3, 4, 5))
        assert str(e) == "(3,4,5)@(0,0,0)"

    def test_str_reflects_origin(self):
        e = ArenaExtent(Vector3D(3, 4, 5), Vector3D(1, 1, 1))
        assert str(e) == "(3,4,5)@(1,1,1)"


# --- exp_template_path ------------------------------------------------------
class TestExpTemplatePath:
    def test_joins_root_dir_and_template_stem(self):
        cmdopts = {"expdef_template": pathlib.Path("/some/dir/template.argos")}
        out = utils.exp_template_path(cmdopts, pathlib.Path("/root"), "c1-exp0")
        assert out == pathlib.Path("/root/c1-exp0/template")


# --- dir_create_checked -----------------------------------------------------
class TestDirCreateChecked:
    def test_creates_with_parents(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        utils.dir_create_checked(target, exist_ok=True)
        assert target.is_dir()

    def test_accepts_str_path(self, tmp_path):
        target = tmp_path / "strpath"
        utils.dir_create_checked(str(target), exist_ok=True)
        assert target.is_dir()

    def test_raises_when_exists_and_not_allowed(self, tmp_path):
        target = tmp_path / "dup"
        target.mkdir()
        with pytest.raises(FileExistsError):
            utils.dir_create_checked(target, exist_ok=False)


# --- exp_range_calc ---------------------------------------------------------
class TestExpRangeCalc:
    def test_none_returns_all(self):
        dirs = ["c1-exp0", "c1-exp1", "c1-exp2"]
        out = utils.exp_range_calc(None, pathlib.Path("/r"), dirs)
        assert out == [pathlib.Path("/r") / d for d in dirs]

    def test_inclusive_slice(self):
        dirs = [f"c1-exp{i}" for i in range(5)]
        out = utils.exp_range_calc("1:3", pathlib.Path("/r"), dirs)
        # min:max is inclusive of max -> indices 1,2,3.
        assert out == [pathlib.Path("/r") / f"c1-exp{i}" for i in (1, 2, 3)]

    def test_min_greater_than_max_raises(self):
        dirs = [f"c1-exp{i}" for i in range(5)]
        with pytest.raises(AssertionError):
            utils.exp_range_calc("3:1", pathlib.Path("/r"), dirs)


# --- exp_include_filter -----------------------------------------------------
class TestExpIncludeFilter:
    def test_none_returns_target_unchanged(self):
        target = [0, 1, 2, 3, 4]
        assert utils.exp_include_filter(None, target, n_exps=5) == target

    def test_explicit_bounds(self):
        target = [0, 1, 2, 3, 4]
        assert utils.exp_include_filter("1:3", target, n_exps=5) == [1, 2]

    def test_empty_start_means_from_beginning(self):
        # Documented 2026 fix: ":Y" must work (previously int("") raised).
        target = [0, 1, 2, 3, 4]
        assert utils.exp_include_filter(":3", target, n_exps=5) == [0, 1, 2]

    def test_empty_end_means_to_end(self):
        target = [0, 1, 2, 3, 4]
        assert utils.exp_include_filter("2:", target, n_exps=5) == [2, 3, 4]

    def test_exp0_excluded_shifts_start(self):
        # When target is shorter than n_exps (a perf measure excluding exp0),
        # an explicit start is shifted down by one so absolute indices line up.
        target = [1, 2, 3, 4]  # len 4 < n_exps 5
        # start=2 -> shifted to 1 -> target[1:] == [2,3,4]
        assert utils.exp_include_filter("2:", target, n_exps=5) == [2, 3, 4]


# --- bivar_exp_labels_calc --------------------------------------------------
class TestBivarExpLabelsCalc:
    def test_splits_and_sorts_axis_labels(self):
        # Names are "cX-expI+cY-expJ"; helper splits on '+' and dedups/sorts.
        class _P:
            def __init__(self, name):
                self.name = name

        dirs = [
            _P("c1-exp0+c2-exp0"),
            _P("c1-exp0+c2-exp1"),
            _P("c1-exp1+c2-exp0"),
            _P("c1-exp1+c2-exp1"),
        ]
        xlabels, ylabels = utils.bivar_exp_labels_calc(dirs)
        assert xlabels == ["c1-exp0", "c1-exp1"]
        assert ylabels == ["c2-exp0", "c2-exp1"]
