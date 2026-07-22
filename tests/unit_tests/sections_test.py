#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Tests for the ``graphs.yaml`` section registry and cross-plugin validation."""

# Core packages

# 3rd party packages
import pytest

# Project packages
from sierra.core.graphs import gconfig, sections
from sierra.plugins.compare.graphs import schema as compareschema

# Importing these registers their sections; that is the behaviour under test.
import sierra.plugins.prod.graphs  # noqa: F401
import sierra.plugins.compare.graphs  # noqa: F401
import sierra.plugins.proc.imagize  # noqa: F401


def _prod(**over):
    g = {"src_stem": "s", "dest_stem": "d", "type": "histogram", "cols": ["a"]}
    g.update(over)
    return g


def _cmp(**over):
    g = {"src_stem": "s", "dest_stem": "d", "type": "comparison_line"}
    g.update(over)
    return g


class TestRegistry:
    def test_all_known_sections_are_registered_when_all_plugins_loaded(self):
        assert set(sections.registered()) == set(sections.KNOWN)

    def test_owners_match_declaration(self):
        for name, section in sections.registered().items():
            assert section.owner == sections.KNOWN[name]

    def test_shapes(self):
        reg = sections.registered()
        assert reg["intra-exp"].shape is sections.Shape.CATEGORIZED
        assert reg["inter-exp"].shape is sections.Shape.CATEGORIZED
        assert reg["inter-controller"].shape is sections.Shape.FLAT
        assert reg["inter-scenario"].shape is sections.Shape.FLAT
        assert reg["imagize"].shape is sections.Shape.FLAT

    def test_registration_is_idempotent(self):
        """Re-registering the identical section must not raise."""
        existing = sections.get("intra-exp")
        sections.register(existing)

    def test_conflicting_registration_rejected(self):
        existing = sections.get("intra-exp")
        conflicting = sections.Section(
            name="intra-exp",
            shape=sections.Shape.FLAT,
            by_type=existing.by_type,
            owner="somebody.else",
        )

        with pytest.raises(RuntimeError, match="already registered"):
            sections.register(conflicting)


class TestPerSectionTypes:
    """A section declares which graph types are legal *in it*."""

    def test_imagize_accepts_only_heatmap_and_network(self):
        assert set(sections.get("imagize").by_type) == {"heatmap", "network"}

    def test_imagize_reuses_prod_schemas_verbatim(self):
        """An imagized heatmap *is* a heatmap -- not a lookalike."""
        imagize = sections.get("imagize")
        prod = sections.get("intra-exp")

        assert imagize.by_type["heatmap"] is prod.by_type["heatmap"]
        assert imagize.by_type["network"] is prod.by_type["network"]

    def test_histogram_rejected_in_imagize(self):
        with pytest.raises(gconfig.ConfigError, match="not supported in this section"):
            gconfig.validate({"imagize": [_prod()]})

    def test_heatmap_accepted_in_imagize(self):
        out = gconfig.validate(
            {"imagize": [{"src_stem": "s", "dest_stem": "d", "type": "heatmap"}]}
        )
        assert len(out["imagize"]) == 1


class TestComparisonLineRename:
    def test_comparison_line_accepted_in_compare_sections(self):
        for name in ("inter-controller", "inter-scenario"):
            out = gconfig.validate({name: [_cmp()]})
            assert len(out[name]) == 1

    def test_old_summary_line_name_rejected_in_compare_sections(self):
        """The rename is a hard break -- no deprecation shim."""
        with pytest.raises(gconfig.ConfigError):
            gconfig.validate({"inter-controller": [_cmp(type="summary_line")]})

    def test_comparison_line_rejected_in_prod_sections(self):
        with pytest.raises(gconfig.ConfigError):
            gconfig.validate({"intra-exp": {"c": [_cmp()]}})

    def test_prod_and_compare_types_are_disjoint(self):
        prod = set(sections.get("intra-exp").by_type)
        compare = set(sections.get("inter-controller").by_type)

        assert not (prod & compare), "type names must not collide across plugins"


