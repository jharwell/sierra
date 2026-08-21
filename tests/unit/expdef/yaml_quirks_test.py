#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""YAML-specific expdef behavior.

Universal contract lives in ``conformance_test.py``. This file holds only
YAML-specific behavior: scalar arrays (which YAML returns as sequence objects,
hence the ``list(...)`` coercions), list-element selection syntax, and
include-flattening.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest
import yaml as pyyaml

# Project packages
from sierra.plugins.expdef.yaml import plugin as yaml_plugin

ExpDef = yaml_plugin.ExpDef

_SCALAR_ARRAYS = """
net:
  host: localhost
  ports: [80, 443]
  aliases: [web, www]
matrix:
  rows:
    - [1, 2]
    - [3, 4]
"""

_WITH_LISTS = """
colors:
  - {color: cyan, value2: 1}
  - {color: magenta, value2: 2}
servers:
  - {name: server, port: 8080}
  - {name: server, port: 8081}
"""


@pytest.fixture
def scalar_arrays(tmp_path):
    p = tmp_path / "scalar_arrays.yaml"
    p.write_text(_SCALAR_ARRAYS)
    return ExpDef(input_fpath=p)


@pytest.fixture
def with_lists(tmp_path):
    p = tmp_path / "with_lists.yaml"
    p.write_text(_WITH_LISTS)
    return ExpDef(input_fpath=p)


class TestScalarArrays:
    def test_get_scalar_array(self, scalar_arrays):
        assert list(scalar_arrays.attr_get("net", "ports")) == [80, 443]

    def test_get_string_array(self, scalar_arrays):
        assert list(scalar_arrays.attr_get("net", "aliases")) == ["web", "www"]

    def test_has_attr_scalar_array(self, scalar_arrays):
        assert scalar_arrays.has_attr("net", "ports") is True

    def test_scalar_array_not_element(self, scalar_arrays):
        assert scalar_arrays.has_element("/net/ports") is False

    def test_change_scalar_array(self, scalar_arrays):
        assert scalar_arrays.attr_change("net", "ports", [8080, 8443]) is True
        assert list(scalar_arrays.attr_get("net", "ports")) == [8080, 8443]

    def test_change_scalar_to_array(self, scalar_arrays):
        assert scalar_arrays.attr_change("net", "host", ["a", "b"]) is True
        assert list(scalar_arrays.attr_get("net", "host")) == ["a", "b"]

    def test_change_array_to_scalar(self, scalar_arrays):
        assert scalar_arrays.attr_change("net", "ports", 8080) is True
        assert scalar_arrays.attr_get("net", "ports") == 8080

    def test_add_scalar_array(self, scalar_arrays):
        assert scalar_arrays.attr_add("net", "backends", ["x", "y", "z"]) is True
        assert list(scalar_arrays.attr_get("net", "backends")) == ["x", "y", "z"]


class TestListElements:
    def test_has_list_element(self, with_lists):
        assert with_lists.has_element("colors") is True
        assert with_lists.has_element("servers") is True

    def test_has_attr_in_list_element(self, with_lists):
        assert with_lists.has_attr('/colors[color=="cyan"]', "color") is True
        assert with_lists.has_attr('/colors[color=="cyan"]', "value2") is True
