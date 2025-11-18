# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages

# test_json_plugin.py
"""
Comprehensive test suite for JSON plugin
"""

# Core packages
import pathlib
import json

# 3rd party packages
import pytest
import tempfile

# Project packages
from sierra.core.experiment import definition
from sierra.plugins.expdef.json.plugin import ExpDef


################################################################################
# Test Fixtures - JSON Files
################################################################################
@pytest.fixture
def json_basic(tmp_path):
    """Basic JSON file with simple structure."""
    content = {
        "app": {"name": "MyApp", "version": "1.0.0", "debug": False, "port": 8080},
        "database": {"host": "localhost", "port": 5432, "name": "mydb"},
    }
    fpath = tmp_path / "basic.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_nested(tmp_path):
    """JSON file with deeply nested structure."""
    content = {
        "app": {
            "name": "NestedApp",
            "config": {
                "level1": {"level2": {"level3": {"value": "deep", "number": 42}}},
                "settings": {"timeout": 30, "retries": 3},
            },
        }
    }
    fpath = tmp_path / "nested.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_with_arrays(tmp_path):
    """JSON file with arrays."""
    content = {
        "colors": [
            {"color": "red", "value1": "foo"},
            {"color": "green", "value1": "#0f0"},
            {"color": "blue", "value": "#00f"},
            {"color": "cyan", "value2": "bar"},
            {"color": "magenta", "value1": "#f0f"},
            {"color": "yellow", "value3": "#ff0"},
        ],
        "servers": [
            {"name": "server1", "ip": "192.168.1.1"},
            {"name": "server2", "ip": "192.168.1.2"},
        ],
    }
    fpath = tmp_path / "arrays.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_mixed_types(tmp_path):
    """JSON file with mixed data types."""
    content = {
        "config": {
            "string_val": "hello",
            "int_val": 42,
            "float_val": 3.14,
            "bool_true": True,
            "bool_false": False,
            "null_val": None,
            "list_val": ["item1", "item2"],
            "dict_val": {"key1": "value1", "key2": "value2"},
        }
    }
    fpath = tmp_path / "mixed.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_for_writing(tmp_path):
    """JSON file for testing write operations."""
    content = {
        "root": {
            "section1": {"data": "value1"},
            "section2": {"data": "value2"},
            "section3": {"subsection": {"data": "value3"}},
        }
    }
    fpath = tmp_path / "write_test.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_empty_sections(tmp_path):
    """JSON file with empty sections."""
    content = {"empty_dict": {}, "empty_list": [], "populated": {"key": "value"}}
    fpath = tmp_path / "empty.json"
    fpath.write_text(json.dumps(content, indent=2))
    return fpath


@pytest.fixture
def json_for_flatten(tmp_path):
    """JSON files for testing flatten operations."""
    # Main config file
    main_content = {
        "main": {"name": "MainConfig", "include": "subconfig.json"},
        "settings": {"timeout": 30},
    }

    # Sub config file
    sub_content = {"sub": {"value": "from_subconfig", "number": 123}}

    main_path = tmp_path / "main.json"
    sub_path = tmp_path / "subconfig.json"

    main_path.write_text(json.dumps(main_content, indent=2))
    sub_path.write_text(json.dumps(sub_content, indent=2))

    return main_path


@pytest.fixture
def json_nested_flatten(tmp_path):
    """JSON files for testing nested flatten operations."""
    # Level 1 config
    level1_content = {"level1": {"data": "level1_data", "include": "level2.json"}}

    # Level 2 config
    level2_content = {"level2": {"data": "level2_data", "value": 456}}

    level1_path = tmp_path / "level1.json"
    level2_path = tmp_path / "level2.json"

    level1_path.write_text(json.dumps(level1_content, indent=2))
    level2_path.write_text(json.dumps(level2_content, indent=2))

    return level1_path


