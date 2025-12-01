# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Comprehensive test suite for YAML plugin
"""

# Core packages
import pathlib

# 3rd party packages
import pytest
import tempfile
import yaml

# Project packages
from sierra.core.experiment import definition
from sierra.plugins.expdef.yaml.plugin import ExpDef

################################################################################
# Test Fixtures - YAML Files
################################################################################


@pytest.fixture
def yaml_basic(tmp_path):
    """Basic YAML file with simple structure."""
    content = """
app:
  name: MyApp
  version: 1.0.0
  debug: false
  port: 8080

database:
  host: localhost
  port: 5432
  name: mydb
"""
    fpath = tmp_path / "basic.yaml"
    fpath.write_text(content)
    return fpath


@pytest.fixture
def yaml_nested(tmp_path):
    """YAML file with deeply nested structure."""
    content = """
app:
  name: NestedApp
  config:
    level1:
      level2:
        level3:
          value: deep
          number: 42
    settings:
      timeout: 30
      retries: 3
"""
    fpath = tmp_path / "nested.yaml"
    fpath.write_text(content)
    return fpath


@pytest.fixture
def yaml_with_lists(tmp_path):
    """YAML file with arrays/lists."""
    content = """
colors:
  - color: red
    value1: foo
  - color: green
    value1: "#0f0"
  - color: blue
    value: "#00f"
  - color: cyan
    value2: bar
  - color: magenta
    value1: "#f0f"
  - color: yellow
    value3: "#ff0"

servers:
  - name: server1
    ip: 192.168.1.1
  - name: server2
    ip: 192.168.1.2
"""
    fpath = tmp_path / "lists.yaml"
    fpath.write_text(content)
    return fpath


@pytest.fixture
def yaml_mixed_types(tmp_path):
    """YAML file with mixed data types."""
    content = """
config:
  string_val: "hello"
  int_val: 42
  float_val: 3.14
  bool_true: true
  bool_false: false
  null_val: null
  list_val:
    - item1
    - item2
  dict_val:
    key1: value1
    key2: value2
"""
    fpath = tmp_path / "mixed.yaml"
    fpath.write_text(content)
    return fpath


@pytest.fixture
def yaml_for_writing(tmp_path):
    """YAML file for testing write operations."""
    content = """
root:
  section1:
    data: value1
  section2:
    data: value2
  section3:
    subsection:
      data: value3
"""
    fpath = tmp_path / "write_test.yaml"
    fpath.write_text(content)
    return fpath


@pytest.fixture
def yaml_empty_sections(tmp_path):
    """YAML file with empty sections."""
    content = """
empty_dict: {}
empty_list: []
populated:
  key: value
"""
    fpath = tmp_path / "empty.yaml"
    fpath.write_text(content)
    return fpath


################################################################################
# Initialization Tests
################################################################################


class TestInitialization:
    """Test ExpDef initialization."""

    def test_load_basic_yaml(self, yaml_basic):
        """Test loading a basic YAML file."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.tree is not None
        assert "app" in expdef.tree
        assert "database" in expdef.tree

    def test_load_with_write_config(self, yaml_basic):
        """Test initialization with write config."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=yaml_basic, write_config=write_config)
        assert expdef.write_config is not None

    def test_processor_created(self, yaml_basic):
        """Test that processor is properly initialized."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.processor is not None

    def test_modifications_tracking(self, yaml_basic):
        """Test that modification tracking is initialized."""
        expdef = ExpDef(input_fpath=yaml_basic)
        adds, changes = expdef.n_mods()
        assert adds == 0
        assert changes == 0


################################################################################
# Attribute Get Tests
################################################################################


