# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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

"""
Wrapper around :py:class:`xml.etree.ElementTree` which contains a small set of functionality for
manipulating XML files.
"""

import xml.etree.ElementTree as ET
import logging


class InvalidElementError(RuntimeError):
    """Error class for when an element cannot be found or used."""


class XMLLuigi:
    """
    A class to help edit and save xml files.

    Functionality includes single tag removal/addition, single attribute change/add/remove.

    Attributes:
        input_filepath: The location of the xml file to process.
        output_filepath: Where the object should save changes it has made to the xml
                         file. (Defaults to overwriting the input file.)
    """

    def __init__(self, input_filepath: str, output_filepath: str = None) -> None:
        if output_filepath is None:
            output_filepath = input_filepath

        self.input_filepath = input_filepath
        self.output_filepath = output_filepath

        self.tree = ET.parse(input_filepath)
        self.root = self.tree.getroot()

    def write(self, filepath=None):
        """Write the XML stored in the object to an output filepath."""
        if filepath is None:
            filepath = self.output_filepath

        self.tree.write(filepath)

    def attr_get(self, path: str, attr: str):
        """
        Retrieve the specified attribute as a child of the element corresponding to the specified
        path, if it exists. If it does not exist, None is returned.
        """
        el = self.root.find(path)
        if el is not None and attr in el.attrib:
            return el.attrib[attr]
        return None

    def attr_change(self, path: str, attr: str, value: str, noprint: bool = False) -> None:
        """
        Change the specified attribute of the *FIRST* element matching the specified path searching
        from the tree root.

        Arguments:
          path: An XPath expression that for the element containing the attribute to
                change. The element must exist or an error will be raised.
          attr: Name of the attribute to change within the enclosing element.
          value: The value to set the attribute to.
        """
        el = self.root.find(path)
        if el is not None and self.has_tag(path) and attr in el.attrib:
            el.attrib[attr] = value
        else:
            if not noprint:
                logging.warning("No attribute '%s' found in node '%s'", attr, path)

    def has_tag(self, path: str) -> bool:
        return self.root.find(path) is not None

    def tag_change(self, path: str, tag: str, value: str) -> None:
        """
        Change the specified tag of the element matching the specified path searching
        from the tree root.

        Arguments:
          path: An XPath expression that for the element containing the tag to
                change. The element must exist or an error will be raised.
          attr: Name of the tag to change within the enclosing element.
          value: The value to set the tag to.
        """
        el = self.root.find(path)
        if el is None:
            logging.warning("Parent node '%s' not found", path)
            return

        for child in el:
            if child.tag == tag:
                child.tag = value
                return
        logging.warning("No such element '%s' found in '%s'", tag, path)

    def tag_remove(self, path: str, tag: str, noprint: bool = False) -> None:
        """
        Remove the specified tag of the child element found in the enclosing parent specified by the
        path.

        Arguments:
          path: An XPath expression that for the element containing the tag to
                remove. The element must exist or an error will be raised.
          tag: Name of the tag to remove within the enclosing element, in XPath syntax.
        """

        parent = self.root.find(path)
        if parent is not None:
            victim = parent.find(tag)
            if victim is not None:
                parent.remove(victim)
                return

        if not noprint:
            logging.warning("No victim '%s' found in parent '%s'", tag, path)

    def tag_add(self, path, tag, attr=dict()):
        """
        Add the tag name as a child element of the element found by the specified path, giving it
        the initial set of specified attributes.
        """
        ET.SubElement(self.root.find(path), tag, attr)


__api__ = [
    'InvalidElementError',
    'XMLLuigi',
]
