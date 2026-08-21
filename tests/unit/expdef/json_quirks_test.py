#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""JSON-specific expdef behavior.

Universal contract lives in ``conformance_test.py``. This file holds only
JSON-specific behavior: real array-valued attributes (scalar arrays), the
element-vs-attribute distinction for nested arrays, include-flattening, and the
logic-error regressions that were specific to the JSON tree model.
"""

# Core packages
import json
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.expdef.json import plugin as json_plugin

ExpDef = json_plugin.ExpDef


@pytest.fixture
def scalar_arrays(tmp_path):
    content = {
        "net": {"host": "localhost", "ports": [80, 443], "aliases": ["web", "www"]},
        "matrix": {"rows": [[1, 2], [3, 4]]},
        "services": [
            {"name": "svc1", "tags": ["a", "b"]},
            {"name": "svc2", "tags": ["c"]},
        ],
    }
    p = tmp_path / "scalar_arrays.json"
    p.write_text(json.dumps(content, indent=2))
    return ExpDef(input_fpath=p)


@pytest.fixture
def for_flatten(tmp_path):
    main = {"main": {"name": "MainConfig", "include": "subconfig.json"},
            "settings": {"timeout": 30}}
    sub = {"sub": {"value": "from_subconfig", "number": 123}}
    (tmp_path / "subconfig.json").write_text(json.dumps(sub, indent=2))
    main_path = tmp_path / "main.json"
    main_path.write_text(json.dumps(main, indent=2))
    return ExpDef(input_fpath=main_path)


class TestScalarArrays:
    def test_get_scalar_array(self, scalar_arrays):
        assert scalar_arrays.attr_get("$.net", "ports") == [80, 443]

    def test_get_string_array(self, scalar_arrays):
        assert scalar_arrays.attr_get("$.net", "aliases") == ["web", "www"]

    def test_has_attr_scalar_array(self, scalar_arrays):
        assert scalar_arrays.has_attr("$.net", "ports") is True

    def test_scalar_array_not_element(self, scalar_arrays):
        assert scalar_arrays.has_element("$.net.ports") is False

    def test_change_scalar_array(self, scalar_arrays):
        assert scalar_arrays.attr_change("$.net", "ports", [8080, 8443]) is True
        assert scalar_arrays.attr_get("$.net", "ports") == [8080, 8443]

    def test_change_scalar_to_array(self, scalar_arrays):
        assert scalar_arrays.attr_change("$.net", "host", ["a", "b"]) is True
        assert scalar_arrays.attr_get("$.net", "host") == ["a", "b"]

    def test_change_array_to_scalar(self, scalar_arrays):
        assert scalar_arrays.attr_change("$.net", "ports", 8080) is True
        assert scalar_arrays.attr_get("$.net", "ports") == 8080

    def test_add_scalar_array(self, scalar_arrays):
        assert scalar_arrays.attr_add("$.net", "backends", ["x", "y", "z"]) is True
        assert scalar_arrays.attr_get("$.net", "backends") == ["x", "y", "z"]

    def test_nested_array_is_element(self, scalar_arrays):
        assert scalar_arrays.has_element("$.matrix.rows") is True
        assert scalar_arrays.has_attr("$.matrix", "rows") is False

    def test_change_refuses_element_clobber(self, scalar_arrays):
        assert scalar_arrays.attr_change("$.matrix", "rows", [1, 2, 3]) is False


class TestFlatten:
    def test_flatten_resolves_include(self, for_flatten):
        for_flatten.flatten(["include"])
        # after flatten the include key is gone from main
        assert "include" not in for_flatten.tree["main"]

    def test_flatten_preserves_other_keys(self, for_flatten):
        for_flatten.flatten(["include"])
        assert for_flatten.tree["settings"]["timeout"] == 30


class TestLogicErrorRegressions:
    def test_multi_match_no_partial_mutation(self, tmp_path):
        content = {"items": [{"id": "a", "speed": 1}, {"id": "b"}]}
        p = tmp_path / "multi.json"
        p.write_text(json.dumps(content))
        expdef = ExpDef(input_fpath=p)
        # a change that cannot apply to every match must not partially apply
        _, chgs_before = expdef.n_mods()
        expdef.attr_change("$.items[*]", "speed", 99)
        # first item must remain untouched at 1
        assert expdef.attr_get("$.items[0]", "speed") in (1, "1")


@pytest.fixture
def remove_all_basic(tmp_path):
    """Basic doc for element_remove_all, mirroring json_test's json_basic."""
    content = {
        "app": {"name": "MyApp", "version": "1.0.0", "debug": False, "port": 8080},
        "database": {"host": "localhost", "port": 5432, "name": "mydb"},
    }
    p = tmp_path / "remove_all.json"
    p.write_text(json.dumps(content, indent=2))
    return ExpDef(input_fpath=p)


class TestElementRemoveAll:
    """JSON-specific: ``element_remove_all`` uses the ``$``-rooted path syntax.

    ``element_remove_all`` is backend-specific — the XML form lives in
    ``xml_quirks_test.py`` — so its JSON cases belong here rather than in the
    universal conformance suite.
    """

    def test_remove_all_single_match(self, remove_all_basic):
        assert remove_all_basic.element_remove_all("$", "database") is True
        assert remove_all_basic.has_element("$.database") is False

    def test_remove_all_no_match_returns_false(self, remove_all_basic):
        assert remove_all_basic.element_remove_all("$.app", "nonexistent") is False

    def test_remove_all_from_nonexistent_path(self, remove_all_basic):
        assert remove_all_basic.element_remove_all("$.nonexistent", "element") is False
