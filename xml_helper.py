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

'''
Terminology/Definitions:
    attribute path: same thing as an element path except for it ends with an attribute. In the form "tag.tag.(...).tag.attribute".

    element list: a list of elements in the form [element, element, element].
        Usually corresponds to a element path list. (See "element path list".)

    element path: a string in the form "tag.tag.(...).tag.tag" that specifies an element in the tree.

    element path list: same thing as an element path except for it's a list in the form [tag, tag, ..., tag, tag].

    empty path: a loose path with no tags or attributes (written as ""). Refers to the first element found (usually the root element).

    loose attribute path: same as a loose element path, except for the final attribute must be an attribute of the element with the previous tag.
        (See "attribute path" for more clarification.)

    loose attribute path list: (see "attribute path", "loose attribute path", and "element path list", for the corresponding definitions.)

    loose element path: a path where all of the subsequent tags in the path are children of the previous tags, but generations may be skipped.
        For example, the bath "b.d.g" may refer to something with the specific path "a.b.c.d.e.f.g".

    loose search: (see "strict search" for the corresponding definition.)

    loose-strict element path: a path where the first tag in the path is found via a loose search, and the following path_list are expected to be direct children.
        In other words, this is basically a strict path that doesn't start with the root tag.

    loose-strict search: (see "strict search" for the corresponding definition.)

    strict path: a path that begins with the root tag and each subsequent tag is a child of the previous tag.
        Specifies exactly one element (or attribute; the attribute must be an attribute of the most recent tag).

    strict search: a search for an element using a strict path.

    If you cannot find a specific term, search for similar terms in the above list to understand the meaning.
        (See "loose attribute path list" for an example of this.)
'''

'''
TODO: right now, loose strict paths are not found correctly. The current algorithm merely looks for the first tag loosely and assumes all the strict tags will come afterwards.
    This may not always be the case: the first element that comes up in the loose search for the first tag may not be the right element; it could be a different element with the same tag.
    Switching to functions that returned generators (rather than just returning the first value found) would help solve this issue.
    Everything should work correctly as long as the following restriction is followed:
    restriction: the first tag in a loose strict path should refer to the topmost element with that tag
'''


class InvalidElementError(RuntimeError):
    '''Error class for when an element cannot be found or used.'''
    pass


