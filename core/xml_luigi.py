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
Wrapper around :class:`xml.etree.ElementTree` which contains a small set of functionality for
manipulating XML files.
"""

# Core packages
import logging
import typing as tp
import pickle
import os

# 3rd party packages

# Project packages
import xml.etree.ElementTree as ET


class XMLAttrChange():
    def __init__(self, path: str, attr: str, value: tp.Union[str, int, float]) -> None:
        self.path = path
        self.attr = attr
        self.value = str(value)

    def __iter__(self):
        yield from [self.path, self.attr, self.value]

    def __repr__(self) -> str:
        return self.path + '/' + self.attr + ': ' + str(self.value)


class XMLTagRm():
    def __init__(self, path: str, tag: str):
        self.path = path
        self.tag = tag

    def __iter__(self):
        yield from [self.path, self.tag]


class XMLTagAdd():
    def __init__(self, path: str, tag: str, attr: dict = dict()):
        self.path = path
        self.tag = tag
        self.attr = attr

    def __iter__(self):
        yield from [self.path, self.tag, self.attr]


class XMLAttrChangeSet():
    @staticmethod
    def unpickle(fpath: str) -> 'XMLAttrChangeSet':
        """
        Read in all the different sets of parameter changes that were pickled to make crucial parts
        of the experiment definition easily accessible. I don't know how many there are, so go until
        you get an exception.

        """
        try:
            with open(fpath, 'rb') as f:
                exp_def = XMLAttrChangeSet()
                while True:
                    exp_def |= XMLAttrChangeSet(*pickle.load(f))
        except EOFError:
            pass
        return exp_def

    def __init__(self, *args: XMLAttrChange) -> None:
        self.changes = set(args)
        self.logger = logging.getLogger(__name__)

    def __len__(self) -> int:
        return len(self.changes)

    def __iter__(self) -> tp.Iterator[XMLAttrChange]:
        return iter(self.changes)

    def __ior__(self, other: 'XMLAttrChangeSet') -> 'XMLAttrChangeSet':
        self.changes |= other.changes
        return self

    def __or__(self, other: 'XMLAttrChangeSet') -> 'XMLAttrChangeSet':
        new = XMLAttrChangeSet(*self.changes)
        new |= other
        return new

    def __repr__(self) -> str:
        return str(self.changes)

    def add(self, chg: XMLAttrChange) -> None:
        self.changes.add(chg)

    def pickle(self, fpath: str, delete: bool = False) -> None:
        if delete and os.path.exists(fpath):
            os.remove(fpath)

        with open(fpath, 'ab') as f:
            pickle.dump(self.changes, f)


class XMLTagRmList():
    def __init__(self, *args: XMLTagRm) -> None:
        self.rms = list(args)

    def __len__(self) -> int:
        return len(self.rms)

    def __iter__(self) -> tp.Iterator[XMLTagRm]:
        return iter(self.rms)

    def extend(self, other: 'XMLTagRmList') -> None:
        self.rms.extend(other.rms)

    def append(self, other: XMLTagRm) -> None:
        self.rms.append(other)


class XMLTagAddList():
    def __init__(self, *args: XMLTagAdd) -> None:
        self.adds = list(args)

    def __len__(self) -> int:
        return len(self.adds)

    def __iter__(self) -> tp.Iterator[XMLTagAdd]:
        return iter(self.adds)

    def extend(self, other: 'XMLTagAddList') -> None:
        self.adds.extend(other.adds)

    def append(self, other: XMLTagAdd) -> None:
        self.adds.append(other)


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
        self.logger = logging.getLogger(__name__)

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
        if el is None:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return

        if attr not in el.attrib:
            if not noprint:
                self.logger.warning("Atribute '%s' not found in in path '%s'", attr, path)
            return

        el.attrib[attr] = value

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
            self.logger.warning("Parent node '%s' not found", path)
            return

        for child in el:
            if child.tag == tag:
                child.tag = value
                return
        self.logger.warning("No such element '%s' found in '%s'", tag, path)

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
            self.logger.warning("No victim '%s' found in parent '%s'", tag, path)

    def tag_add(self, path, tag, attr=dict()):
        """
        Add the tag name as a child element of the element found by the specified path, giving it
        the initial set of specified attributes.
        """
        el = self.root.find(path)
        if el is None:
            self.logger.warning("Parent node '%s' not found", path)
            return

        ET.SubElement(el, tag, attr)


__api__ = [
    'InvalidElementError',
    'XMLLuigi',
    'XMLAttrChange',
    'XMLAttrChangeSet',
    'XMLTagAdd',
    'XMLTagAddList',
    'XMLTagRm',
    'XMLTagRmList'
]
