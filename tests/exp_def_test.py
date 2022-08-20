# Copyright 2022 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

# Core packages

# 3rd party packages
from xmldiff import main

# Project packages
from sierra.core.experiment.definition import XMLExpDef
from sierra.core.experiment import xml
import sierra.core.logging


def test_rdrw():
    sierra.core.logging.initialize('INFO')

    config = xml.WriterConfig([{'src_parent': None,
                                'src_tag': '.'}])
    exp1 = XMLExpDef(input_fpath="./tests/test1.xml",
                     write_config=config)

    exp1.write("/tmp/test1-out.xml")

    diff = main.diff_files("./tests/test1.xml", "/tmp/test1-out.xml")

    assert len(diff) == 0


def test_attr():
    exp1 = XMLExpDef(input_fpath="./tests/test1.xml")

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


def test_tag():
    exp1 = XMLExpDef(input_fpath="./tests/test1.xml")

    assert exp1.has_tag(".//nest")

    assert exp1.tag_remove(".//params", "nest")
    assert exp1.has_tag(".//nest")
    assert not exp1.tag_remove(".//params", "nest")
    assert exp1.has_tag(".//nest")

    exp1.tag_remove_all(".//arena", "box")
    assert not exp1.has_tag(".//box")
    assert not exp1.tag_remove_all(".//arena", "box")
    assert not exp1.tag_remove_all(".//foo", "box")
    assert not exp1.tag_remove_all(".//arena", "box2")

    exp1.tag_add(".//strategy/blocks", "explore")
    exp1.tag_remove(".//strategy/blocks", "explore")
    assert exp1.has_tag(".//strategy/blocks/explore")
    assert not exp1.tag_add(".//strategy/fizz", "buzz")
    exp1.tag_remove(".//strategy/blocks", "explore")
    assert not exp1.has_tag(".//strategy/blocks/explore")
    assert not exp1.tag_remove(".//strategy/foo", "explore")

    assert exp1.tag_add(".//strategy/blocks", "explore", allow_dup=False)
    assert not exp1.tag_add(".//strategy/blocks", "explore", allow_dup=False)

    exp1.tag_change(".//controllers", "crw_controller", "foobar_controller")
    assert not exp1.has_tag(".//controllers/crw_controller")
    assert exp1.has_tag(".//controllers/foobar_controller")
    assert not exp1.tag_change(".//foo", "crw_controller", "foobar_controller")
    assert not exp1.tag_change(".//controllers",
                               "crw_controller",
                               "foobar_controller")
