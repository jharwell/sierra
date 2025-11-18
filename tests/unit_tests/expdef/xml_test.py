# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages

# 3rd party packages
# Copyright 2024 Test Suite, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Comprehensive test suite for XML experiment definition plugin."""

# Core packages
import pathlib
import xml.etree.ElementTree as ET
import pickle

# 3rd party packages
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Project packages
from sierra.core.experiment import definition
from sierra.plugins.expdef.xml import plugin as xml


################################################################################
# Fixtures
################################################################################
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def simple_xml_file(temp_dir):
    """Create a simple XML file for testing."""
    xml_content = """<?xml version="1.0"?>
<root>
    <config>
        <parameter name="value1" type="int">10</parameter>
        <parameter name="value2" type="string">test</parameter>
    </config>
    <experiment id="exp1">
        <setting enabled="true">active</setting>
    </experiment>
</root>"""

    fpath = temp_dir / "simple.xml"
    fpath.write_text(xml_content)
    return fpath


@pytest.fixture
def complex_xml_file(temp_dir):
    """Create a complex XML file with nested structures."""
    xml_content = """<?xml version="1.0"?>
<simulation>
    <arena>
        <size x="10" y="10" z="5"/>
        <objects>
            <box id="box1" x="1" y="1"/>
            <box id="box2" x="2" y="2"/>
            <sphere id="sphere1" radius="0.5"/>
        </objects>
    </arena>
    <controllers>
        <controller type="diffusion" id="ctrl1">
            <parameters speed="1.0" rotation="0.5"/>
        </controller>
    </controllers>
    <physics>
        <gravity value="9.81"/>
    </physics>
</simulation>"""

    fpath = temp_dir / "complex.xml"
    fpath.write_text(xml_content)
    return fpath


@pytest.fixture
def nested_xml_file(temp_dir):
    """Create an XML file with deep nesting."""
    xml_content = """<?xml version="1.0"?>
<level1>
    <level2>
        <level3>
            <level4>
                <level5 attr="deep">value</level5>
            </level4>
        </level3>
    </level2>
    <parallel_branch>
        <data>test</data>
    </parallel_branch>
</level1>"""

    fpath = temp_dir / "nested.xml"
    fpath.write_text(xml_content)
    return fpath


@pytest.fixture
def empty_elements_xml_file(temp_dir):
    """Create an XML file with empty elements."""
    xml_content = """<?xml version="1.0"?>
<root>
    <empty_parent>
    </empty_parent>
    <parent_with_children>
        <child1/>
        <child2/>
    </parent_with_children>
</root>"""

    fpath = temp_dir / "empty_elements.xml"
    fpath.write_text(xml_content)
    return fpath


@pytest.fixture
def duplicate_tags_xml_file(temp_dir):
    """Create an XML file with duplicate tag names."""
    xml_content = """<?xml version="1.0"?>
<root>
    <collection>
       <item id="1" name="first"/>
       <item id="2" name="second"/>
       <item id="3" name="third"/>
       <group>
           <item id="4" name="nested"/>
       </group>
   </collection>
</root>"""

    fpath = temp_dir / "duplicates.xml"
    fpath.write_text(xml_content)
    return fpath


################################################################################
# ExpDef Tests - Initialization
################################################################################
class TestExpDefInitialization:
    """Test suite for ExpDef initialization."""

    write_config = definition.WriterConfig(
        [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]
    )

    def test_init_simple_file(self, simple_xml_file):
        """Test initialization with a simple XML file."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.input_fpath == simple_xml_file
        assert expdef.tree is not None
        assert expdef.root is not None
        assert expdef.write_config is None

    def test_init_with_write_config(
        self,
        simple_xml_file,
    ):
        """Test initialization with write configuration."""
        expdef = xml.ExpDef(simple_xml_file, self.write_config)
        assert expdef.write_config == self.write_config

    def test_init_complex_file(self, complex_xml_file):
        """Test initialization with complex XML structure."""
        expdef = xml.ExpDef(complex_xml_file)
        assert expdef.root.tag == "simulation"

    def test_init_nonexistent_file(self, temp_dir):
        """Test initialization with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            xml.ExpDef(temp_dir / "nonexistent.xml")

    def test_init_element_adds_empty(self, simple_xml_file):
        """Test that element_adds list is initialized empty."""
        expdef = xml.ExpDef(simple_xml_file)
        assert len(expdef.element_adds) == 0

    def test_init_attr_chgs_empty(self, simple_xml_file):
        """Test that attr_chgs set is initialized empty."""
        expdef = xml.ExpDef(simple_xml_file)
        assert len(expdef.attr_chgs) == 0


