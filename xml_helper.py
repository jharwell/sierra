'''
By: London Lowmanstone

Terminology/Definitions:
    attribute path: same thing as an element path except for it ends with an attribute. In the form "tag.tag.(...).tag.attribute".

    element path: something in the form "tag.tag.(...).tag.tag" that specifies an element in the tree.

    element path list: same thing as an element path except for it's in the form [tag, tag, ..., tag, tag].

    empty path: a loose path path with no tags or attributes. Refers to the first element found (usually the root element).

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

import xml.etree.ElementTree as ET


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


    def write(self, filepath=None):
        '''Write the XML stored in the object to an output filepath.'''
        if filepath is None:
            filepath = self.output_filepath

        self.tree.write(filepath)


    def get_element(self, path):
        '''Alias for get_element_with_loose_attribute_path.'''
        return self.get_element_with_loose_attribute_path(path)


    def set_attribute(self, path):
        '''Alias for set_attribute_with_loose_path_to.'''
        return self.set_attribute_with_loose_path_to(path)


    def remove_element(self, path):
        '''Alias for remove_element_with_loose_strict_path.'''
        return self.remove_element_with_loose_strict_path(path)


    def remove_element_with_loose_strict_path(self, path):
        '''
        Takes a loose-strict path to an element.
        Removes that element from the tree (including all of its subelements).
        Raises an InvalidElementError if an element cannot be found or if the specified element is the root element.
        Restriction: the root element cannot be removed.
        '''
        return self._remove_element_with_loose_strict_path_list(self._path_to_path_list(path))

    def strict_loose_to_strict_path_list(self, path_list):
        '''
        Takes a strict-loose path list and returns the corresponding strict path list.
        '''
        # find out the strict location of the first tag
        strict_start = self.get_element_with_loose_attribute_path()


    def get_element_with_loose_attribute_path(self, path):
        '''
        Takes a loose path to an attribute.
        Returns an element with the matching attribute.
        (Returns None if such an element cannot be found.)
        '''

        return self._get_element_with_loose_attribute_path_list(self._path_to_path_list(path))

    def _path_to_path_list(self, path):
        '''Takes a path and returns the corresponding path list.'''
        return path.split(".")

    def _remove_element_with_loose_strict_path_list(self, path_list):
        '''TODO document'''
        strict_element_list = self._loose_strict_element_path_list_to_strict_element_list(path_list)
        strict_element_list[-2].remove(strict_element_list[-1])

    def _loose_strict_element_path_list_to_strict_element_list(self, path_list):
        '''Takes a loose-strict element path list and returns the corresponding strict element list.'''
        initial_tag = path_list.pop(0)
        # will have the element corresponding to the first tag in the list
        initial_strict_element_list = self._loose_element_path_list_to_strict_element_list([initial_tag])
        if initial_strict_element_list is None:
            return None
        else:
            ans = self._strict_element_path_list_to_strict_element_list_starting_at(path_list, initial_strict_element_list[0]) # TODO write
            if ans is None:
                return None
            else:
                return initial_strict_element_list + ans

    def _strict_element_path_list_to_strict_element_list_starting_at(self, path_list, starting_element):
        # base case
        if not path_list:
            # the list is empty, we've reached the goal
            return []

        goal_tag = path_list.pop(0)

        # iterate through children
        for subelement in starting_element:
            if subelement.tag == goal_tag:
                ans = self._strict_element_path_list_to_strict_element_list_starting_at(path_list, subelement)
                if ans is not None:
                    return [subelement] + ans

        return None


    def _loose_element_path_list_to_strict_element_list(self, path_list):
        '''Takes a loose element path list and returns the corresponding strict path list'''
        # TODO dp
        print("Here's the path list I got")
        print(path_list)
        path_list, starting_element = self._check_path_list_starting_point(path_list)
        print("after")
        print(path_list)
        ans = self._loose_element_path_list_to_strict_element_list_starting_at(path_list, starting_element)
        print("ans:", ans)
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

        for subelement in starting_element:
            if subelement.tag == goal_tag:
                # this might be the element we were searching for next
                new_path_list = path_list[1:]
            else:
                new_path_list = path_list[:]
            ans = self._loose_element_path_list_to_strict_element_list_starting_at(new_path_list, subelement)
            if ans is not None:
                return [subelement] + ans
        # could not find the rest of the path under this starting element
        return None


    def _get_element_with_loose_strict_path_list(self, path_list):
        '''TODO document'''
        starting_element = self._get_element_with_loose_path_list(path_list[0])
        return get_element_with_strict_path_list_inside(self, path_list[1:], starting_element)

    # def _get_element_with_loose_path_list(self, path_list): # TODO if going to use this, check _check_path function for ([root]) case
    #     '''TODO document'''
    #     return self._get_element_with_loose_path_list_inside(self._check_path_list_starting_point(path_list))

    def _get_element_with_strict_path_list_inside(self, path_list, starting_element):
        '''TODO document'''
        # base case
        if not path_list:
            # the list is empty, we've reached the goal
            return starting_element

        goal_tag = path_list.pop(0)

        for subelement in starting_element:
            if subelement.tag == goal_tag:
                ans = self._get_element_with_strict_path_list_inside(path_list, subelement)
                if ans is not None:
                    return ans

        return None



    # TODO if going to use this, check _check_path for [root] case
    # def _get_element_with_loose_attribute_path_list(self, path_list, starting_element=None):
    #     '''TODO document'''
    #     return self._get_element_with_loose_attribute_path_list_inside(*self._check_path_list_starting_point(path_list, starting_element))

    def _check_path_list_starting_point(self, path_list, starting_element=None):
        '''
        Helper function for finding the correct place to start a search.
        If starting_element is None, this means that the search is inside the document as a whole.
        The goal is to pass the data to a function that searches inside an element; the document is not an element.
        So this function minimizes the search to a search within
        So this will check if the root element matches with the first tag, making it so that the search can then be done inside of the root element.'''
        if starting_element is None:
            # deal with the case where we search inside the xml document itself
            starting_element = self.root

            if len(path_list) >= 1 and path_list[0] == self.root.tag:
                # having the root as the first tag will cause the function to search inside root for root itself (and thus fail), so catch that case here.
                path_list = path_list[1:]

        return (path_list, starting_element)

    def set_attribute_with_loose_path_to(self, path, value):
        '''
        Takes a loose path to an attribute and sets that attribute to the given value.
        Raises an InvalidElementError if a matching element with the attribute cannot be found.
        Converts the value to a string before setting the attribute.
        '''
        path_list = self._path_to_path_list(path)
        element = self._get_element_with_loose_attribute_path_list(path_list)
        if element is not None:
            value = str(value)
            element.set(path_list[-1], value)
        else:
            raise InvalidElementError("An element matching the path attribute '{}' could not be found".format(path))

    def _get_element_with_loose_path_list_inside(self, path_list, starting_element):
        '''
        Recursive function that takes a loose element path list and an element object to start the search at.
        Returns an element inside the starting element that matches the given path.
        (Returns None if such an element cannot be found.)
        Restriction: only searches *inside* the starting_element for the an element with the given path.
            This means that a strict path list *will not work*; it won't be able to find the root tag within the root tag.
        '''
        # base case
        if not path_list:
            # the list is empty, we've found the goal
            return starting_element

        goal_tag = path_list.pop(0)
        # iterate through matching inner elements
        for element in starting_element.iter(goal_tag):
            if element is starting_element:
                # skip over searching starting_element for the tag or attribute; we're only interested in subelements
                continue

                ans = self._get_element_with_loose_path_list_inside(path_list, element)
                if ans is not None:
                    return ans

        # no matching element was found under the starting element
        return None


    def _get_element_with_loose_attribute_path_list_inside(self, path_list, starting_element):
        '''
        Recursive function that takes a loose attribute path list and an element object to start the search at.
        Returns an element with the matching attribute.
        (Returns None if such an element cannot be found.)
        Restriction: only searches *inside* the starting_element for the loose attribute path list.
            This means that a strict path list will not work; it won't be able to find the root tag within the root tag.
        Note that if the element matching the last tag in the path list does not have the given attribute,
            this function will search for that attribut
        '''
        if len(path_list) == 1:
            # looking for an element with the attribute path_list[0]
            if starting_element.get(path_list[0]) is not None:
                # it's in this tag specifically
                return starting_element
            else:
                # search all inner elements of this tag for something with this attribute
                goal_tag = None
        else:
            # searching for an element with this tag
            goal_tag = path_list.pop(0)

        # iterate through inner elements that match the goal tag
        for element in starting_element.iter(goal_tag):
            if element is starting_element:
                # skip over searching starting_element for the tag or attribute; we're only interested in subelements
                continue

            ans = self._get_element_with_loose_attribute_path_list_inside(path_list, element)
            if ans is not None:
                return ans

        # no matching element was found under the starting element
        return None


if __name__ == "__main__":
    x = XMLHelper("Sample XML Files/single-source-test.argos")
    # ans = x.get_element_with_path_attribute("footbot_light.implementation")
    # print(ans.get("implementation"))
    # x.set_attribute_with_loose_path_to("differential_steering.implementation", "hello world")
    # print(x.get_element("actuators.implementation").get("implementation"))
    # x.remove_element()
    # x.write() # to change it on the actual file
    print(x._loose_strict_element_path_list_to_strict_element_list(["argos-configuration", "loop_functions", "visualization"]))
    print(x._loose_strict_element_path_list_to_strict_element_list(["argos-configuration", "visualization"]))
    x.remove_element("argos-configuration.visualization")
    x.write()
