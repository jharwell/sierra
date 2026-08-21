#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for the reusable batch-criteria PARSE utilities.

These cover the shared, engine-agnostic parsing helpers that live in
``sierra.core.variables`` -- the code every criterion (builtin or project)
delegates its cmdline spec parsing to. Distinct from bc_test.py, which drives
the full factory -> attr-changelist -> exp-names integration for specific
criteria; here we pin just the spec-string -> numbers/cardinality mapping, where
an off-by-one silently produces the wrong number of experiments.

Scope note: the only BUILTIN batch criterion is MonteCarlo (``builtin.py``); the
per-project criteria (max_speed, fuel, ...) are thin shims over these shared
helpers and aren't re-tested here. What's worth pinning is the shared grammar:
``linspace_parse`` (used by density/speed/fuel-style ranges), the MonteCarlo
parse, ``population_size.parse`` (Log/Linear), ``variable_density.parse``, and
``exp_setup.parse``.
"""

# Core packages

# 3rd party packages
import pytest

# Project packages
from sierra.core.variables import builtin, population_size, variable_density
from sierra.core.variables import exp_setup


# --- linspace_parse: <min>.<max>.C<cardinality> -----------------------------
#
# Returns list(np.linspace(min*scale, max*scale, cardinality)) -- FLOATS. The
# scale_factor lets specs like "4.8.C8" with scale 0.1 yield a 0.4-0.8 range
# without parsing decimals out of the CLI string.
class TestLinspaceParse:
    def test_docstring_example(self):
        assert builtin.linspace_parse("1.9.C5") == [1, 3, 5, 7, 9]

    def test_returns_floats(self):
        vals = builtin.linspace_parse("1.9.C5")
        assert all(isinstance(v, float) for v in vals)

    def test_two_points_endpoints(self):
        assert builtin.linspace_parse("1.9.C2") == [1, 9]

    def test_cardinality_count(self):
        for card in (2, 3, 4, 5, 8):
            assert len(builtin.linspace_parse(f"1.100.C{card}")) == card

    def test_endpoints_preserved(self):
        vals = builtin.linspace_parse("2.20.C4")
        assert vals[0] == 2
        assert vals[-1] == 20

    def test_scale_factor_shifts_range(self):
        # The documented trick: "4.8.C8" * 0.1 -> a 0.4..0.8 range.
        vals = builtin.linspace_parse("4.8.C8", 0.1)
        assert vals[0] == pytest.approx(0.4)
        assert vals[-1] == pytest.approx(0.8)
        assert len(vals) == 8

    def test_scale_factor_default_is_identity(self):
        assert builtin.linspace_parse("1.9.C5", 1.0) == builtin.linspace_parse("1.9.C5")

    def test_whitespace_tolerated(self):
        # The regex allows optional whitespace around the .C and cardinality.
        assert builtin.linspace_parse("1.9.C 5") == builtin.linspace_parse("1.9.C5")

    def test_bad_spec_raises(self):
        with pytest.raises(AssertionError):
            builtin.linspace_parse("not-a-spec")


# --- The one builtin criterion: MonteCarlo ----------------------------------
class TestMonteCarloParse:
    def test_cardinality_extracted(self):
        # "MonteCarlo.C7" -> cardinality 7.
        assert builtin._mc_parse("montecarlo.MonteCarlo.C7") == 7

    def test_various_cardinalities(self):
        for card in (1, 3, 10, 25):
            assert builtin._mc_parse(f"mc.MonteCarlo.C{card}") == card

    def test_rejects_non_montecarlo(self):
        # The parser asserts the criterion name is MonteCarlo.
        with pytest.raises(AssertionError):
            builtin._mc_parse("mc.SomethingElse.C5")

    def test_rejects_missing_cardinality(self):
        with pytest.raises(AssertionError):
            builtin._mc_parse("mc.MonteCarlo.notacard")


# --- population_size.parse: Log / Linear ------------------------------------
class TestPopulationSizeParse:
    def test_log_powers_of_two(self):
        # Log16 -> [1, 2, 4, 8, 16].
        assert population_size.parse("population_size.Log16") == [1, 2, 4, 8, 16]

    def test_log_cardinality_is_log2_plus_one(self):
        # Log32 -> 2^0..2^5 = 6 experiments.
        vals = population_size.parse("population_size.Log32")
        assert vals == [1, 2, 4, 8, 16, 32]

    def test_linear_explicit_cardinality(self):
        # Linear3.C3 -> increment 1 -> [1, 2, 3] (matches engine spec usage).
        assert population_size.parse("population_size.Linear3.C3") == [1, 2, 3]

    def test_linear_default_cardinality_is_max_over_ten(self):
        # Linear100 with no C -> cardinality max/10 = 10 -> [10,20,...,100].
        assert population_size.parse("population_size.Linear100") == [
            10,
            20,
            30,
            40,
            50,
            60,
            70,
            80,
            90,
            100,
        ]

    def test_linear_increment(self):
        # Linear20.C4 -> increment 20/4=5 -> [5,10,15,20].
        assert population_size.parse("population_size.Linear20.C4") == [5, 10, 15, 20]

    def test_bad_model_raises(self):
        # "Exponential" matches neither Log nor Linear, so the model regex
        # returns None and .group() raises AttributeError before the assert.
        with pytest.raises((AssertionError, AttributeError)):
            population_size.parse("population_size.Exponential16")


# --- variable_density.parse: <minpNN>.<maxpNN>.C<card> ----------------------
#
# Density chunks use "<int>p<mantissa>" spelling: 4p5 -> 4.5.
class TestVariableDensityParse:
    def test_basic_range(self):
        # 4p5 -> 4.5, 8p5 -> 8.5, C3 -> [4.5, 6.5, 8.5].
        vals = variable_density.parse("density.4p5.8p5.C3")
        assert vals == [pytest.approx(4.5), pytest.approx(6.5), pytest.approx(8.5)]

    def test_cardinality(self):
        assert len(variable_density.parse("density.1p0.9p0.C5")) == 5

    def test_mantissa_parsed(self):
        # 0p25 -> 0.25; single-point-ish endpoints.
        vals = variable_density.parse("density.0p25.1p75.C2")
        assert vals[0] == pytest.approx(0.25)
        assert vals[-1] == pytest.approx(1.75)

    def test_wrong_section_count_raises(self):
        with pytest.raises(AssertionError):
            variable_density.parse("density.4p5.C3")  # missing max section


# --- exp_setup.parse: T<secs>[.K<ticks>] ------------------------------------
class TestExpSetupParse:
    def test_secs_only(self):
        out = exp_setup.parse("exp_setup.T50", {})
        assert out["n_secs_per_run"] == 50
        assert "n_ticks_per_sec" not in out

    def test_secs_and_ticks(self):
        out = exp_setup.parse("exp_setup.T5.K5", {})
        assert out["n_secs_per_run"] == 5
        assert out["n_ticks_per_sec"] == 5

    def test_pretty_name_set(self):
        out = exp_setup.parse("exp_setup.T50.K10", {})
        assert out["pretty_name"] == "T50.K10"

    def test_defaults_preserved(self):
        # Keys already in dflts pass through untouched.
        out = exp_setup.parse("exp_setup.T5", {"existing": "kept"})
        assert out["existing"] == "kept"

    def test_bad_spec_raises(self):
        with pytest.raises(AssertionError):
            exp_setup.parse("exp_setup.X99", {})