class TestAttrGet:
    """Test attr_get functionality."""

    def test_get_string_attr(self, yaml_basic):
        """Test getting a string attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        value = expdef.attr_get("app", "name")
        assert value == "MyApp"

    def test_get_number_attr(self, yaml_basic):
        """Test getting a numeric attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        value = expdef.attr_get("app", "port")
        assert value == 8080

    def test_get_bool_attr(self, yaml_basic):
        """Test getting a boolean attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        value = expdef.attr_get("app", "debug")
        assert value is False

    def test_get_nonexistent_attr(self, yaml_basic):
        """Test getting a non-existent attribute returns None."""
        expdef = ExpDef(input_fpath=yaml_basic)
        value = expdef.attr_get("app", "nonexistent")
        assert value is None

    def test_get_nested_attr(self, yaml_nested):
        """Test getting a deeply nested attribute."""
        expdef = ExpDef(input_fpath=yaml_nested)

        value = expdef.attr_get("/app/config/level1/level2/level3", "value")
        assert value == "deep"

    def test_get_attr_nonexistent_path(self, yaml_basic):
        """Test getting attribute from non-existent path."""
        expdef = ExpDef(input_fpath=yaml_basic)
        value = expdef.attr_get("nonexistent/path", "attr")
        assert value is None

    def test_get_container_not_attr(self, yaml_basic):
        """Test that containers are not returned as attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)
        # 'database' is a dict, not a scalar attribute
        value = expdef.attr_get("", "database")
        assert value is None


################################################################################
# Attribute Change Tests
################################################################################


class TestAttrChange:
    """Test attr_change functionality."""

    def test_change_string_attr(self, yaml_basic):
        """Test changing a string attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_change("app", "name", "NewApp")
        assert result is True
        assert expdef.attr_get("app", "name") == "NewApp"

    def test_change_number_attr(self, yaml_basic):
        """Test changing a numeric attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_change("app", "port", 9090)
        assert result is True
        assert expdef.attr_get("app", "port") == 9090

    def test_change_bool_attr(self, yaml_basic):
        """Test changing a boolean attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_change("app", "debug", True)
        assert result is True
        assert expdef.attr_get("app", "debug") is True

    def test_change_tracks_modification(self, yaml_basic):
        """Test that changes are tracked."""
        expdef = ExpDef(input_fpath=yaml_basic)
        expdef.attr_change("app", "name", "NewApp")
        adds, changes = expdef.n_mods()
        assert changes == 1

    def test_change_nonexistent_path(self, yaml_basic):
        """Test changing attribute in non-existent path fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_change("nonexistent", "attr", "value")
        assert result is False

    def test_change_nonexistent_attr(self, yaml_basic):
        """Test changing non-existent attribute fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_change("app", "nonexistent", "value")
        assert result is False

    def test_change_nested_attr(self, yaml_nested):
        """Test changing a deeply nested attribute."""
        expdef = ExpDef(input_fpath=yaml_nested)
        result = expdef.attr_change(
            "/app/config/level1/level2/level3", "value", "shallow"
        )
        assert result is True
        assert expdef.attr_get("/app/config/level1/level2/level3", "value") == "shallow"

    def test_change_multiple_occurrences(self, yaml_with_lists):
        """Test changing attribute in multiple matching elements."""
        expdef = ExpDef(input_fpath=yaml_with_lists)
        # Change all 'name' attributes in servers
        result = expdef.attr_change("/servers[name%server]", "name", "updated")
        assert result is True


################################################################################
# Attribute Add Tests
################################################################################


class TestAttrAdd:
    """Test attr_add functionality."""

    def test_add_new_attr(self, yaml_basic):
        """Test adding a new attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_add("app", "timeout", 30)
        assert result is True
        assert expdef.attr_get("app", "timeout") == 30

    def test_add_tracks_modification(self, yaml_basic):
        """Test that additions are tracked."""
        expdef = ExpDef(input_fpath=yaml_basic)
        expdef.attr_add("app", "timeout", 30)
        adds, changes = expdef.n_mods()
        assert changes == 1

    def test_add_duplicate_attr_fails(self, yaml_basic):
        """Test that adding duplicate attribute fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_add("app", "name", "AnotherName")
        assert result is False

    def test_add_to_nonexistent_path(self, yaml_basic):
        """Test adding to non-existent path fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_add("nonexistent", "attr", "value")
        assert result is False

    def test_add_nested_attr(self, yaml_nested):
        """Test adding attribute to nested path."""
        expdef = ExpDef(input_fpath=yaml_nested)
        result = expdef.attr_add("/app/config/settings", "cache_size", 100)
        assert result is True
        assert expdef.attr_get("/app/config/settings", "cache_size") == 100

    def test_add_string_attr(self, yaml_basic):
        """Test adding string attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_add("/app", "environment", "production")
        assert result is True
        assert expdef.attr_get("/app", "environment") == "production"

    def test_add_number_attr(self, yaml_basic):
        """Test adding numeric attribute."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.attr_add("/database", "max_connections", 100)
        assert result is True
        assert expdef.attr_get("/database", "max_connections") == 100