class TestShapeHandling:
    """Regression tests for the shape-handling crashers."""

    def test_flat_section_alone(self):
        """Previously NameError: 'category' leaked from the other branch."""
        out = gconfig.validate({"imagize": [{"src_stem": "s", "type": "network"}]})
        assert isinstance(out["imagize"], list)

    def test_mixed_shapes_in_one_file(self):
        """Previously AttributeError: .values() on a list section."""
        out = gconfig.validate(
            {
                "intra-exp": {"c": [_prod()]},
                "imagize": [{"src_stem": "s", "type": "network"}],
            }
        )
        assert isinstance(out["intra-exp"], dict)
        assert isinstance(out["imagize"], list)

    def test_flat_section_given_mapping_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="expected a list of graphs"):
            gconfig.validate({"imagize": {"cat": []}})

    def test_categorized_section_given_list_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="expected a mapping"):
            gconfig.validate({"intra-exp": [_prod()]})

    def test_flat_section_error_location_has_no_category(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate({"imagize": [{"src_stem": "s", "type": "bogus"}]})

        assert "imagize[0]" in str(e.value)


class TestUnknownSections:
    def test_truly_unknown_section_rejected(self):
        with pytest.raises(gconfig.ConfigError, match="unknown top-level section"):
            gconfig.validate({"not-a-section": []})

    def test_known_section_is_known_even_if_owner_unloaded(self):
        for name in sections.KNOWN:
            assert sections.is_known(name)

    def test_unknown_section_is_not_known(self):
        assert not sections.is_known("not-a-section")


class TestDefaults:
    def test_compare_defaults_materialized(self):
        out = gconfig.validate({"inter-controller": [_cmp()]})
        g = out["inter-controller"][0]

        assert g["title"] == ""
        assert g["label"] == ""
        assert g["primary_axis"] == 0
        assert g["index"] == -1

    def test_include_exp_defaults_to_whole_range(self):
        """':' is a no-op for exp_include_filter, so it is a safe default."""
        out = gconfig.validate({"inter-controller": [_cmp()]})

        assert out["inter-controller"][0]["include_exp"] == ":"

    def test_every_schema_key_is_defaulted_or_cmdline_derived(self):
        """No key requires a consumer-side default.

        The schema is the single source of truth for defaults: a key is either
        required, given a constant default here, or listed in CMDLINE_DEFAULTS
        because its fallback is a runtime value. Anything else would force a
        consumer back to .get(), which is what this arrangement exists to
        prevent.
        """
        out = gconfig.validate({"inter-controller": [_cmp()]})
        got = out["inter-controller"][0]

        declared = {str(k) for k in compareschema.comparison_line._validator_dict}
        missing = declared - set(got) - set(compareschema.CMDLINE_DEFAULTS)

        assert not missing, f"keys with no default and not cmdline-derived: {missing}"

    def test_resolve_fills_cmdline_derived_keys(self):
        out = gconfig.validate({"inter-controller": [_cmp()]})
        resolved = compareschema.resolve(
            out["inter-controller"][0], {"graphs_backend": "bokeh"}
        )

        assert resolved["backend"] == "bokeh"

    def test_resolve_does_not_override_explicit_value(self):
        out = gconfig.validate({"inter-controller": [_cmp(backend="matplotlib")]})
        resolved = compareschema.resolve(
            out["inter-controller"][0], {"graphs_backend": "bokeh"}
        )

        assert resolved["backend"] == "matplotlib"

    def test_resolve_does_not_mutate_input(self):
        out = gconfig.validate({"inter-controller": [_cmp()]})
        graph = out["inter-controller"][0]
        compareschema.resolve(graph, {"graphs_backend": "bokeh"})

        assert "backend" not in graph

    def test_index_is_int_not_str(self):
        out = gconfig.validate({"inter-controller": [_cmp(index=3)]})

        assert out["inter-controller"][0]["index"] == 3
        assert isinstance(out["inter-controller"][0]["index"], int)


class TestErrorAggregation:
    def test_problems_across_sections_reported_together(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate(
                {
                    "intra-exp": {"c": [_prod(type="bogus1")]},
                    "inter-controller": [_cmp(type="bogus2")],
                    "imagize": [{"src_stem": "s", "type": "histogram"}],
                }
            )

        assert len(e.value.problems) == 3

    def test_error_names_the_owning_plugin_on_shape_mismatch(self):
        with pytest.raises(gconfig.ConfigError) as e:
            gconfig.validate({"imagize": {"cat": []}})

        assert "proc.imagize" in str(e.value)