################################################################################
# ExpDef Tests - Attribute Operations
################################################################################
class TestExpDefAttributeOperations:
    """Test suite for attribute get, change, and add operations."""

    def test_attr_get_existing(self, simple_xml_file):
        """Test getting an existing attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        value = expdef.attr_get("config/parameter", "name")
        assert value == "value1"

    def test_attr_get_nonexistent_path(self, simple_xml_file):
        """Test getting attribute from non-existent path."""
        expdef = xml.ExpDef(simple_xml_file)
        value = expdef.attr_get("nonexistent/path", "attr")
        assert value is None

    def test_attr_get_nonexistent_attr(self, simple_xml_file):
        """Test getting non-existent attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        value = expdef.attr_get("config/parameter", "nonexistent")
        assert value is None

    def test_attr_change_existing(self, simple_xml_file):
        """Test changing an existing attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("config/parameter", "name", "new_value")
        assert result is True
        assert expdef.attr_get("config/parameter", "name") == "new_value"

    def test_attr_change_int_value(self, simple_xml_file):
        """Test changing attribute to integer value."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("config/parameter", "type", 42)
        assert result is True
        assert expdef.attr_get("config/parameter", "type") == 42

    def test_attr_change_float_value(self, simple_xml_file):
        """Test changing attribute to float value."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("config/parameter", "type", 3.14)
        assert result is True

    def test_attr_change_nonexistent_path(self, simple_xml_file):
        """Test changing attribute on non-existent path."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("nonexistent/path", "attr", "value")
        assert result is False

    def test_attr_change_nonexistent_attr(self, simple_xml_file):
        """Test changing non-existent attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("config/parameter", "nonexistent", "value")
        assert result is False

    def test_attr_change_with_noprint(self, simple_xml_file):
        """Test attribute change with noprint flag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change("nonexistent/path", "attr", "value", noprint=True)
        assert result is False

    def test_attr_change_updates_attr_chgs(self, simple_xml_file):
        """Test that attr_change updates the attr_chgs set."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.attr_change("config/parameter", "name", "new_value")
        assert len(expdef.attr_chgs) == 1

    def test_attr_add_new(self, simple_xml_file):
        """Test adding a new attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_add("config/parameter", "new_attr", "new_value")
        assert result is True
        assert expdef.attr_get("config/parameter", "new_attr") == "new_value"

    def test_attr_add_existing(self, simple_xml_file):
        """Test adding an attribute that already exists."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_add("config/parameter", "name", "value")
        assert result is False

    def test_attr_add_nonexistent_path(self, simple_xml_file):
        """Test adding attribute to non-existent path."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_add("nonexistent/path", "attr", "value")
        assert result is False

    def test_attr_add_with_noprint(self, simple_xml_file):
        """Test attribute add with noprint flag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_add("config/parameter", "name", "value", noprint=True)
        assert result is False

    def test_attr_add_updates_attr_chgs(self, simple_xml_file):
        """Test that attr_add updates the attr_chgs set."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.attr_add("config/parameter", "new_attr", "new_value")
        assert len(expdef.attr_chgs) == 1