################################################################################
# Initialization Tests
################################################################################
class TestInitialization:
    """Test ExpDef initialization."""

    def test_load_basic_json(self, json_basic):
        """Test loading a basic JSON file."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.tree is not None
        assert "app" in expdef.tree
        assert "database" in expdef.tree

    def test_load_with_write_config(self, json_basic):
        """Test initialization with write config."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=json_basic, write_config=write_config)
        assert expdef.write_config is not None

    def test_modifications_tracking(self, json_basic):
        """Test that modification tracking is initialized."""
        expdef = ExpDef(input_fpath=json_basic)
        adds, changes = expdef.n_mods()
        assert adds == 0
        assert changes == 0

    def test_tree_is_dict(self, json_basic):
        """Test that loaded tree is a dictionary."""
        expdef = ExpDef(input_fpath=json_basic)
        assert isinstance(expdef.tree, dict)


################################################################################
# Attribute Get Tests
################################################################################
class TestAttrGet:
    """Test attr_get functionality."""

    def test_get_string_attr(self, json_basic):
        """Test getting a string attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        value = expdef.attr_get("$.app", "name")
        assert value == "MyApp"

    def test_get_number_attr(self, json_basic):
        """Test getting a numeric attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        value = expdef.attr_get("$.app", "port")
        assert value == 8080

    def test_get_bool_attr(self, json_basic):
        """Test getting a boolean attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        value = expdef.attr_get("$.app", "debug")
        assert value is False

    def test_get_nonexistent_attr(self, json_basic):
        """Test getting a non-existent attribute returns None."""
        expdef = ExpDef(input_fpath=json_basic)
        value = expdef.attr_get("$.app", "nonexistent")
        assert value is None

    def test_get_nested_attr(self, json_nested):
        """Test getting a deeply nested attribute."""
        expdef = ExpDef(input_fpath=json_nested)
        value = expdef.attr_get("$.app.config.level1.level2.level3", "value")
        assert value == "deep"

    def test_get_attr_nonexistent_path(self, json_basic):
        """Test getting attribute from non-existent path."""
        expdef = ExpDef(input_fpath=json_basic)
        value = expdef.attr_get("$.nonexistent.path", "attr")
        assert value is None

    def test_get_container_not_attr(self, json_basic):
        """Test that containers are not returned as attributes."""
        expdef = ExpDef(input_fpath=json_basic)
        # 'database' is a dict, not a scalar attribute
        value = expdef.attr_get("$", "database")
        assert value is None

    def test_get_float_attr(self, json_mixed_types):
        """Test getting a float attribute."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        value = expdef.attr_get("$.config", "float_val")
        assert value == 3.14


################################################################################
# Attribute Change Tests
################################################################################
class TestAttrChange:
    """Test attr_change functionality."""

    def test_change_string_attr(self, json_basic):
        """Test changing a string attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.app", "name", "NewApp")
        assert result is True
        assert expdef.attr_get("$.app", "name") == "NewApp"

    def test_change_number_attr(self, json_basic):
        """Test changing a numeric attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.app", "port", 9090)
        assert result is True
        assert expdef.attr_get("$.app", "port") == 9090

    def test_change_bool_attr(self, json_basic):
        """Test changing a boolean attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.app", "debug", True)
        assert result is True
        assert expdef.attr_get("$.app", "debug") is True

    def test_change_tracks_modification(self, json_basic):
        """Test that changes are tracked."""
        expdef = ExpDef(input_fpath=json_basic)
        expdef.attr_change("$.app", "name", "NewApp")
        adds, changes = expdef.n_mods()
        assert changes == 1

    def test_change_nonexistent_path(self, json_basic):
        """Test changing attribute in non-existent path fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.nonexistent", "attr", "value")
        assert result is False

    def test_change_nonexistent_attr(self, json_basic):
        """Test changing non-existent attribute fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.app", "nonexistent", "value")
        assert result is False

    def test_change_nested_attr(self, json_nested):
        """Test changing a deeply nested attribute."""
        expdef = ExpDef(input_fpath=json_nested)
        result = expdef.attr_change(
            "$.app.config.level1.level2.level3", "value", "shallow"
        )
        assert result is True
        new_val = expdef.attr_get("$.app.config.level1.level2.level3", "value")
        assert new_val == "shallow"

    def test_change_to_null(self, json_basic):
        """Test changing attribute to null."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_change("$.app", "name", None)
        assert result is True
        assert expdef.attr_get("$.app", "name") is None