################################################################################
# Has Element Tests
################################################################################


class TestHasElement:
    """Test has_element functionality."""

    def test_has_dict_element(self, yaml_basic):
        """Test detecting dict elements."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.has_element("app") is True
        assert expdef.has_element("database") is True

    def test_has_list_element(self, yaml_with_lists):
        """Test detecting list elements."""
        expdef = ExpDef(input_fpath=yaml_with_lists)
        assert expdef.has_element("colors") is True
        assert expdef.has_element("servers") is True

    def test_has_nested_element(self, yaml_nested):
        """Test detecting nested elements."""
        expdef = ExpDef(input_fpath=yaml_nested)
        assert expdef.has_element("/app/config") is True
        assert expdef.has_element("/app/config/level1/level2") is True

    def test_scalar_not_element(self, yaml_basic):
        """Test that scalar values are not elements."""
        expdef = ExpDef(input_fpath=yaml_basic)
        # These are attributes (scalars), not elements
        assert expdef.has_element("/app/name") is False
        assert expdef.has_element("/app/port") is False

    def test_nonexistent_element(self, yaml_basic):
        """Test non-existent element returns False."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.has_element("nonexistent") is False

    def test_empty_dict_is_element(self, yaml_empty_sections):
        """Test that empty dict is still an element."""
        expdef = ExpDef(input_fpath=yaml_empty_sections)
        assert expdef.has_element("empty_dict") is True

    def test_empty_list_is_element(self, yaml_empty_sections):
        """Test that empty list is still an element."""
        expdef = ExpDef(input_fpath=yaml_empty_sections)
        assert expdef.has_element("empty_list") is True


################################################################################
# Has Attribute Tests
################################################################################


class TestHasAttr:
    """Test has_attr functionality."""

    def test_has_existing_attr(self, yaml_basic):
        """Test detecting existing attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.has_attr("app", "name") is True
        assert expdef.has_attr("app", "port") is True
        assert expdef.has_attr("database", "host") is True

    def test_has_nonexistent_attr(self, yaml_basic):
        """Test non-existent attribute returns False."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.has_attr("app", "nonexistent") is False

    def test_has_nested_attr(self, yaml_nested):
        """Test detecting nested attributes."""
        expdef = ExpDef(input_fpath=yaml_nested)
        assert expdef.has_attr("/app/config/level1/level2/level3", "value") is True
        assert expdef.has_attr("/app/config/settings", "timeout") is True

    def test_container_not_attr(self, yaml_basic):
        """Test that containers are not considered attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)
        # 'config' in nested yaml is a dict, not a scalar attribute
        # This should return False
        assert expdef.has_attr("app", "database") is False

    def test_has_attr_in_list_element(self, yaml_with_lists):
        """Test detecting attribute in list elements."""
        expdef = ExpDef(input_fpath=yaml_with_lists)
        assert expdef.has_attr('/colors[color=="cyan"]', "color") is True
        assert expdef.has_attr('/colors[color=="cyan"]', "value2") is True

    def test_has_attr_nonexistent_path(self, yaml_basic):
        """Test has_attr with non-existent path."""
        expdef = ExpDef(input_fpath=yaml_basic)
        assert expdef.has_attr("nonexistent/path", "attr") is False


################################################################################
# Element Change Tests
################################################################################


class TestElementChange:
    """Test element_change functionality."""

    def test_change_element_tag(self, yaml_basic):
        """Test changing an element tag (renaming key)."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_change("", "app", "application")
        assert result is True
        assert expdef.has_element("application") is True
        assert expdef.has_element("app") is False

    def test_change_nested_element_tag(self, yaml_nested):
        """Test changing nested element tag."""
        expdef = ExpDef(input_fpath=yaml_nested)
        result = expdef.element_change("/app/config", "level1", "layer1")
        assert result is True
        assert expdef.has_element("/app/config/layer1") is True

    def test_change_preserves_subtree(self, yaml_nested):
        """Test that changing tag preserves subtree."""
        expdef = ExpDef(input_fpath=yaml_nested)
        old_value = expdef.attr_get("/app/config/level1/level2/level3", "value")
        expdef.element_change("/app/config", "level1", "layer1")
        new_value = expdef.attr_get("/app/config/layer1/level2/level3", "value")
        assert old_value == new_value

    def test_change_nonexistent_tag(self, yaml_basic):
        """Test changing non-existent tag fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_change("/app", "nonexistent", "newtag")
        assert result is False

    def test_change_nonexistent_path(self, yaml_basic):
        """Test changing tag in non-existent path fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_change("/nonexistent", "tag", "newtag")
        assert result is False


