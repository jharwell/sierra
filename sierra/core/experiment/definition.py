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
Wrapper around :class:`xml.etree.ElementTree` which contains a small set of
functionality for reading, writing, and manipulating XML files.
"""

# Core packages
import typing as tp
import os
import logging
import xml.etree.ElementTree as ET
import pickle

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.experiment import xml


class XMLExpDef:
    """Read, write, and modify parsed XML files into experiment definitions.

    Functionality includes single tag removal/addition, single attribute
    change/add/remove.

    Attributes:

        input_filepath: The location of the XML file to process.

        writer: The configuration for how the XML data will be written.
    """

    def __init__(self,
                 input_fpath: str,
                 write_config: tp.Optional[xml.WriterConfig] = None) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        self.tree = ET.parse(self.input_fpath)
        self.root = self.tree.getroot()
        self.tag_adds = xml.TagAddList()
        self.attr_chgs = xml.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

    def write_config_set(self, config: xml.WriterConfig) -> None:
        """Set the write config for the object; provided for cases in which the
        configuration is dependent on whether or not certain tags are present in
        the input file.
        """
        self.write_config = config

    def write(self, base_path: str) -> None:
        """Write the XML stored in the object to the filesystem according to
        configuration.
        """
        for config in self.write_config.values:

            if config['src_parent'] is None:
                src_root = config['src_tag']
            else:
                src_root = "{0}/{1}".format(config['src_parent'],
                                            config['src_tag'])

            tree = self.root.find(src_root)
            # Customizing the output write path is not required
            if 'opath_leaf' in config and config['opath_leaf'] is not None:
                opath = base_path + config['opath_leaf']
            else:
                opath = base_path

            if tree is None:
                self.logger.warning("Cannot write non-existent tree@%s to %s",
                                    src_root,
                                    opath)
                continue

            self.logger.trace("Write tree@%s to %s",  # type: ignore
                              src_root,
                              opath)

            # Renaming tree root is not required
            if 'rename_to' in config and config['rename_to'] is not None:
                tree.tag = config['rename_to']
                self.logger.trace("Rename tree root -> %s",  # type: ignore
                                  config['rename_to'])

            # Adding tags not required
            if 'dest_parent' in config and config['dest_parent'] is not None:
                to_write = ET.ElementTree()
                if 'create_tags' in config and config['create_tags'] is not None:
                    for spec in config['create_tags']:
                        if to_write.getroot() is None:
                            to_write._setroot(ET.Element(spec.tag, spec.attr))
                        else:
                            elt = to_write.find(spec.path)
                            ET.SubElement(elt, spec.tag, spec.attr)

                parent = to_write.getroot().find(config['dest_parent'])
                parent.append(tree)
            else:
                to_write = ET.ElementTree(tree)
                parent = to_write.getroot()

            # Grafts are not required
            if 'child_grafts' in config and config['child_grafts'] is not None:
                dest_root = "{0}/{1}".format(config['dest_parent'],
                                             config['src_tag'])
                graft_parent = to_write.getroot().find(dest_root)
                for g in config['child_grafts']:
                    self.logger.trace("Graft tree@%s as child under %s",  # type: ignore
                                      g,
                                      dest_root)
                    elt = self.root.find(g)
                    graft_parent.append(elt)

            # Write out pretty XML to make it easier to read to see if things
            # have been generated correctly.
            ET.indent(to_write, space="\t", level=0)
            to_write.write(opath, encoding='utf-8')

    def attr_get(self, path: str, attr: str):
        """
        Retrieve the specified attribute as a child of the element corresponding
        to the specified path, if it exists. If it does not exist, None is
        returned.

        """
        el = self.root.find(path)
        if el is not None and attr in el.attrib:
            return el.attrib[attr]
        return None

    def attr_change(self,
                    path: str,
                    attr: str,
                    value: str,
                    noprint: bool = False) -> None:
        """
        Change the specified attribute of the *FIRST* element matching the
        specified path searching from the tree root.

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
            return

        if attr not in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' not found in in path '%s'",
                                    attr,
                                    path)
            return

        el.attrib[attr] = value
        self.logger.trace("Modify attribute: '%s/%s' = '%s'",
                          path,
                          attr,
                          value)
        self.attr_chgs.add(xml.AttrChange(path, attr, value))

    def attr_add(self,
                 path: str,
                 attr: str,
                 value: str,
                 noprint: bool = False) -> None:
        """
        Add the specified attribute of the *FIRST* element matching the
        specified path searching from the tree root.

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
            return

        if attr in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' already in path '%s'",
                                    attr,
                                    path)
            return

        el.set(attr, value)
        self.logger.trace("Add new attribute: '%s/%s' = '%s'",  # type: ignore
                          path,
                          attr,
                          value)
        self.attr_chgs.add(xml.AttrChange(path, attr, value))

    def has_tag(self, path: str) -> bool:
        return self.root.find(path) is not None

    def tag_change(self, path: str, tag: str, value: str) -> None:
        """
        Change the specified tag of the element matching the specified path
        searching from the tree root.

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
            return

        for child in el:
            if child.tag == tag:
                child.tag = value
                self.logger.trace("Modify tag: '%s/%s' = '%s'",  # type: ignore
                                  path,
                                  tag,
                                  value)
                return
        self.logger.warning("No such element '%s' found in '%s'", tag, path)

    def tag_remove(self, path: str, tag: str, noprint: bool = False) -> None:
        """
        Remove the specified tag of the child element found in the enclosing
        parent specified by the path. If more than one tag matches, only one is
        removed.

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
            return

        victim = parent.find(tag)
        if victim is None:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'",
                                    tag,
                                    path)
            return

        parent.remove(victim)

    def tag_remove_all(self,
                       path: str,
                       tag: str,
                       noprint: bool = False) -> None:
        """
        Remove the specified tag(s) of the child element found in the enclosing
        parent specified by the path. If more than one tag matches in the
        parent, all matching child tags are removed.

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
            return

        victims = parent.findall(tag)
        if victims is None:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'",
                                    tag,
                                    path)
            return

        for victim in victims:
            parent.remove(victim)
            self.logger.trace("Remove matching tag: '%s/%s'",  # type: ignore
                              path,
                              tag)

    def tag_add(self,
                path: str,
                tag: str,
                attr={},
                allow_dup: bool = True,
                noprint: bool = False) -> None:
        """
        Add the tag name as a child element of the element found by the
        specified path, giving it the initial set of specified attributes.

        """
        parent = self.root.find(path)
        if parent is None:
            if not noprint:
                self.logger.warning("Parent node '%s' not found", path)
            return

        if not allow_dup:
            if parent.find(tag) is not None:
                if not noprint:
                    self.logger.warning("Child tag '%s' already in parent '%s'",
                                        tag,
                                        path)
                return

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


def unpickle(fpath: str) -> tp.Optional[tp.Union[xml.AttrChangeSet,
                                                 xml.TagAddList]]:
    """
    Read in all the different sets of parameter changes that were pickled to
    make crucial parts of the experiment definition easily accessible. You don't
    know how many there are, so go until you get an exception.
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