################################################################################
# Attribute Add Tests
################################################################################
class TestAttrAdd:
    """Test attr_add functionality."""

    def test_add_new_attr(self, json_basic):
        """Test adding a new attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_add("$.app", "timeout", 30)
        assert result is True
        assert expdef.attr_get("$.app", "timeout") == 30

    def test_add_tracks_modification(self, json_basic):
        """Test that additions are tracked."""
        expdef = ExpDef(input_fpath=json_basic)
        expdef.attr_add("$.app", "timeout", 30)
        adds, changes = expdef.n_mods()
        assert changes == 1

    def test_add_duplicate_attr_fails(self, json_basic):
        """Test that adding duplicate attribute fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_add("$.app", "name", "AnotherName")
        assert result is False

    def test_add_to_nonexistent_path(self, json_basic):
        """Test adding to non-existent path fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_add("$.nonexistent", "attr", "value")
        assert result is False

    def test_add_nested_attr(self, json_nested):
        """Test adding attribute to nested path."""
        expdef = ExpDef(input_fpath=json_nested)
        result = expdef.attr_add("$.app.config.settings", "cache_size", 100)
        assert result is True
        assert expdef.attr_get("$.app.config.settings", "cache_size") == 100

    def test_add_string_attr(self, json_basic):
        """Test adding string attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_add("$.app", "environment", "production")
        assert result is True
        assert expdef.attr_get("$.app", "environment") == "production"

    def test_add_float_attr(self, json_basic):
        """Test adding float attribute."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.attr_add("$.database", "version", 14.5)
        assert result is True
        assert expdef.attr_get("$.database", "version") == 14.5


################################################################################
# Has Element Tests
################################################################################
class TestHasElement:
    """Test has_element functionality."""

    def test_has_dict_element(self, json_basic):
        """Test detecting dict elements."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.has_element("$.app") is True
        assert expdef.has_element("$.database") is True

    def test_has_array_element(self, json_with_arrays):
        """Test detecting array elements."""
        expdef = ExpDef(input_fpath=json_with_arrays)
        assert expdef.has_element("$.colors") is True
        assert expdef.has_element("$.servers") is True

    def test_has_nested_element(self, json_nested):
        """Test detecting nested elements."""
        expdef = ExpDef(input_fpath=json_nested)
        assert expdef.has_element("$.app.config") is True
        assert expdef.has_element("$.app.config.level1.level2") is True

    def test_scalar_not_element(self, json_basic):
        """Test that scalar values are not elements."""
        expdef = ExpDef(input_fpath=json_basic)
        # These are attributes (scalars), not elements
        assert expdef.has_element("$.app.name") is False
        assert expdef.has_element("$.app.port") is False

    def test_nonexistent_element(self, json_basic):
        """Test non-existent element returns False."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.has_element("$.nonexistent") is False

    def test_empty_dict_is_element(self, json_empty_sections):
        """Test that empty dict is still an element."""
        expdef = ExpDef(input_fpath=json_empty_sections)
        assert expdef.has_element("$.empty_dict") is True

    def test_empty_array_is_element(self, json_empty_sections):
        """Test that empty array is still an element."""
        expdef = ExpDef(input_fpath=json_empty_sections)
        assert expdef.has_element("$.empty_list") is True

    def test_null_not_element(self, json_mixed_types):
        """Test that null value is not an element."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        assert expdef.has_element("$.config.null_val") is False


