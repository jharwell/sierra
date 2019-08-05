"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

import xml.etree.ElementTree as ET


class InvalidElementError(RuntimeError):
    """Error class for when an element cannot be found or used."""
    pass


class XMLLuigi:
    def __init__(self, input_filepath, output_filepath=None):
        """
         A class to help edit (add, remove, modify tags/attributes) and save xml files.

         Parameters:
             input_filepath: The location of the xml file to process.
             output_filepath (optional): Where the object should save changes it has made to the xml
                                         file. (Defaults to overwriting the input file.)
        """
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

    def attribute_change(self, path, attr, value, noprint=False):
        """
        Change the specified attribute of the *FIRST* element matching the specified path searching
        from the tree root.

        Parameters:
          path(str): An XPath expression that for the element containing the attribute to
                     change. The element must exist or an error will be raised.
          attr(str): Name of the attribute to change within the enclosing element.
          value(str): The value to set the attribute to.
        """
        el = self.root.find(path)

        if self.has_tag(path) and attr in el.attrib:
            el.attrib[attr] = value   # pytype: disable=attribute-error
        else:
            if not noprint:
                print("WARNING: No attribute '{1}' found in node '{0}'".format(path, attr))

    def has_tag(self, path):
        return self.root.find(path) is not None

    def tag_change(self, path, tag, value):
        """
        Change the specified tag of the element matching the specified path searching
        from the tree root.

        Parameters:
          path(str): An XPath expression that for the element containing the tag to
                     change. The element must exist or an error will be raised.
          attr(str): Name of the tag to change within the enclosing element.
          value(str): The value to set the tag to.
        """

        el = self.root.find(path)
        for child in el:
            if child.tag == tag:
                child.tag = value
                return
        raise InvalidElementError("No such element '{0}' found in '{1}'".format(tag, path))

    def tag_remove(self, path, tag, noprint=False):
        """
        Remove the specified tag of the child element found in the enclosing parent specified by the
        path.

        Parameters:
          path(str): An XPath expression that for the element containing the tag to
                     remove. The element must exist or an error will be raised.
          tag(str): Name of the tag to remove within the enclosing element, in XPath syntax.
        """

        try:
            parent = self.root.find(path)
            victim = parent.find(tag)    # pytype: disable=attribute-error
            parent.remove(victim)   # pytype: disable=attribute-error
        except (AttributeError, TypeError):
            if not noprint:
                print("WARNING: No victim '{0}' found in parent '{1}'".format(tag, path))
            pass

    def tag_add(self, path, tag, attr={}):
        ET.SubElement(self.root.find(path), tag, attr)
