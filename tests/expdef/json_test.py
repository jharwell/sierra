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
import jsondiff
import json
import pathlib

# Project packages
from sierra.core.experiment import definition
from sierra.plugins.expdef.json.plugin import ExpDef
import sierra.core.logging


def test_rdrw():
    sierra.core.logging.initialize('INFO')

    config = definition.WriterConfig([{'src_parent': None,
                                       'src_tag': '$'}])
    exp1 = ExpDef(input_fpath="./tests/expdef/f9.json",
                  write_config=config)

    exp1.write("/tmp/f9-out.json")

    diff = jsondiff.diff(json.load(open("./tests/expdef/f9.json")),
                         json.load(open("/tmp/f9-out.json")))

    assert len(diff) == 0


def test_f2():
    f = ExpDef(input_fpath="./tests/expdef/f2.json")

    # Element existence
    assert f.has_element("$.colors")
    assert not f.has_element("$.colorss")

    # Attribute existence
    assert f.has_attr("$.colors[?(@.value1=='foo')]",
                      "color")
    assert f.has_attr("$.colors[?(@.value2=='bar')]",
                      "color")
    assert not f.has_attr("$.colors[?(@.value1=='foo')]",
                          "value")
    assert not f.has_attr("$.colors[?(@.value1=='bar')]",
                          "color")

    # Attribute update
    assert f.attr_change("$.colors[?(@.value2=='bar')]",
                         "value2",
                         "baz")
    assert not f.attr_change("$.colors[?(@.value2=='bar')]",
                             "value2",
                             "bar")

    assert f.has_attr("$.colors[?(@.value2=='baz')]",
                      "color")

    assert not f.has_attr("$.colors[?(@.color=='blue')]",
                          "number")

    assert f.attr_add("$.colors[?(@.color=='red')]", "number", "1")

    assert f.attr_get("$.colors[?(@.color=='red')]",
                      "number") == "1"
    assert f.attr_get("$.colors[?(@.color=='blue')]",
                      "number") is None

    # Add element to non-existing parent
    assert not f.element_add("$.numbers", "numbers", {"one": "1", "two": "2"})

    # Add a new element
    assert f.element_add("$", "numbers", {"one": "1", "two": "2"})
    assert f.has_element("$.numbers")
    assert f.has_attr("$.numbers", "one")
    assert f.attr_get("$.numbers", "one") == "1"
    assert f.element_add("$", "numbers", {"three": "3", "four": "4"})
    assert f.has_element("$.numbers")
    assert f.has_attr("$.numbers", "three")
    assert f.attr_get("$.numbers", "three") == "3"

    # Add an already existing element, causing a list to be created
    assert not f.element_add("$",
                             "numbers",
                             {"one": "1", "two": "2"},
                             allow_dup=False)
    assert f.has_element("$.numbers")
    assert f.has_attr("$.numbers", "one")
    assert f.has_attr("$.numbers", "two")
    assert f.has_attr("$.numbers", "three")
    assert f.has_attr("$.numbers", "four")
    assert f.attr_get("$.numbers", "one") == "1"
    assert f.attr_get("$.numbers", "two") == "2"
    assert f.attr_get("$.numbers", "three") == '3'
    assert f.attr_get("$.numbers", "four") == '4'

    # Remove non-existing element
    assert not f.element_remove("$.numbers", "numbers")

    # Remove existing element
    assert f.element_remove("$", "numbers")
    assert not f.has_element("$.numbers")


def test_f4():
    f = ExpDef(input_fpath="./tests/expdef/f4.json")

    # Element existence
    assert f.has_element("$.batters")
    assert f.has_element("$.batters.batter")
    assert f.has_element("$.topping")
    assert not f.has_element("$.topping.type")
    # this is an attribute
    assert not f.has_element("$.topping[?(@.type=='None')].type")

    # Attribute existence. If a key doesn't map to a literal int, bool, etc., it
    # isn't an attribute.
    assert f.has_attr("$", "id")
    assert not f.has_attr("$", "batters")
    assert not f.has_attr("$.batters", "batter")
    assert not f.has_attr("$", "topping")

    # Attribute update
    assert f.attr_change("$",
                         "type",
                         "pie")
    assert f.has_attr("$", "type")
    assert f.attr_get("$", "type") == "pie"

    assert not f.attr_change("$.batters",
                             "batter",
                             "foo")
    assert f.has_element("$.batters.batter")
    assert f.attr_get("$.batters", "batter") is None
    assert f.attr_change("$.topping2[?(@.type=='Maple')]",
                         "id",
                         "foobar")
    assert f.attr_get("$.topping2[?(@.type=='Maple')]",
                      "id") == "foobar"

    assert f.element_remove("$", "topping")
    assert not f.has_element("$.topping")

    assert f.element_add("$", "topping2", {})
    assert f.has_element("$.topping2")
    assert f.element_add("$", "topping2", {})

    assert f.element_remove_all("$", "topping2")
    assert not f.has_element("$.topping2")


def test_flatten():
    sierra.core.logging.initialize('INFO')
    config = definition.WriterConfig([{'src_parent': None,
                                       'src_tag': '$'}])
    f1 = ExpDef(input_fpath=pathlib.Path("./tests/expdef/flatten.json"),
                write_config=config)
    f1.flatten(["$.batters.path",
                "$.topping[?(@.path =~ json)].path",
                ])
    f1.write("/tmp/flatten-out.json")

    diff = jsondiff.diff(json.load(open("./tests/expdef/flatten-out.json")),
                         json.load(open("/tmp/flatten-out.json")))

    assert len(diff) == 0
