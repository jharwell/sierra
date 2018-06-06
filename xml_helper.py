import xml.etree.ElementTree as ET


class ElementNotFoundError(RuntimeError):
    '''Error class for when an element cannot be found.'''
    pass


class XMLHelper:
    def __init__(self, input_filename, output_filename=None):
        '''
        A class to help edit and save xml files
        parameters:
            input_filename: the location of the xml file to process
            output_filename (optional): where the object should save changes it has made to the xml file
                (defaults to overwriting the input file)
        '''
        if output_filename is None:
            output_filename = input_filename

        self.input_filename = input_filename
        self.output_filename = output_filename

        self.tree = ET.parse(input_filename)
        # restriction: assumes the root of the xml file is not going to change
        self.root = self.tree.getroot()


    def write(self, filename=None):
        '''Write the XML stored in the object to an output file path'''
        if filename is None:
            filename = self.output_filename

        self.tree.write(filename)


    def get_element(self, s):
        '''Alias for get_element_with_path_attribute'''
        return self.get_element_with_path_attribute(s)


    def set_element(self, s):
        '''Alias for set_path_attribute'''
        return self.set_path_attribute(s)


    def get_element_with_path_attribute(self, s):
        '''
        Takes a string in the form "tag.tag.tag.attribute" with as many tags as you want (only one attribute allowed).
        Returns the element that's in that position on the tree with that particular attribute.
        Each tag should be the descendant of a previous tag in the path, but does not have to be any previous tag's child.
        The attribute can also be in any descendant of the last tag. (If no tags are specified, the attribute can in any descendant of the root element)

        In other words, this is extremely flexible. As long as you follow the hierarchy, it should work.

        Returns None if an element on the given path without the given attribute is not found.
        '''
        # the last string in this list will be the attribute
        tag_list = s.split(".")

        if len(tag_list) > 1 and tag_list[0] == self.root.tag:
            # having the root as the first tag will cause self._get_element_with_path_attribute to search inside root for itself, so catch that case here.
            tag_list = tag_list[1:]

        return self._get_element_with_path_attribute(tag_list, starting_element=self.root)


    def set_path_attribute(self, s, value):
        '''
        Takes a path attribute (see "get_element_with_path_attribute" for form) and sets it to a particular value.
        Raises an ElementNotFoundError if a matching element for the given path attribute cannot be found
        '''
        element = self.get_element_with_path_attribute(s)
        if element is not None:
            element.set(s.split(".")[-1], value)
        else:
            raise ElementNotFoundError("An element matching the path attribute '{}' could not be found".format(s))


    def _get_element_with_path_attribute(self, tags, starting_element):
        '''
        Recursive function to accomplish the corresponding "public" function (the one without an underscore)
        Takes a list in the form [tag, tag, ..., tag, tag, attribute]
        As long as the specified tag and attributes are within the hierarchy, this will return the tag that contains the specified attribute.

        Returns None if a matching element cannot be found
        '''

        if len(tags) == 1:
            # looking for an element with the attribute tags[0]
            if starting_element.get(tags[0]) is not None:
                # it's in this tag specifically
                return starting_element
            else:
                # search all inner elements of this tag for something with this attribute
                goal_tag = None
        else:
            # searching for an element with this tag
            goal_tag = tags.pop(0)

        # iterate through inner elements
        for element in starting_element.iter(goal_tag):
            if element is starting_element:
                # skip over searching starting_element for the tag or attribute; we're only interested in the child elements
                continue

            ans = self._get_element_with_path_attribute(tags, element)
            if ans is not None:
                return ans

        # no matching element was found under the starting element
        return None


if __name__ == "__main__":
    x = XMLHelper("Sample XML Files/single-source.argos")
    # ans = x.get_element_with_path_attribute("footbot_light.implementation")
    # print(ans.get("implementation"))
    x.set_path_attribute("differential_steering.implementation", "hello world")
    # print(x.get_element("actuators.implementation").get("implementation"))
    x.write() # to change it on the actual file