################################################################################
# ExpDef Tests - Element Queries
################################################################################
class TestExpDefElementQueries:
    """Test suite for element existence queries."""

    def test_has_element_existing(self, simple_xml_file):
        """Test checking for existing element."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.has_element("config") is True

    def test_has_element_nonexistent(self, simple_xml_file):
        """Test checking for non-existent element."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.has_element("nonexistent") is False

    def test_has_element_nested(self, complex_xml_file):
        """Test checking for nested element."""
        expdef = xml.ExpDef(complex_xml_file)
        assert expdef.has_element("arena/objects/box") is True

    def test_has_attr_existing(self, simple_xml_file):
        """Test checking for existing attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.has_attr("config/parameter", "name") is True

    def test_has_attr_nonexistent_path(self, simple_xml_file):
        """Test checking for attribute on non-existent path."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.has_attr("nonexistent/path", "attr") is False

    def test_has_attr_nonexistent_attr(self, simple_xml_file):
        """Test checking for non-existent attribute."""
        expdef = xml.ExpDef(simple_xml_file)
        assert expdef.has_attr("config/parameter", "nonexistent") is False


################################################################################
# ExpDef Tests - Element Modification
################################################################################
class TestExpDefElementModification:
    """Test suite for element change operations."""

    def test_element_change_existing(self, simple_xml_file):
        """Test changing an existing element tag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_change("config", "parameter", "new_parameter")
        assert result is True

    def test_element_change_nonexistent_path(self, simple_xml_file):
        """Test changing element on non-existent path."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_change("nonexistent/path", "tag", "new_tag")
        assert result is False

    def test_element_change_nonexistent_tag(self, simple_xml_file):
        """Test changing non-existent element tag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_change("config", "nonexistent", "new_tag")
        assert result is False


################################################################################
# ExpDef Tests - Element Removal
################################################################################
class TestExpDefElementRemoval:
    """Test suite for element removal operations."""

    def test_element_remove_existing(self, simple_xml_file):
        """Test removing an existing element."""
        expdef = xml.ExpDef(simple_xml_file)

        # Verify there are initially 2 parameters
        params_before = expdef.root.findall("config/parameter")
        assert len(params_before) == 2

        result = expdef.element_remove("config", "parameter")
        assert result is True

        # Verify only one parameter remains (first one removed)
        params_after = expdef.root.findall("config/parameter")
        assert len(params_after) == 1

    def test_element_remove_nonexistent_parent(self, simple_xml_file):
        """Test removing element from non-existent parent."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_remove(".//nonexistent", "child")
        assert result is False

    def test_element_remove_nonexistent_child(self, simple_xml_file):
        """Test removing non-existent child element."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_remove(".//config", "nonexistent")
        assert result is False

    def test_element_remove_with_noprint(self, simple_xml_file):
        """Test element removal with noprint flag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_remove(".//nonexistent", "child", noprint=True)
        assert result is False

    def test_element_remove_all_duplicates(self, duplicate_tags_xml_file):
        """Test removing all elements with same tag."""
        expdef = xml.ExpDef(duplicate_tags_xml_file)
        result = expdef.element_remove_all(".//collection", "item")
        assert result is True
        # Verify all items at that level are removed
        items = expdef.root.findall(".//collection/item")
        assert len(items) == 0

    def test_element_remove_all_nonexistent_parent(self, simple_xml_file):
        """Test removing all from non-existent parent."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_remove_all(".//nonexistent", "child")
        assert result is False

    def test_element_remove_all_no_matches(self, simple_xml_file):
        """Test removing all when no matches exist."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_remove_all(".//config", "nonexistent")
        assert result is False

    def test_element_remove_all_with_noprint(self, duplicate_tags_xml_file):
        """Test removing all elements with noprint flag."""
        expdef = xml.ExpDef(duplicate_tags_xml_file)
        result = expdef.element_remove_all(".//nonexistent", "child", noprint=True)
        assert result is False