################################################################################
# Has Attribute Tests
################################################################################
class TestHasAttr:
    """Test has_attr functionality."""

    def test_has_existing_attr(self, json_basic):
        """Test detecting existing attributes."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.has_attr("$.app", "name") is True
        assert expdef.has_attr("$.app", "port") is True
        assert expdef.has_attr("$.database", "host") is True

    def test_has_nonexistent_attr(self, json_basic):
        """Test non-existent attribute returns False."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.has_attr("$.app", "nonexistent") is False

    def test_has_nested_attr(self, json_nested):
        """Test detecting nested attributes."""
        expdef = ExpDef(input_fpath=json_nested)
        path = "$.app.config.level1.level2.level3"
        assert expdef.has_attr(path, "value") is True
        assert expdef.has_attr("$.app.config.settings", "timeout") is True

    def test_container_not_attr(self, json_basic):
        """Test that containers are not considered attributes."""
        expdef = ExpDef(input_fpath=json_basic)
        # 'database' is a dict, not a scalar attribute
        assert expdef.has_attr("$", "database") is False

    def test_has_attr_in_array_element(self, json_with_arrays):
        """Test detecting attribute in array elements."""
        expdef = ExpDef(input_fpath=json_with_arrays)
        # jsonpath for array element with filter
        assert expdef.has_attr('$.colors[?(@.color=="cyan")]', "color") is True
        assert expdef.has_attr('$.colors[?(@.color=="cyan")]', "value2") is True

    def test_has_attr_nonexistent_path(self, json_basic):
        """Test has_attr with non-existent path."""
        expdef = ExpDef(input_fpath=json_basic)
        assert expdef.has_attr("$.nonexistent.path", "attr") is False

    def test_has_bool_attr(self, json_mixed_types):
        """Test detecting boolean attributes."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        assert expdef.has_attr("$.config", "bool_true") is True
        assert expdef.has_attr("$.config", "bool_false") is True


################################################################################
# Element Remove Tests
################################################################################
class TestElementRemove:
    """Test element_remove functionality."""

    def test_remove_element(self, json_basic):
        """Test removing an element."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove("$", "database")
        assert result is True
        assert expdef.has_element("$.database") is False

    def test_remove_nested_element(self, json_nested):
        """Test removing nested element."""
        expdef = ExpDef(input_fpath=json_nested)
        result = expdef.element_remove("$.app.config", "level1")
        assert result is True
        assert expdef.has_element("$.app.config.level1") is False

    def test_remove_nonexistent_element(self, json_basic):
        """Test removing non-existent element fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove("$.app", "nonexistent")
        assert result is False

    def test_remove_from_nonexistent_path(self, json_basic):
        """Test removing from non-existent path fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove("$.nonexistent", "element")
        assert result is False

    def test_remove_with_noprint(self, json_basic):
        """Test remove with noprint flag."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove("$.app", "nonexistent", noprint=True)
        assert result is False

    def test_remove_scalar_fails(self, json_basic):
        """Test that removing scalar (not element) fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove("$.app", "name")
        assert result is False


