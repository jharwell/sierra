#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""XML-specific expdef behavior.

The universal ExpDef contract is tested once in ``conformance_test.py``. This file
holds only behavior that is genuinely specific to the XML backend and therefore
does NOT belong in the shared suite:

* XML attribute values are always strings, so assigning a list/dict must be
  rejected rather than silently stringified.
* ``flatten`` is not supported by XML and must raise NotImplementedError.
* duplicate-tag handling and ``element_remove_all``.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from sierra.plugins.expdef.xml import plugin as xml


_SIMPLE = """<?xml version="1.0"?>
<root>
  <config>
    <parameter name="value1" type="int">10</parameter>
  </config>
</root>"""

_DUPLICATES = """<?xml version="1.0"?>
<root>
  <collection>
    <item id="1" name="first"/>
    <item id="2" name="second"/>
    <item id="3" name="third"/>
    <group><item id="4" name="nested"/></group>
  </collection>
</root>"""


@pytest.fixture
def simple(tmp_path):
    p = tmp_path / "simple.xml"
    p.write_text(_SIMPLE)
    return xml.ExpDef(p)


@pytest.fixture
def duplicates(tmp_path):
    p = tmp_path / "dup.xml"
    p.write_text(_DUPLICATES)
    return xml.ExpDef(p)


class TestNonScalarRejection:
    """XML attributes cannot hold arrays/objects."""

    def test_change_list_rejected(self, simple):
        assert simple.attr_change("config/parameter", "name", [80, 443]) is False
        assert simple.attr_get("config/parameter", "name") == "value1"

    def test_change_dict_rejected(self, simple):
        assert simple.attr_change("config/parameter", "name", {"a": 1}) is False

    def test_add_list_rejected(self, simple):
        assert simple.attr_add("config/parameter", "ports", [80, 443]) is False
        assert simple.has_attr("config/parameter", "ports") is False

    def test_add_dict_rejected(self, simple):
        assert simple.attr_add("config/parameter", "opts", {"a": 1}) is False

    def test_scalar_still_works(self, simple):
        assert simple.attr_change("config/parameter", "name", "renamed") is True


class TestFlattenUnsupported:
    def test_flatten_raises(self, simple):
        with pytest.raises(NotImplementedError):
            simple.flatten(["key1", "key2"])


class TestElementRemoveAll:
    def test_remove_all_duplicates(self, duplicates):
        # Precondition: collection has direct <item> children to remove.
        assert duplicates.has_element(".//collection/item") is True
        duplicates.element_remove_all(".//collection", "item")
        # Post-condition: every direct <item> child of collection is gone. The
        # nested <group><item/> is NOT a direct child, so it must survive.
        assert duplicates.has_element(".//collection/item") is False
        assert duplicates.has_element(".//collection/group/item") is True

    def test_remove_all_nonexistent_parent(self, duplicates):
        assert duplicates.element_remove_all(".//nonexistent", "child") is False

    def test_remove_all_no_matches(self, simple):
        assert simple.element_remove_all(".//config", "nonexistent") is not True

    def test_remove_all_noprint(self, duplicates):
        assert (
            duplicates.element_remove_all(".//nonexistent", "child", noprint=True)
            is False
        )
