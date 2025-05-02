# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages

# 3rd party packages
from xmldiff import main

# Project packages
from sierra.core.experiment import definition
from sierra.plugins.expdef.xml.plugin import ExpDef, Writer
import sierra.core.logging


def test_rdrw():
    sierra.core.logging.initialize('INFO')

    config = definition.WriterConfig([{'src_parent': None,
                                       'src_tag': '.'}])
    exp1 = ExpDef(input_fpath="./tests/expdef/f1.xml",
                  write_config=config)

    exp1.write("/tmp/f1-out.xml")

    diff = main.diff_files("./tests/expdef/f1.xml", "/tmp/f1-out.xml")

    assert len(diff) == 0


def test_attr():
    exp1 = ExpDef(input_fpath="./tests/expdef/f1.xml")

    assert exp1.has_attr(".//controllers/crw_controller", "id")
    assert not exp1.has_attr(".//controller/crw_controller", "__NONE__")

    exp1.attr_change(".//params/output", "output_leaf", "__TODAY__")
    assert not exp1.attr_change(".//params/output", "baz", "__TODAY__")
    assert not exp1.attr_change(".//params/foo", "bar", "__TODAY__")
    assert exp1.attr_get(".//params/output", "output_leaf") == "__TODAY__"
    assert exp1.attr_get(".//params/output", "baz") is None

    exp1.attr_change(".//params/output", "__NONE__", "__TODAY__")
    assert not exp1.has_attr(".//params/output", "__NONE__")

    assert exp1.attr_add(".//params/output", "fizzbuzz", 17)
    assert not exp1.attr_add(".//params/output", "fizzbuzz", 17)
    assert not exp1.attr_add(".//params/fizz", "buzz", 17)
    assert exp1.attr_get(".//params/output", "fizzbuzz") == 17


def test_element():
    exp1 = ExpDef(input_fpath="./tests/expdef/f1.xml")

    assert exp1.has_element(".//nest")

    assert exp1.element_remove(".//params", "nest")
    assert exp1.has_element(".//nest")
    assert not exp1.element_remove(".//params", "nest")
    assert exp1.has_element(".//nest")

    exp1.element_remove_all(".//arena", "box")
    assert not exp1.has_element(".//box")
    assert not exp1.element_remove_all(".//arena", "box")
    assert not exp1.element_remove_all(".//foo", "box")
    assert not exp1.element_remove_all(".//arena", "box2")

    exp1.element_add(".//strategy/blocks", "explore")
    exp1.element_remove(".//strategy/blocks", "explore")
    assert exp1.has_element(".//strategy/blocks/explore")
    assert not exp1.element_add(".//strategy/fizz", "buzz")
    exp1.element_remove(".//strategy/blocks", "explore")
    assert not exp1.has_element(".//strategy/blocks/explore")
    assert not exp1.element_remove(".//strategy/foo", "explore")

    assert exp1.element_add(".//strategy/blocks", "explore", allow_dup=False)
    assert not exp1.element_add(".//strategy/blocks", "explore", allow_dup=False)

    exp1.element_change(".//controllers", "crw_controller", "foobar_controller")
    assert not exp1.has_element(".//controllers/crw_controller")
    assert exp1.has_element(".//controllers/foobar_controller")
    assert not exp1.element_change(".//foo", "crw_controller", "foobar_controller")
    assert not exp1.element_change(".//controllers",
                                   "crw_controller",
                                   "foobar_controller")


def test_write_root_rename():
    config = definition.WriterConfig([{
        'rename_to': 'foobar',
        'src_parent': None,
        'src_tag': '.'
    }])
    f = ExpDef(input_fpath="./tests/expdef/f2.xml",
               write_config=config)
    assert f.tree.getroot().tag == 'argos-configuration'

    f.write("/tmp/f2-out.xml")

    f2 = f = ExpDef(input_fpath="/tmp/f2-out.xml")

    assert f2.tree.getroot().tag == 'foobar'


def test_write_subtree():
    config = definition.WriterConfig([{
        'src_parent': '.',
        'src_tag': 'framework'
    }])
    f = ExpDef(input_fpath="./tests/expdef/f2.xml",
               write_config=config)
    assert f.tree.getroot().tag == 'argos-configuration'

    f.write("/tmp/f2-out.xml")

    f2 = f = ExpDef(input_fpath="/tmp/f2-out.xml")

    assert f2.tree.getroot().tag == 'framework'


def test_write_add_tags():
    config = definition.WriterConfig([{
        'src_parent': None,
        'src_tag': '.',
        'new_children_parent': '.',
        'new_children': [
            definition.ElementAdd.as_root('newroot', {}),
            definition.ElementAdd('.', 'tag1', {"foo": "7"}, False),
            definition.ElementAdd('.', 'tag2', {"bar": "baz"}, False),
            definition.ElementAdd('.//tag2', 'tag3', {"circle": "17"}, False)
        ]
    }])
    f = ExpDef(input_fpath="./tests/expdef/f2.xml",
               write_config=config)

    f.write("/tmp/f2-out.xml")

    f2 = f = ExpDef(input_fpath="/tmp/f2-out.xml")

    assert f2.has_element('.//tag1')
    assert f2.has_element('.//tag2')
    assert f2.has_element('.//tag2/tag3')
    assert f2.has_attr('.//tag1', "foo")
    assert f2.attr_get('.//tag1', 'foo') == "7"

    assert f2.has_element('.//tag2/tag3')
    assert f2.has_attr('.//tag2/tag3', "circle")
    assert f2.attr_get('.//tag2/tag3', 'circle') == "17"


def test_write_add_grafts():
    config = definition.WriterConfig([{
        'src_parent': None,
        'src_tag': 'framework',
        'child_grafts_parent': '.',  # really .//framework
        'child_grafts': [
            './/controllers/crw_controller/actuators',
            './/controllers/crw_controller/sensors'
        ]
    }])
    f = ExpDef(input_fpath="./tests/expdef/f3.xml",
               write_config=config)

    f.write("/tmp/f3-out.xml")

    f2 = f = ExpDef(input_fpath="/tmp/f3-out.xml")

    assert f2.has_element('.//actuators')
    assert f2.has_element('.//sensors')


def test_write_opath():
    for i in range(0, 3):
        config = definition.WriterConfig([{
            'rename_to': 'foobar',
            'src_parent': None,
            'src_tag': '.',
            'opath_leaf': i

        }])
        f = ExpDef(input_fpath="./tests/expdef/f2.xml",
                   write_config=config)
        assert f.tree.getroot().tag == 'argos-configuration'

        f.write("/tmp/f2-out.xml")

        f2 = f = ExpDef(f"/tmp/f2-out.xml{i}")

        assert f2.tree.getroot().tag == 'foobar'