################################################################################
# Element Remove Tests
################################################################################


class TestElementRemove:
    """Test element_remove functionality."""

    def test_remove_element(self, yaml_basic):
        """Test removing an element."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_remove("", "database")
        assert result is True
        assert expdef.has_element("database") is False

    def test_remove_nested_element(self, yaml_nested):
        """Test removing nested element."""
        expdef = ExpDef(input_fpath=yaml_nested)
        result = expdef.element_remove("/app/config", "level1")
        assert result is True
        assert expdef.has_element("/app/config/level1") is False

    def test_remove_nonexistent_element(self, yaml_basic):
        """Test removing non-existent element fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_remove("/app", "nonexistent")
        assert result is False

    def test_remove_from_nonexistent_path(self, yaml_basic):
        """Test removing from non-existent path fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_remove("/nonexistent", "element")
        assert result is False

    def test_remove_with_noprint(self, yaml_basic):
        """Test remove with noprint flag."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_remove("/app", "nonexistent", noprint=True)
        assert result is False


################################################################################
# Element Add Tests
################################################################################


class TestElementAdd:
    """Test element_add functionality."""

    def test_add_simple_element(self, yaml_basic):
        """Test adding a simple element."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_add("/app", "cache", {"enabled": True, "ttl": 3600})
        assert result is True
        assert expdef.has_element("/app/cache") is True

    def test_add_element_tracks_modification(self, yaml_basic):
        """Test that element addition is tracked."""
        expdef = ExpDef(input_fpath=yaml_basic)
        expdef.element_add("/app", "cache", {"enabled": True})
        adds, changes = expdef.n_mods()
        assert adds == 1

    def test_add_duplicate_not_allowed(self, yaml_basic):
        """Test adding duplicate element with allow_dup=False."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_add("/", "app", {"name": "test"}, allow_dup=False)
        assert result is False

    def test_add_duplicate_creates_list(self, yaml_basic):
        """Test adding duplicate element with allow_dup=True creates list."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_add("/", "database", {"host": "backup"}, allow_dup=True)
        assert result is True

    def test_add_to_nested_path(self, yaml_nested):
        """Test adding element to nested path."""
        expdef = ExpDef(input_fpath=yaml_nested)
        result = expdef.element_add(
            "/app/config/settings", "logging", {"level": "INFO"}
        )
        assert result is True
        assert expdef.has_element("/app/config/settings/logging") is True

    def test_add_empty_element(self, yaml_basic):
        """Test adding element with None attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_add("/app", "new_section", None)
        assert result is True

    def test_add_to_nonexistent_path(self, yaml_basic):
        """Test adding to non-existent path fails."""
        expdef = ExpDef(input_fpath=yaml_basic)
        result = expdef.element_add("/nonexistent", "element", {})
        assert result is False


################################################################################
# Write Tests
################################################################################


