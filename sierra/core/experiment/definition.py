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

"""
Functionality for reading, writing, and manipulating experiment definitions.

Currently, experiments can be specified in:

- XML
"""

# Core packages
import typing as tp
import logging
import xml.etree.ElementTree as ET
import sys
import pathlib

# 3rd party packages

# Project packages
from sierra.core.experiment import xml
from sierra.core import types


class XMLExpDef:
    """Read, write, and modify parsed XML files into experiment definitions.

    Functionality includes single tag removal/addition, single attribute
    change/add/remove.

    Attributes:

        input_filepath: The location of the XML file to process.

        writer: The configuration for how the XML data will be written.
    """

    def __init__(self,
                 input_fpath: pathlib.Path,
                 write_config: tp.Optional[xml.WriterConfig] = None) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        self.tree = ET.parse(self.input_fpath)
        self.root = self.tree.getroot()
        self.tag_adds = xml.TagAddList()
        self.attr_chgs = xml.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

        if sys.version_info < (3, 9):
            self.logger.warning(("XML files written with python < 3.9 "
                                 "are not human readable"))

    def write_config_set(self, config: xml.WriterConfig) -> None:
        """Set the write config for the object.

        Provided for cases in which the configuration is dependent on whether or
        not certain tags are present in the input file.

        """
        self.write_config = config

    def write(self, base_opath: pathlib.Path) -> None:
        """Write the XML stored in the object to the filesystem.

        """
        assert self.write_config is not None, \
            "Can't write without write config"

        writer = xml.Writer(self.tree)
        writer(self.write_config, base_opath)

    def attr_get(self, path: str, attr: str):
        """Retrieve the specified attribute of the element at the specified path.

        If it does not exist, None is returned.

        """
        el = self.root.find(path)
        if el is not None and attr in el.attrib:
            return el.attrib[attr]
        return None

    def attr_change(self,
                    path: str,
                    attr: str,
                    value: str,
                    noprint: bool = False) -> bool:
        """Change the specified attribute of the element at the specified path.

        Only the attribute of the *FIRST* element matching the specified path is
        changed.

        Arguments:

          path: An XPath expression that for the element containing the
                attribute to change. The element must exist or an error will be
                raised.

          attr: An XPath expression for the name of the attribute to change
                within the enclosing element.

          value: The value to set the attribute to.

        """
        el = self.root.find(path)
        if el is None:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return False

        if attr not in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' not found in in path '%s'",
                                    attr,
                                    path)
            return False

        el.attrib[attr] = value
        self.logger.trace("Modify attr: '%s/%s' = '%s'",  # type: ignore
                          path,
                          attr,
                          value)

        self.attr_chgs.add(xml.AttrChange(path, attr, value))
        return True

    def attr_add(self,
                 path: str,
                 attr: str,
                 value: str,
                 noprint: bool = False) -> bool:
        """Add the specified attribute to the element matching the specified path.

        Only the *FIRST* element matching the specified path searching from the
        tree root is modified.

        Arguments:

          path: An XPath expression that for the element containing the
                attribute to add. The element must exist or an error will be
                raised.

          attr: An XPath expression for the name of the attribute to change
                within the enclosing element.

          value: The value to set the attribute to.

        """
        el = self.root.find(path)
        if el is None:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return False

        if attr in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' already in path '%s'",
                                    attr,
                                    path)
            return False

        el.set(attr, value)
        self.logger.trace("Add new attribute: '%s/%s' = '%s'",  # type: ignore
                          path,
                          attr,
                          value)
        self.attr_chgs.add(xml.AttrChange(path, attr, value))
        return True

    def has_tag(self, path: str) -> bool:
        return self.root.find(path) is not None

    def has_attr(self, path: str, attr: str) -> bool:
        el = self.root.find(path)
        if el is None:
            return False
        return attr in el.attrib

    def tag_change(self, path: str, tag: str, value: str) -> bool:
        """
        Change the specified tag of the element matching the specified path.

        Arguments:

          path: An XPath expression that for the element containing the tag to
                change. The element must exist or an error will be raised.

          tag: An XPath expression of the tag to change within the enclosing
                element.

          value: The value to set the tag to.
        """
        el = self.root.find(path)
        if el is None:
            self.logger.warning("Parent node '%s' not found", path)
            return False

        for child in el:
            if child.tag == tag:
                child.tag = value
                self.logger.trace("Modify tag: '%s/%s' = '%s'",  # type: ignore
                                  path,
                                  tag,
                                  value)
                return True

        self.logger.warning("No such element '%s' found in '%s'", tag, path)
        return False

    def tag_remove(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove the specified child in the enclosing parent specified by the path.

        If more than one tag matches, only one is removed. If the path does not
        exist, nothing is done.

        Arguments:

          path: An XPath expression that for the element containing the tag to
                remove. The element must exist or an error will be raised.

          tag: An XPath expression of the tag to remove within the enclosing
               element.

        """

        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent node '%s' not found", path)
            return False

        victim = parent.find(tag)
        if victim is None:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'",
                                    tag,
                                    path)
            return False

        parent.remove(victim)
        return True

    def tag_remove_all(self,
                       path: str,
                       tag: str,
                       noprint: bool = False) -> bool:
        """Remove the specified tag(s) in the enclosing parent specified by the path.

        If more than one tag matches in the parent, all matching child tags are
        removed.

        Arguments:

          path: An XPath expression that for the element containing the tag to
                remove. The element must exist or an error will be raised.

          tag: An XPath expression for the tag to remove within the enclosing
               element.

        """

        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent node '%s' not found", path)
            return False

        victims = parent.findall(tag)
        if not victims:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'",
                                    tag,
                                    path)
            return False

        for victim in victims:
            parent.remove(victim)
            self.logger.trace("Remove matching tag: '%s/%s'",  # type: ignore
                              path,
                              tag)

        return True

    def tag_add(self,
                path: str,
                tag: str,
                attr: types.StrDict = {},
                allow_dup: bool = True,
                noprint: bool = False) -> bool:
        """
        Add tag name as a child element of enclosing parent.
        """
        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent node '%s' not found", path)
            return False

        if not allow_dup:
            if parent.find(tag) is not None:
                if not noprint:
                    self.logger.warning("Child tag '%s' already in parent '%s'",
                                        tag,
                                        path)
                return False

            ET.SubElement(parent, tag, attrib=attr)
            self.logger.trace("Add new unique tag: '%s/%s' = '%s'",  # type: ignore
                              path,
                              tag,
                              str(attr))
        else:
            # Use ET.Element instead of ET.SubElement so that child nodes with
            # the same 'tag' don't overwrite each other.
            child = ET.Element(tag, attrib=attr)
            parent.append(child)
            self.logger.trace("Add new tag: '%s/%s' = '%s'",  # type: ignore
                              path,
                              tag,
                              str(attr))

        self.tag_adds.append(xml.TagAdd(path, tag, attr, allow_dup))
        return True


def unpickle(fpath: pathlib.Path) -> tp.Optional[tp.Union[xml.AttrChangeSet,
                                                          xml.TagAddList]]:
    """Unickle all XML modifications from the pickle file at the path.

    You don't know how many there are, so go until you get an exception.

    """
    try:
        return xml.AttrChangeSet.unpickle(fpath)
    except EOFError:
        pass

    try:
        return xml.TagAddList.unpickle(fpath)
    except EOFError:
        pass

    raise NotImplementedError


__api__ = [
    'XMLExpDef',
]