################################################################################
# ExpDef Tests - Element Addition
################################################################################
class TestExpDefElementAddition:
    """Test suite for element addition operations."""

    def test_element_add_simple(self, simple_xml_file):
        """Test adding a simple element."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_add(".//config", "new_element")
        assert result is True
        assert expdef.has_element(".//config/new_element") is True

    def test_element_add_with_attributes(self, simple_xml_file):
        """Test adding element with attributes."""
        expdef = xml.ExpDef(simple_xml_file)
        attrs = {"attr1": "value1", "attr2": "value2"}
        result = expdef.element_add(".//config", "new_element", attr=attrs)
        assert result is True
        assert expdef.has_attr(".//config/new_element", "attr1") is True

    def test_element_add_nonexistent_parent(self, simple_xml_file):
        """Test adding element to non-existent parent."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_add(".//nonexistent", "child")
        assert result is False

    def test_element_add_duplicate_allowed(self, simple_xml_file):
        """Test adding duplicate elements when allowed."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.element_add(".//config", "duplicate", allow_dup=True)
        result = expdef.element_add(".//config", "duplicate", allow_dup=True)
        assert result is True

    def test_element_add_duplicate_not_allowed(self, simple_xml_file):
        """Test adding duplicate elements when not allowed."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.element_add(".//config", "unique", allow_dup=False)
        result = expdef.element_add(".//config", "unique", allow_dup=False)
        assert result is False

    def test_element_add_with_noprint(self, simple_xml_file):
        """Test element addition with noprint flag."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_add(".//nonexistent", "child", noprint=True)
        assert result is False

    def test_element_add_updates_element_adds(self, simple_xml_file):
        """Test that element_add updates the element_adds list."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.element_add(".//config", "new_element")
        assert len(expdef.element_adds) == 1

    def test_element_add_multiple_duplicates(self, simple_xml_file):
        """Test adding multiple duplicate elements."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.element_add(".//config", "item", allow_dup=True)
        expdef.element_add(".//config", "item", allow_dup=True)
        expdef.element_add(".//config", "item", allow_dup=True)
        items = expdef.root.findall(".//config/item")
        assert len(items) == 3


################################################################################
# ExpDef Tests - Utility Methods
################################################################################
class TestExpDefUtilityMethods:
    """Test suite for utility methods."""

    write_config = definition.WriterConfig(
        [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]
    )

    def test_n_mods_initial(self, simple_xml_file):
        """Test n_mods returns correct counts initially."""
        expdef = xml.ExpDef(simple_xml_file)
        adds, changes = expdef.n_mods()
        assert adds == 0
        assert changes == 0

    def test_n_mods_after_modifications(self, simple_xml_file):
        """Test n_mods returns correct counts after modifications."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.element_add(".//config", "new_element")
        expdef.attr_change(".//config/parameter", "name", "new_value")
        adds, changes = expdef.n_mods()
        assert adds == 1
        assert changes == 1

    def test_write_config_set(self, simple_xml_file):
        """Test setting write configuration."""
        expdef = xml.ExpDef(simple_xml_file)
        expdef.write_config_set(self.write_config)
        assert expdef.write_config == self.write_config

    def test_flatten_not_implemented(self, simple_xml_file):
        """Test that flatten raises NotImplementedError."""
        expdef = xml.ExpDef(simple_xml_file)
        with pytest.raises(NotImplementedError):
            expdef.flatten(["key1", "key2"])