class TestWrite:
    """Test write functionality."""

    def test_write_entire_tree(self, yaml_basic, tmp_path):
        """Test writing entire YAML tree."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=yaml_basic, write_config=write_config)

        output = tmp_path / "output.yaml"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = yaml.safe_load(f)
        assert "name" in data
        assert data["name"] == "MyApp"

    def test_write_section(self, yaml_for_writing, tmp_path):
        """Test writing specific section."""
        write_config = definition.WriterConfig(
            [{"src_parent": "/root", "src_tag": "section1"}]
        )
        expdef = ExpDef(input_fpath=yaml_for_writing, write_config=write_config)

        output = tmp_path / "section1.yaml"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = yaml.safe_load(f)
        assert "data" in data
        assert data["data"] == "value1"

    def test_write_nested_section(self, yaml_for_writing, tmp_path):
        """Test writing nested section."""
        write_config = definition.WriterConfig(
            [{"src_parent": "/root/section3", "src_tag": "subsection"}]
        )
        expdef = ExpDef(input_fpath=yaml_for_writing, write_config=write_config)

        output = tmp_path / "subsection.yaml"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = yaml.safe_load(f)
        assert "data" in data

    def test_write_with_custom_name(self, yaml_basic, tmp_path):
        """Test writing with custom output filename."""
        write_config = definition.WriterConfig(
            [{"src_parent": None, "src_tag": "app", "opath_leaf": "-custom"}]
        )
        expdef = ExpDef(input_fpath=yaml_basic, write_config=write_config)

        output = tmp_path / "output.yaml"
        expdef.write(output)

        expected = tmp_path / "output.yaml-custom"
        assert expected.exists()

    def test_write_after_modifications(self, yaml_basic, tmp_path):
        """Test writing after making modifications."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=yaml_basic, write_config=write_config)

        # Make modifications
        expdef.attr_change("/app", "name", "ModifiedApp")
        expdef.attr_add("/app", "timeout", 30)

        output = tmp_path / "modified.yaml"
        expdef.write(output)

        # Verify modifications persisted
        with open(output) as f:
            data = yaml.safe_load(f)
        assert data["name"] == "ModifiedApp"
        assert data["timeout"] == 30

    def test_write_without_config_fails(self, yaml_basic, tmp_path):
        """Test that writing without config raises error."""
        expdef = ExpDef(input_fpath=yaml_basic)  # No write_config

        output = tmp_path / "output.yaml"
        with pytest.raises(ValueError, match="Can't write without write config"):
            expdef.write(output)

    def test_write_config_set(self, yaml_basic):
        """Test setting write config after initialization."""
        expdef = ExpDef(input_fpath=yaml_basic)

        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef.write_config_set(write_config)

        assert expdef.write_config is not None


################################################################################
# Complex Scenario Tests
################################################################################


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_modify_multiple_attributes(self, yaml_basic):
        """Test modifying multiple attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)

        expdef.attr_change("/app", "name", "UpdatedApp")
        expdef.attr_change("/app", "version", "2.0.0")
        expdef.attr_change("/app", "debug", True)
        expdef.attr_change("/database", "host", "db.example.com")

        assert expdef.attr_get("/app", "name") == "UpdatedApp"
        assert expdef.attr_get("/app", "version") == "2.0.0"
        assert expdef.attr_get("/app", "debug") is True
        assert expdef.attr_get("/database", "host") == "db.example.com"

    def test_add_and_modify(self, yaml_basic):
        """Test adding then modifying attributes."""
        expdef = ExpDef(input_fpath=yaml_basic)

        # Add new attribute
        expdef.attr_add("/app", "timeout", 30)
        assert expdef.attr_get("/app", "timeout") == 30

        # Modify the newly added attribute
        expdef.attr_change("/app", "timeout", 60)
        assert expdef.attr_get("app", "timeout") == 60

    def test_restructure_tree(self, yaml_basic):
        """Test restructuring the YAML tree."""
        expdef = ExpDef(input_fpath=yaml_basic)

        # Add new section
        expdef.element_add("/", "logging", {"level": "INFO", "file": "app.log"})

        # Remove old section
        expdef.element_remove("/", "database")

        # Verify changes
        assert expdef.has_element("/logging") is True
        assert expdef.has_element("/database") is False

    def test_work_with_array_elements(self, yaml_with_lists):
        """Test operations on array elements."""
        expdef = ExpDef(input_fpath=yaml_with_lists)

        # Check specific element
        assert expdef.has_attr('/colors[color=="cyan"]', "value2") is True

        # Modify attribute in array element
        expdef.attr_change('/colors[color=="cyan"]', "value2", "updated")
        assert expdef.attr_get('/colors[color=="cyan"]', "value2") == "updated"

    def test_deep_nesting_operations(self, yaml_nested):
        """Test operations on deeply nested structures."""
        expdef = ExpDef(input_fpath=yaml_nested)

        # Modify deep value
        expdef.attr_change("/app/config/level1/level2/level3", "value", "very_deep")

        # Add to deep path
        expdef.attr_add("/app/config/level1/level2/level3", "new_value", "added_deep")

        # Verify
        assert (
            expdef.attr_get("/app/config/level1/level2/level3", "value") == "very_deep"
        )
        assert (
            expdef.attr_get("/app/config/level1/level2/level3", "new_value")
            == "added_deep"
        )

    def test_modification_tracking(self, yaml_basic):
        """Test that all modifications are tracked correctly."""
        expdef = ExpDef(input_fpath=yaml_basic)

        # Make various modifications
        expdef.attr_change("app", "name", "NewApp")
        expdef.attr_add("app", "timeout", 30)
        expdef.element_add("", "cache", {"enabled": True})
        expdef.attr_change("database", "host", "newhost")

        adds, changes = expdef.n_mods()
        assert adds == 1  # One element add
        assert changes == 3  # Three attribute changes + one attribute add


################################################################################
# Edge Cases and Error Handling
################################################################################


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_path(self, yaml_basic):
        """Test operations with empty path."""
        expdef = ExpDef(input_fpath=yaml_basic)

        # Empty path refers to root
        assert expdef.has_element("") is True

        # Can add to root
        result = expdef.element_add("", "newroot", {"key": "value"})
        assert result is True

    def test_special_characters_in_values(self, tmp_path):
        """Test handling special characters."""
        content = """