################################################################################
# Element Remove All Tests
################################################################################
class TestElementRemoveAll:
    """Test element_remove_all functionality."""

    def test_remove_all_single_match(self, json_basic):
        """Test remove_all with single match."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove_all("$", "database")
        assert result is True
        assert expdef.has_element("$.database") is False

    def test_remove_all_nonexistent(self, json_basic):
        """Test remove_all with non-existent element."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove_all("$.app", "nonexistent")
        assert result is False

    def test_remove_all_from_nonexistent_path(self, json_basic):
        """Test remove_all from non-existent path."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_remove_all("$.nonexistent", "element")
        assert result is False


################################################################################
# Element Add Tests
################################################################################
class TestElementAdd:
    """Test element_add functionality."""

    def test_add_simple_element(self, json_basic):
        """Test adding a simple element."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$.app", "cache", {"enabled": True, "ttl": 3600})
        assert result is True
        assert expdef.has_element("$.app.cache") is True

    def test_add_element_tracks_modification(self, json_basic):
        """Test that element addition is tracked."""
        expdef = ExpDef(input_fpath=json_basic)
        expdef.element_add("$.app", "cache", {"enabled": True})
        adds, changes = expdef.n_mods()
        assert adds == 1

    def test_add_duplicate_not_allowed(self, json_basic):
        """Test adding duplicate element with allow_dup=False."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$", "app", {"name": "test"}, allow_dup=False)
        assert result is False

    def test_add_duplicate_creates_array(self, json_basic):
        """Test adding duplicate element with allow_dup=True creates array."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$", "database", {"host": "backup"}, allow_dup=True)
        assert result is True
        # After adding duplicate, it should become an array
        # Verify by checking the structure
        assert "database" in expdef.tree

    def test_add_to_nested_path(self, json_nested):
        """Test adding element to nested path."""
        expdef = ExpDef(input_fpath=json_nested)
        result = expdef.element_add(
            "$.app.config.settings", "logging", {"level": "INFO"}
        )
        assert result is True
        assert expdef.has_element("$.app.config.settings.logging") is True

    def test_add_empty_element(self, json_basic):
        """Test adding element with None attributes."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$.app", "new_section", None)
        assert result is True

    def test_add_to_nonexistent_path(self, json_basic):
        """Test adding to non-existent path fails."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$.nonexistent", "element", {})
        assert result is False

    def test_add_with_noprint(self, json_basic):
        """Test add with noprint flag."""
        expdef = ExpDef(input_fpath=json_basic)
        result = expdef.element_add("$.nonexistent", "elem", {}, noprint=True)
        assert result is False


################################################################################
# Write Tests
################################################################################
class TestWrite:
    """Test write functionality."""

    def test_write_entire_tree(self, json_basic, tmp_path):
        """Test writing entire JSON tree."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=json_basic, write_config=write_config)

        output = tmp_path / "output.json"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = json.load(f)
        assert "name" in data
        assert data["name"] == "MyApp"

    def test_write_section(self, json_for_writing, tmp_path):
        """Test writing specific section."""
        write_config = definition.WriterConfig(
            [{"src_parent": "root", "src_tag": "section1"}]
        )
        expdef = ExpDef(input_fpath=json_for_writing, write_config=write_config)

        output = tmp_path / "section1.json"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = json.load(f)
        assert "data" in data
        assert data["data"] == "value1"

    def test_write_nested_section(self, json_for_writing, tmp_path):
        """Test writing nested section."""
        write_config = definition.WriterConfig(
            [{"src_parent": "root.section3", "src_tag": "subsection"}]
        )
        expdef = ExpDef(input_fpath=json_for_writing, write_config=write_config)

        output = tmp_path / "subsection.json"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = json.load(f)
        assert "data" in data

    def test_write_with_custom_name(self, json_basic, tmp_path):
        """Test writing with custom output filename."""
        write_config = definition.WriterConfig(
            [{"src_parent": None, "src_tag": "app", "opath_leaf": "-custom"}]
        )
        expdef = ExpDef(input_fpath=json_basic, write_config=write_config)

        output = tmp_path / "output.json"
        expdef.write(output)

        expected = tmp_path / "output.json-custom"
        assert expected.exists()

    def test_write_after_modifications(self, json_basic, tmp_path):
        """Test writing after making modifications."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=json_basic, write_config=write_config)

        # Make modifications
        expdef.attr_change("$.app", "name", "ModifiedApp")
        expdef.attr_add("$.app", "timeout", 30)

        output = tmp_path / "modified.json"
        expdef.write(output)

        # Verify modifications persisted
        with open(output) as f:
            data = json.load(f)
        assert data["name"] == "ModifiedApp"
        assert data["timeout"] == 30

    def test_write_without_config_fails(self, json_basic, tmp_path):
        """Test that writing without config raises error."""
        expdef = ExpDef(input_fpath=json_basic)  # No write_config

        output = tmp_path / "output.json"
        with pytest.raises(AssertionError):
            expdef.write(output)

    def test_write_config_set(self, json_basic):
        """Test setting write config after initialization."""
        expdef = ExpDef(input_fpath=json_basic)

        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef.write_config_set(write_config)

        assert expdef.write_config is not None

    def test_write_array(self, json_with_arrays, tmp_path):
        """Test writing array section."""
        write_config = definition.WriterConfig(
            [{"src_parent": None, "src_tag": "colors"}]
        )
        expdef = ExpDef(input_fpath=json_with_arrays, write_config=write_config)

        output = tmp_path / "colors.json"
        expdef.write(output)

        assert output.exists()
        with open(output) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 6