################################################################################
# Writer Tests
################################################################################
class TestWriter:
    """Test suite for Writer class."""

    def test_writer_init(self, simple_xml_file):
        """Test Writer initialization."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)
        assert writer.tree == tree
        assert writer.root == tree.getroot()

    def test_writer_call_basic(self, simple_xml_file, temp_dir):
        """Test basic writer call."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        write_config = definition.WriterConfig(
            [
                {
                    "src_parent": None,
                    "src_tag": ".",
                    "opath_leaf": None,
                    "rename_to": None,
                    "new_children_parent": None,
                    "new_children": None,
                    "child_grafts_parent": None,
                    "child_grafts": None,
                }
            ]
        )

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)
        assert output_path.exists()

    def test_writer_with_rename(self, simple_xml_file, temp_dir):
        """Test writer with root element rename."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        write_config = MagicMock()
        write_config.values = [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": "renamed_root",
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)

        # Verify rename occurred
        output_tree = ET.parse(output_path)
        assert output_tree.getroot().tag == "renamed_root"

    def test_writer_with_custom_opath(self, simple_xml_file, temp_dir):
        """Test writer with custom output path."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        write_config = MagicMock()
        write_config.values = [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": "_custom",
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)
        custom_path = temp_dir / "output.xml_custom"
        assert custom_path.exists()

    def test_writer_subtree(self, complex_xml_file, temp_dir):
        """Test writer with subtree extraction."""
        tree = ET.parse(complex_xml_file)
        writer = xml.Writer(tree)

        write_config = MagicMock()
        write_config.values = [
            {
                "src_parent": ".",
                "src_tag": "arena",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]

        output_path = temp_dir / "arena.xml"
        writer(write_config, output_path)
        assert output_path.exists()

        # Verify only arena subtree was written
        output_tree = ET.parse(output_path)
        assert output_tree.getroot().tag == "arena"

    def test_writer_nonexistent_subtree(self, simple_xml_file, temp_dir):
        """Test writer with non-existent subtree path."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        write_config = MagicMock()
        write_config.values = [
            {
                "src_parent": "nonexistent",
                "src_tag": "child",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)
        # File should not be created for non-existent subtree
        assert not output_path.exists()


################################################################################
# Writer Tests - New Children
################################################################################
class TestWriterNewChildren:
    """Test suite for Writer's new children functionality."""

    def test_add_new_children(self, simple_xml_file, temp_dir):
        """Test adding new children to an element."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        write_config = definition.WriterConfig(
            [
                {
                    "src_parent": None,
                    "src_tag": "config",
                    "opath_leaf": None,
                    "rename_to": None,
                    "new_children_parent": ".",
                    "new_children": [
                        definition.ElementAdd(
                            path=".", tag="new_child", attr={"id": "1"}, allow_dup=False
                        )
                    ],
                    "child_grafts_parent": None,
                    "child_grafts": None,
                }
            ]
        )

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)

        # Verify new child was added
        output_tree = ET.parse(output_path)
        new_child = output_tree.getroot().find(".//new_child")
        assert new_child is not None
        assert new_child.attrib["id"] == "1"

    def test_add_new_children_as_root(self, simple_xml_file, temp_dir):
        """Test adding new children as root element."""
        tree = ET.parse(simple_xml_file)
        writer = xml.Writer(tree)

        new_child_spec = MagicMock()
        new_child_spec.path = "new_root"
        new_child_spec.tag = "child"
        new_child_spec.attr = {}
        new_child_spec.as_root_elt = True

        write_config = definition.WriterConfig(
            [
                {
                    "src_parent": None,
                    "src_tag": ".",
                    "opath_leaf": None,
                    "rename_to": None,
                    "new_children_parent": ".",
                    "new_children": [new_child_spec],
                    "child_grafts_parent": None,
                    "child_grafts": None,
                }
            ]
        )

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)
        assert output_path.exists()


################################################################################
# Writer Tests - Grafts
################################################################################
class TestWriterGrafts:
    """Test suite for Writer's grafting functionality."""

    def test_add_grafts(self, complex_xml_file, temp_dir):
        """Test grafting elements from one location to another."""
        tree = ET.parse(complex_xml_file)
        writer = xml.Writer(tree)

        write_config = MagicMock()
        write_config.values = [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": "arena",
                "child_grafts": ["physics/gravity"],
            }
        ]

        output_path = temp_dir / "output.xml"
        writer(write_config, output_path)

        # Verify graft occurred
        output_tree = ET.parse(output_path)
        grafted = output_tree.getroot().find(".//arena/gravity")
        assert grafted is not None