class XMLHelper:
    def __init__(self, input_filepath, output_filepath=None):
        '''
        A class to help edit and save xml files.
        Parameters:
            input_filepath: the location of the xml file to process.
            output_filepath (optional): where the object should save changes it has made to the xml file.
                (Defaults to overwriting the input file.)
        '''
        if output_filepath is None:
            output_filepath = input_filepath

        self.input_filepath = input_filepath
        self.output_filepath = output_filepath

        self.tree = ET.parse(input_filepath)
        # restriction: assumes the root of the xml file is not going to change
        self.root = self.tree.getroot()


    ### Simple exposed functions ###
    # These are the functions most people should call
    def write(self, filepath=None):
        '''Write the XML stored in the object to an output filepath.'''
        if filepath is None:
            filepath = self.output_filepath

        self.tree.write(filepath)

    def set_attribute(self, path, value):
        '''Alias for set_attribute_with_loose_path_to.'''
        return self.set_attribute_with_loose_path_to(path, value)

    def set_tag(self, path, value):
        '''Alias for set_tag_of_element_with_loose_strict_path_to.'''
        return self.set_tag_of_element_with_loose_strict_path_to(path, value)

    def remove_element(self, path):
        '''Alias for remove_element_with_loose_strict_path.'''
        return self.remove_element_with_loose_strict_path(path)


    ### Explicit exposed functions ###
    # These functions can be called, and they have more explicit names
    # I separate them from the simple functions so that end users don't need to be confused by them
    def set_attribute_with_loose_path_to(self, path, value):
        '''
        Takes a loose path to an attribute and sets that attribute to the given value.
        Raises an InvalidElementError if a matching element with the attribute cannot be found.
        Converts the value to a string before setting the attribute.
        '''
        path_list = self._path_to_path_list(path)
        element = self._get_element_with_loose_attribute_path_list_inside(
            *self._check_path_list_starting_point(path_list))
        if element is not None:
            value = str(value)
            element.set(path_list[-1], value)
        else:
            raise InvalidElementError(
                "An element matching the path attribute '{}' could not be found".format(path))

    def set_tag_of_element_with_loose_strict_path_to(self, path, value):
        '''Takes a loose strict path to an element and sets the tag of that element to the given value.'''
        try:
            return self._set_tag_of_element_with_loose_strict_path_list_to(self._path_to_path_list(path), value)
        except InvalidElementError:
            raise InvalidElementError("Could not find the element with the loose strict path '{}'".format(path))

    def remove_element_with_loose_strict_path(self, path):
        '''
        Takes a loose-strict path to an element.
        Removes that element from the tree (including all of its subelements).
        Raises an InvalidElementError if an element cannot be found or if the specified element is the root element.
        Restriction: the root element cannot be removed.
        '''
        return self._remove_element_with_loose_strict_path_list(self._path_to_path_list(path))


    ### Private functions ###
    # These are the helper functions that are used by other functions in the class
    # These start with an underscore to indicate that they are private and should not be called by end users
    def _path_to_path_list(self, path):
        '''Takes a path and returns the corresponding path list.'''
        return path.split(".")

    def  _set_tag_of_element_with_loose_strict_path_list_to(self, path_list, value):
        '''Takes a loose strict path list to an element and sets the tag of that element to the given value.'''
        try:
            # get the specified element at the end of the path
            element = self._loose_strict_element_path_list_to_strict_element_list(path_list)[-1]
            element.tag = value
        except:
            raise InvalidElementError("The element with path_list {} could not be found".format(path_list))


    def _remove_element_with_loose_strict_path_list(self, path_list):
        '''Takes a loose strict element path list and removes the corresponding element (and all of it's subelements) from the tree.'''
        strict_element_list = self._loose_strict_element_path_list_to_strict_element_list(
            path_list)
        try:
            strict_element_list[-2].remove(strict_element_list[-1])
        except (IndexError, TypeError) as e:
            if isinstance(e, IndexError):
                # trying to remove the root element
                raise InvalidElementError("You cannot remove the root element")
            else:  # TypeError: the strict element list was not found
                raise InvalidElementError(
                    "The element path list {} could not be found".format(path_list))

    def _loose_strict_element_path_list_to_strict_element_list(self, path_list):
        '''
        Takes a loose-strict element path list and returns the corresponding strict element list.
        This function will modify the element path list.
        '''
        initial_tag = path_list.pop(0)
        # will have the element corresponding to the first tag in the list
        initial_strict_element_list = self._loose_element_path_list_to_strict_element_list([initial_tag])
        if initial_strict_element_list is None:
            # couldn't find the first tag
            raise InvalidElementError("Could not find the tag '{}' which came at the start of a loose strict path".format(initial_tag))
        ans = self._strict_element_path_list_to_strict_element_list_starting_at(
            path_list, initial_strict_element_list[-1])
        return initial_strict_element_list + ans


    def _strict_element_path_list_to_strict_element_list_starting_at(self, path_list, starting_element):
        '''Takes a strict element path list starting under a given starting element, and returns the element list corresponding to the path list'''
        # base case
        if not path_list:
            # the list is empty, we've reached the goal
            return []

        goal_tag = path_list.pop(0)
        # iterate only through direct children
        for subelement in starting_element:
            if not subelement is starting_element and self._has_tag_or_id(subelement, goal_tag):
                try:
                    ans = self._strict_element_path_list_to_strict_element_list_starting_at(
                        path_list, subelement)
                    return [subelement] + ans
                except InvalidElementError:
                    # couldn't find it; move on to the next one
                    pass


        raise InvalidElementError("Could not find an element matching the strict path list {} by looking under the element {}".format(path_list, starting_element))

    def _loose_element_path_list_to_strict_element_list(self, path_list):
        '''Takes a loose element path list and returns the corresponding strict element list'''
        path_list, starting_element = self._check_path_list_starting_point(
            path_list)
        ans = self._loose_element_path_list_to_strict_element_list_starting_at(
            path_list, starting_element)
        if ans is None:
            return ans
        else:
            return [starting_element] + ans

    def _loose_element_path_list_to_strict_element_list_starting_at(self, path_list, starting_element):
        '''Takes a loose element path list and a starting element to search in, and returns the strict path list continuing after the starting element'''
        # base case
        if not path_list:
            # we have gotten to the end of the list
            return []

        goal_tag = path_list[0]

        # iterate through all direct children
        for subelement in starting_element:
            if not subelement is starting_element and self._has_tag_or_id(subelement, goal_tag):
                # this might be the element we were searching for next
                new_path_list = path_list[1:]
            else:
                new_path_list = path_list[:]
            ans = self._loose_element_path_list_to_strict_element_list_starting_at(
                new_path_list, subelement)
            if ans is not None:
                return [subelement] + ans
        # could not find the rest of the path under this starting element
        return None

    def _check_path_list_starting_point(self, path_list, starting_element=None):
        '''
        Helper function for finding the correct place to start a search.
        If starting_element is None, this means that the search is inside the document as a whole.
        The goal is to pass the data to a function that searches inside an element; the document is not an element.
        So this will check if the root element matches with the first tag, making it so that the search can then be done inside of the root element.
        restriction: do not have elements inside the root element with the same tag or id as the root element
        # Warning: this may cause a subsequent search to fail or return an incorrect value if there are multiple elements with the same tag as the root
            # for example, searching for the loose strict path "a.a.b.c" might not be able to find "a.e.a.a.b.c" because it will search for "a.b.c" directly below the first "a"
            # if the above restriction is followed, everything should work as expected.
        # upgrade: the starting_element parameter may not be needed; if this function is being used, it's probably set to None.

        path_list is an element path list
        starting_element is an element object
        '''

        if starting_element is None:
            # deal with the case where we search inside the xml document itself
            starting_element = self.root

            if len(path_list) >= 1 and self._has_tag_or_id(self.root, path_list[0]):
                # having the root as the first tag will cause the function to search inside root for root itself (and thus fail), so catch that case here.
                path_list = path_list[1:]

        return (path_list, starting_element)

    def _get_element_with_loose_attribute_path_list_inside(self, path_list, starting_element):
        '''
        Takes a loose attribute path list.
        Returns an element with the matching attribute.
        (Returns None if such an element cannot be found.)
        '''
        if len(path_list) == 1:
            # looking for an element with the attribute of path_list[0]
            if starting_element.get(path_list[0]) is not None:
                # it's in this tag specifically
                return starting_element
            else:
                # search all inner elements of this tag for something with this attribute
                goal_tag = None
        else:
            # searching for an element with this tag
            goal_tag = path_list[0]

        # iterate through inner elements
        for element in starting_element.iter():
            # skip over searching starting_element for the tag or attribute; we're only interested in the child elements
            if element is starting_element:
                continue

            # if this element matches the next part of the path, remove it from the path since it was found
            if self._has_tag_or_id(element, goal_tag):
                new_path_list = path_list[1:]
            else:
                # copy the path so that it can backtrack
                new_path_list = path_list[:]

            # check inside this element for the rest of the path
            try:
                return self._get_element_with_loose_attribute_path_list_inside(new_path_list, element)
            except InvalidElementError:
                # couldn't find the attribute under that element, try the next one
                pass

        # no matching element was found under the starting element
        raise InvalidElementError("Could not find an element matching the path list {} under the element {}".format(path_list, starting_element))

    def _has_tag_or_id(self, element, tag_or_id):
        '''
        Determines whether or not the given element has the given tag or id
        element is an element object
        tag_or_id is a tag (a string)
        '''
        # check to see if the tag matches
        if element.tag == tag_or_id:
            return True
        # make sure it has an id and that the id matches
        if "id" in element.attrib and element.attrib["id"] == tag_or_id:
            return True
        return False


if __name__ == "__main__":
    x = XMLHelper("testing_generated_configs/new-single-source-test_0.argos")
    x.remove_element("actuators.differential_steering")
    x.set_attribute("arena.wall_east.position", "big")
    # x.set_tag("loop_functions.output.grid", "hello")
    x.write("testing4.argos")