special:
  quotes: "value with 'quotes'"
  symbols: "@#$%^&*()"
  unicode: "café résumé"
"""
        fpath = tmp_path / "special.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.attr_get("special", "quotes") is not None
        assert expdef.attr_get("special", "symbols") == "@#$%^&*()"

    def test_null_values(self, yaml_mixed_types):
        """Test handling null/None values."""
        expdef = ExpDef(input_fpath=yaml_mixed_types)
        value = expdef.attr_get("config", "null_val")
        assert value is None

    def test_numeric_string_distinction(self, tmp_path):
        """Test distinguishing between numbers and numeric strings."""
        content = """
values:
  number: 123
  string: "123"
  float: 45.67
  string_float: "45.67"
"""
        fpath = tmp_path / "numeric.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.attr_get("values", "number") == 123
        assert expdef.attr_get("values", "string") == "123"

    def test_large_numbers(self, tmp_path):
        """Test handling large numbers."""
        content = """
big_numbers:
  large_int: 999999999999999
  large_float: 1.23e10
"""
        fpath = tmp_path / "large.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.attr_get("big_numbers", "large_int") == 999999999999999

    def test_multiline_strings(self, tmp_path):
        """Test handling multiline strings."""
        content = """
multiline:
  literal: |
    Line 1
    Line 2
    Line 3
  folded: >
    This is a
    folded string
"""
        fpath = tmp_path / "multiline.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        literal = expdef.attr_get("multiline", "literal")
        assert literal is not None
        assert "Line 1" in literal


################################################################################
# Performance and Stress Tests
################################################################################


class TestPerformance:
    """Test performance with larger structures."""

    def test_large_array(self, tmp_path):
        """Test handling large arrays."""
        # Create YAML with 1000 items
        items = [f"  - item: item{i}\n    value: {i}" for i in range(1000)]
        content = "items:\n" + "\n".join(items)

        fpath = tmp_path / "large_array.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.has_element("items") is True

    def test_many_modifications(self, yaml_basic):
        """Test making many modifications."""
        expdef = ExpDef(input_fpath=yaml_basic)

        # Add 100 attributes
        for i in range(100):
            expdef.attr_add("app", f"attr{i}", i)

        adds, changes = expdef.n_mods()
        assert changes == 100

        # Verify some additions
        assert expdef.attr_get("app", "attr0") == 0
        assert expdef.attr_get("app", "attr99") == 99

    def test_deep_nesting_limit(self, tmp_path):
        """Test very deep nesting."""
        # Create deeply nested structure
        content = "level0:\n"
        indent = "  "
        for i in range(1, 20):
            content += f"{indent * i}level{i}:\n"
        content += f"{indent * 20}value: deep"

        fpath = tmp_path / "deep.yaml"
        fpath.write_text(content)

        expdef = ExpDef(input_fpath=fpath)
        path = "/" + "/".join([f"level{i}" for i in range(20)])

        assert expdef.has_attr(path, "value") is True