################################################################################
# ExpDef Tests - Write Operations
################################################################################
class TestExpDefWrite:
    """Test suite for ExpDef write operations."""

    write_config = definition.WriterConfig(
        [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]
    )

    def test_write_without_config(self, simple_xml_file, temp_dir):
        """Test that write without config raises assertion."""
        expdef = xml.ExpDef(simple_xml_file)
        with pytest.raises(AssertionError):
            expdef.write(temp_dir / "output.xml")

    def test_write_with_config(self, simple_xml_file, temp_dir):
        """Test write with valid configuration."""
        expdef = xml.ExpDef(simple_xml_file, write_config=self.write_config)
        output_path = temp_dir / "output.xml"
        expdef.write(output_path)
        assert output_path.exists()

    def test_write_after_modifications(self, simple_xml_file, temp_dir):
        """Test write after making modifications."""
        expdef = xml.ExpDef(simple_xml_file, write_config=self.write_config)
        expdef.attr_change(".//config/parameter", "name", "modified")
        expdef.element_add(".//config", "new_element")

        output_path = temp_dir / "output.xml"
        expdef.write(output_path)

        # Verify modifications persisted
        output_tree = ET.parse(output_path)
        param = output_tree.getroot().find(".//config/parameter")
        assert param.get("name") == "modified"
        assert output_tree.getroot().find("config/new_element") is not None


################################################################################
# Integration Tests
################################################################################
class TestIntegration:
    """Integration tests combining multiple operations."""

    write_config = definition.WriterConfig(
        [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": None,
                "rename_to": None,
                "new_children_parent": None,
                "new_children": None,
                "child_grafts_parent": None,
                "child_grafts": None,
            }
        ]
    )

    def test_full_workflow(self, complex_xml_file, temp_dir):
        """Test complete workflow: load, modify, write."""
        expdef = xml.ExpDef(complex_xml_file, write_config=self.write_config)

        # Make various modifications
        expdef.attr_change(".//arena/size", "x", "20")
        expdef.element_add(".//arena/objects", "cylinder", attr={"id": "cyl1"})
        expdef.element_remove(".//arena/objects", "sphere")
        expdef.attr_add(".//physics/gravity", "units", "m/s^2")

        # Write output
        output_path = temp_dir / "modified.xml"
        expdef.write(output_path)

        # Verify all modifications
        output_tree = ET.parse(output_path)
        root = output_tree.getroot()

        assert root.find(".//arena/size").get("x") == "20"
        assert root.find(".//arena/objects/cylinder") is not None
        assert root.find(".//arena/objects/sphere") is None
        assert root.find(".//physics/gravity").get("units") == "m/s^2"

    def test_multiple_element_adds(self, simple_xml_file):
        """Test adding multiple elements in sequence."""
        expdef = xml.ExpDef(simple_xml_file)

        for i in range(5):
            expdef.element_add(".//config", f"element_{i}", attr={"id": str(i)})

        adds, _ = expdef.n_mods()
        assert adds == 5

        # Verify all elements exist
        for i in range(5):
            assert expdef.has_element(f"config/element_{i}")

    def test_chained_modifications(self, nested_xml_file):
        """Test modifications at different nesting levels."""
        expdef = xml.ExpDef(nested_xml_file)

        expdef.attr_change(".//level2/level3/level4/level5", "attr", "modified")
        expdef.element_add(".//level2", "new_level3")
        expdef.element_remove(".", "parallel_branch")

        _, changes = expdef.n_mods()
        assert changes == 1
        assert not expdef.has_element(".//parallel_branch")
        assert expdef.has_element(".//level2/new_level3")


################################################################################
# Utility Function Tests
################################################################################
class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_root_querypath(self):
        """Test root_querypath returns correct value."""
        assert xml.root_querypath() == "."