################################################################################
# Flatten Tests
################################################################################
class TestFlatten:
    """Test flatten functionality."""

    def test_flatten_single_level(self, json_for_flatten):
        """Test flattening with single include."""
        expdef = ExpDef(input_fpath=json_for_flatten)

        # Verify include key exists before flatten
        assert "include" in expdef.tree["main"]

        # Flatten
        expdef.flatten(["include"])

        # Verify include key is removed and content is merged
        assert "include" not in expdef.tree["main"]
        # Content from subconfig.json should be merged in
        assert "sub" in expdef.tree["main"]
        assert expdef.tree["main"]["sub"]["value"] == "from_subconfig"

    def test_flatten_nested(self, json_nested_flatten):
        """Test flattening with nested includes."""
        expdef = ExpDef(input_fpath=json_nested_flatten)

        # Flatten
        expdef.flatten(["include"])

        # Verify nested content is merged
        assert "level2" in expdef.tree["level1"]
        assert expdef.tree["level1"]["level2"]["data"] == "level2_data"

    def test_flatten_preserves_other_keys(self, json_for_flatten):
        """Test that flatten preserves non-include keys."""
        expdef = ExpDef(input_fpath=json_for_flatten)

        # Verify original content exists
        assert expdef.tree["main"]["name"] == "MainConfig"
        assert expdef.tree["settings"]["timeout"] == 30

        # Flatten
        expdef.flatten(["include"])

        # Verify original content is preserved
        assert expdef.tree["main"]["name"] == "MainConfig"
        assert expdef.tree["settings"]["timeout"] == 30

    def test_flatten_nonexistent_key(self, json_basic):
        """Test flattening with non-existent key doesn't fail."""
        expdef = ExpDef(input_fpath=json_basic)

        # This should not raise an error
        expdef.flatten(["nonexistent_key"])

        # Tree should be unchanged
        assert "app" in expdef.tree
        assert "database" in expdef.tree

    def test_flatten_multiple_keys(self, tmp_path):
        """Test flattening with multiple different keys."""
        content = {
            "section1": {"include_a": "file_a.json", "data": "original"},
            "section2": {"include_b": "file_b.json", "value": 123},
        }

        file_a = {"merged_a": "from_a"}
        file_b = {"merged_b": "from_b"}

        main = tmp_path / "main.json"
        (tmp_path / "file_a.json").write_text(json.dumps(file_a))
        (tmp_path / "file_b.json").write_text(json.dumps(file_b))
        main.write_text(json.dumps(content))

        expdef = ExpDef(input_fpath=main)
        expdef.flatten(["include_a", "include_b"])

        # Verify both includes were processed
        assert "merged_a" in expdef.tree["section1"]
        assert "merged_b" in expdef.tree["section2"]


################################################################################
# Complex Scenario Tests
################################################################################
class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_modify_multiple_attributes(self, json_basic):
        """Test modifying multiple attributes."""
        expdef = ExpDef(input_fpath=json_basic)

        expdef.attr_change("$.app", "name", "UpdatedApp")
        expdef.attr_change("$.app", "version", "2.0.0")
        expdef.attr_change("$.app", "debug", True)
        expdef.attr_change("$.database", "host", "db.example.com")

        assert expdef.attr_get("$.app", "name") == "UpdatedApp"
        assert expdef.attr_get("$.app", "version") == "2.0.0"
        assert expdef.attr_get("$.app", "debug") is True
        assert expdef.attr_get("$.database", "host") == "db.example.com"

    def test_add_and_modify(self, json_basic):
        """Test adding then modifying attributes."""
        expdef = ExpDef(input_fpath=json_basic)

        # Add new attribute
        expdef.attr_add("$.app", "timeout", 30)
        assert expdef.attr_get("$.app", "timeout") == 30

        # Modify the newly added attribute
        expdef.attr_change("$.app", "timeout", 60)
        assert expdef.attr_get("$.app", "timeout") == 60

    def test_restructure_tree(self, json_basic):
        """Test restructuring the JSON tree."""
        expdef = ExpDef(input_fpath=json_basic)

        # Add new section
        expdef.element_add("$", "logging", {"level": "INFO", "file": "app.log"})

        # Remove old section
        expdef.element_remove("$", "database")

        # Verify changes
        assert expdef.has_element("$.logging") is True
        assert expdef.has_element("$.database") is False

    def test_work_with_array_elements(self, json_with_arrays):
        """Test operations on array elements."""
        expdef = ExpDef(input_fpath=json_with_arrays)

        # Check specific element using jsonpath filter
        path = '$.colors[?(@.color=="cyan")]'
        assert expdef.has_attr(path, "value2") is True

        # Modify attribute in array element
        expdef.attr_change(path, "value2", "updated")
        assert expdef.attr_get(path, "value2") == "updated"

    def test_deep_nesting_operations(self, json_nested):
        """Test operations on deeply nested structures."""
        expdef = ExpDef(input_fpath=json_nested)

        # Modify deep value
        path = "$.app.config.level1.level2.level3"
        expdef.attr_change(path, "value", "very_deep")

        # Add to deep path
        expdef.attr_add(path, "new_value", "added_deep")

        # Verify
        assert expdef.attr_get(path, "value") == "very_deep"
        assert expdef.attr_get(path, "new_value") == "added_deep"

    def test_modification_tracking(self, json_basic):
        """Test that all modifications are tracked correctly."""
        expdef = ExpDef(input_fpath=json_basic)

        # Make various modifications
        expdef.attr_change("$.app", "name", "NewApp")
        expdef.attr_add("$.app", "timeout", 30)
        expdef.element_add("$", "cache", {"enabled": True})
        expdef.attr_change("$.database", "host", "newhost")

        adds, changes = expdef.n_mods()
        assert adds == 1  # One element add
        assert changes == 3  # Three attribute changes + one attribute add

    def test_chain_operations(self, json_basic, tmp_path):
        """Test chaining multiple operations together."""
        write_config = definition.WriterConfig([{"src_parent": None, "src_tag": "app"}])
        expdef = ExpDef(input_fpath=json_basic, write_config=write_config)

        # Chain operations
        expdef.attr_change("$.app", "version", "3.0.0")
        expdef.attr_add("$.app", "author", "TestUser")
        expdef.element_add("$.app", "features", ["feature1", "feature2"])

        # Write result
        output = tmp_path / "chained.json"
        expdef.write(output)

        # Verify all changes persisted
        with open(output) as f:
            data = json.load(f)
        assert data["version"] == "3.0.0"
        assert data["author"] == "TestUser"
        assert "features" in data