################################################################################
# Edge Cases and Error Handling
################################################################################
class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_malformed_xml(self, temp_dir):
        """Test handling of malformed XML."""
        malformed_xml = temp_dir / "malformed.xml"
        malformed_xml.write_text("<?xml version='1.0'?><root><unclosed>")

        with pytest.raises(ET.ParseError):
            xml.ExpDef(malformed_xml)

    def test_empty_xml_file(self, temp_dir):
        """Test handling of empty XML file."""
        empty_xml = temp_dir / "empty.xml"
        empty_xml.write_text("")

        with pytest.raises(ET.ParseError):
            xml.ExpDef(empty_xml)

    def test_xml_with_namespaces(self, temp_dir):
        """Test handling XML with namespaces."""
        ns_xml = temp_dir / "namespace.xml"
        ns_xml.write_text(
            """<?xml version="1.0"?>
<root xmlns:ns="http://example.com">
    <ns:element attr="value"/>
</root>"""
        )

        expdef = xml.ExpDef(ns_xml)
        assert expdef.root is not None

    def test_xml_with_comments(self, temp_dir):
        """Test handling XML with comments."""
        comment_xml = temp_dir / "comments.xml"
        comment_xml.write_text(
            """<?xml version="1.0"?>
<root>
    <!-- This is a comment -->
    <element>value</element>
</root>"""
        )

        expdef = xml.ExpDef(comment_xml)
        assert expdef.has_element(".//element")

    def test_very_deep_nesting(self, temp_dir):
        """Test handling very deeply nested XML."""
        depth = 20
        xml_start = '<?xml version="1.0"?>\n'
        xml_content = xml_start
        for i in range(depth):
            xml_content += f"<level{i}>"
        xml_content += "<data>value</data>"
        for i in range(depth - 1, -1, -1):
            xml_content += f"</level{i}>"

        deep_xml = temp_dir / "deep.xml"
        deep_xml.write_text(xml_content)

        expdef = xml.ExpDef(deep_xml)
        assert expdef.root is not None

    def test_special_characters_in_attributes(self, temp_dir):
        """Test handling special characters in attribute values."""
        special_xml = temp_dir / "special.xml"
        special_xml.write_text(
            """<?xml version="1.0"?>
<root>
    <element attr="&lt;&gt;&amp;&quot;&apos;"/>
</root>"""
        )

        expdef = xml.ExpDef(special_xml)
        assert expdef.has_attr(".//element", "attr")

    def test_unicode_in_xml(self, temp_dir):
        """Test handling Unicode characters in XML."""
        unicode_xml = temp_dir / "unicode.xml"
        unicode_xml.write_text(
            """<?xml version="1.0" encoding="utf-8"?>
<root>
    <element attr="こんにちは">Hello 世界</element>
</root>""",
            encoding="utf-8",
        )

        expdef = xml.ExpDef(unicode_xml)
        assert expdef.has_element(".//element")


################################################################################
# Performance Tests
################################################################################
class TestPerformance:
    """Test suite for performance-related scenarios."""

    def test_large_number_of_elements(self, temp_dir):
        """Test handling XML with large number of elements."""
        xml_content = '<?xml version="1.0"?>\n<root>\n'
        for i in range(1000):
            xml_content += f'  <item id="{i}"/>\n'
        xml_content += "</root>"

        large_xml = temp_dir / "large.xml"
        large_xml.write_text(xml_content)

        expdef = xml.ExpDef(large_xml)
        assert expdef.root is not None

    def test_many_modifications(self, simple_xml_file):
        """Test making many modifications in sequence."""
        expdef = xml.ExpDef(simple_xml_file)

        for i in range(100):
            expdef.element_add(".//config", f"item_{i}", allow_dup=True)

        adds, _ = expdef.n_mods()
        assert adds == 100


################################################################################
# Boundary Tests
################################################################################
class TestBoundaryConditions:
    """Test suite for boundary conditions."""

    def test_empty_attribute_value(self, simple_xml_file):
        """Test handling empty attribute values."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.attr_change(".//config/parameter", "name", "")
        assert result is True
        assert expdef.attr_get(".//config/parameter", "name") == ""

    def test_empty_element_addition(self, simple_xml_file):
        """Test adding element with empty attributes."""
        expdef = xml.ExpDef(simple_xml_file)
        result = expdef.element_add("config", "empty", attr={})
        assert result is True

    def test_root_level_operations(self, simple_xml_file):
        """Test operations at root level."""
        expdef = xml.ExpDef(simple_xml_file)
        # Root level queries
        assert expdef.has_element(".") is True

    def test_path_with_dots(self, nested_xml_file):
        """Test handling paths with single dot."""
        expdef = xml.ExpDef(nested_xml_file)
        assert expdef.has_element(".") is True