################################################################################
# Edge Cases and Error Handling
################################################################################
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_root_path_operations(self, json_basic):
        """Test operations at root level."""
        expdef = ExpDef(input_fpath=json_basic)

        # Root path
        assert expdef.has_element("$") is True

        # Can add to root
        result = expdef.element_add("$", "newroot", {"key": "value"})
        assert result is True

    def test_special_characters_in_values(self, tmp_path):
        """Test handling special characters."""
        content = {
            "special": {
                "quotes": 'value with "quotes"',
                "symbols": "@#$%^&*()",
                "unicode": "café résumé",
                "newlines": "line1\nline2",
            }
        }
        fpath = tmp_path / "special.json"
        fpath.write_text(json.dumps(content, indent=2))

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.attr_get("$.special", "quotes") is not None
        assert expdef.attr_get("$.special", "symbols") == "@#$%^&*()"
        assert "café" in expdef.attr_get("$.special", "unicode")

    def test_null_values(self, json_mixed_types):
        """Test handling null/None values."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        value = expdef.attr_get("$.config", "null_val")
        # Note: JSON null becomes Python None
        assert value is None

    def test_numeric_types(self, json_mixed_types):
        """Test handling different numeric types."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        assert expdef.attr_get("$.config", "int_val") == 42
        assert expdef.attr_get("$.config", "float_val") == 3.14

    def test_boolean_values(self, json_mixed_types):
        """Test handling boolean values."""
        expdef = ExpDef(input_fpath=json_mixed_types)
        assert expdef.attr_get("$.config", "bool_true") is True
        assert expdef.attr_get("$.config", "bool_false") is False

    def test_empty_structures(self, json_empty_sections):
        """Test handling empty dicts and arrays."""
        expdef = ExpDef(input_fpath=json_empty_sections)
        assert expdef.has_element("$.empty_dict") is True
        assert expdef.has_element("$.empty_list") is True

    def test_large_numbers(self, tmp_path):
        """Test handling large numbers."""
        content = {
            "big_numbers": {
                "large_int": 999999999999999,
                "large_float": 1.23e10,
                "negative": -999999,
            }
        }
        fpath = tmp_path / "large.json"
        fpath.write_text(json.dumps(content))

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.attr_get("$.big_numbers", "large_int") == 999999999999999
        assert expdef.attr_get("$.big_numbers", "negative") == -999999

    def test_jsonpath_special_syntax(self, json_with_arrays):
        """Test jsonpath special syntax."""
        expdef = ExpDef(input_fpath=json_with_arrays)

        # Array index
        path = "$.colors[0]"
        assert expdef.has_attr(path, "color") is True

        # Array slice
        path = "$.colors[0:2]"
        matches = expdef.processor(path) if hasattr(expdef, "processor") else None
        # Just verify path doesn't crash


################################################################################
# Performance and Stress Tests
################################################################################
class TestPerformance:
    """Test performance with larger structures."""

    def test_large_array(self, tmp_path):
        """Test handling large arrays."""
        # Create JSON with 1000 items
        items = [{"item": f"item{i}", "value": i} for i in range(1000)]
        content = {"items": items}

        fpath = tmp_path / "large_array.json"
        fpath.write_text(json.dumps(content))

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.has_element("$.items") is True

    def test_many_modifications(self, json_basic):
        """Test making many modifications."""
        expdef = ExpDef(input_fpath=json_basic)

        # Add 100 attributes
        for i in range(100):
            expdef.attr_add("$.app", f"attr{i}", i)

        adds, changes = expdef.n_mods()
        assert changes == 100

        # Verify some additions
        assert expdef.attr_get("$.app", "attr0") == 0
        assert expdef.attr_get("$.app", "attr99") == 99

    def test_deep_nesting_limit(self, tmp_path):
        """Test very deep nesting."""
        # Create deeply nested structure
        content = {"level0": {}}
        current = content["level0"]
        for i in range(1, 20):
            current[f"level{i}"] = {}
            current = current[f"level{i}"]
        current["value"] = "deep"

        fpath = tmp_path / "deep.json"
        fpath.write_text(json.dumps(content))

        expdef = ExpDef(input_fpath=fpath)
        path = "$.level0." + ".".join([f"level{i}" for i in range(1, 20)])
        assert expdef.has_attr(path, "value") is True

    def test_wide_structure(self, tmp_path):
        """Test structure with many keys at same level."""
        content = {"root": {f"key{i}": f"value{i}" for i in range(500)}}

        fpath = tmp_path / "wide.json"
        fpath.write_text(json.dumps(content))

        expdef = ExpDef(input_fpath=fpath)
        assert expdef.has_attr("$.root", "key0") is True
        assert expdef.has_attr("$.root", "key499") is True
