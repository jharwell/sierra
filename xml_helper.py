'''
By: London Lowmanstone

Terminology/Definitions:
    element path: something in the form "tag.tag.(...).tag.tag" that specifies an element in the tree

    element path list: same thing as an element path except for it's in the form [tag, tag, ..., tag, tag]

    attribute path: same thing as an element path except for it ends with an attribute. In the form "tag.tag.(...).tag.attribute"

    attribute path list: (see "element path list" and "attribute path" for the corresponding definitions)

    strict path: a path that begins with the root tag and each subsequent tag is a child of the previous tag.
        Specifies exactly one element (or attribute; the attribute must be an attribute of the most recent tag).

    loose path: a path where all of the subsequent tags are children of the previous tags, but generations may be skipped.
        For example, the bath "b.d.g" may refer to an element with the specific path "a.b.c.d.e.f.g"

    loose-strict path: a path where the first tag in the path is found via a loose search, and the following tags are expected to be direct children.
        In other words, this is basically a strict path that doesn't start with the root tag.

    strict search: a search for an element using a strict path.

    loose search: (see "strict search" for the corresponding definition)

    loose-strict search: (see "strict search" for the corresponding definition)
'''

import xml.etree.ElementTree as ET


class InvalidElementError(RuntimeError):
    '''Error class for when an element cannot be found or used'''
    pass


class XMLHelper:
    def __init__(self, input_filepath, output_filepath=None):
        '''
        A class to help edit and save xml files
        parameters:
            input_filepath: the location of the xml file to process
            output_filepath (optional): where the object should save changes it has made to the xml file
                (defaults to overwriting the input file)
        '''
        if output_filepath is None:
            output_filepath = input_filepath

        self.input_filepath = input_filepath
        self.output_filepath = output_filepath

        self.tree = ET.parse(input_filepath)
        # restriction: assumes the root of the xml file is not going to change
        self.root = self.tree.getroot()


    def write(self, filepath=None):
        '''Write the XML stored in the object to an output filepath'''
        if filepath is None:
            filepath = self.output_filepath

        self.tree.write(filepath)


    def get_element(self, s):
        '''Alias for get_element_with_path_attribute'''
        return self.get_element_with_path_attribute(s)


    def set_element(self, s):
        '''Alias for set_path_attribute'''
        return self.set_path_attribute(s)


    def get_element_with_path_attribute(self, s):
        '''
        Takes a loose path to an attribute.
        Returns an element with the matching attribute.
        (Returns None if such an element cannot be found.)
        '''
        # the last string in this list will be the attribute
        tag_list = s.split(".")

        if len(tag_list) > 1 and tag_list[0] == self.root.tag:
            # having the root as the first tag will cause self._get_element_with_path_attribute to search inside root for itself, so catch that case here.
            tag_list = tag_list[1:]

        return self._get_element_with_path_attribute(tag_list, starting_element=self.root)


    def set_path_attribute(self, s, value):
        '''
        Takes a loose path to an attribute and sets that attribute to the given value
        Raises an InvalidElementError if a matching element with the attribute cannot be found.
        Converts the value to a string before setting the attribute.
        '''
        element = self.get_element_with_path_attribute(s)
        if element is not None:
            value = str(value)
            element.set(s.split(".")[-1], value)
        else:
            raise InvalidElementError("An element matching the path attribute '{}' could not be found".format(s))


    def _get_element_with_path_attribute(self, tags, starting_element):
        '''
        Recursive function to accomplish the corresponding "public" function (the function of the same name that does not begin with an underscore)
        Takes an attribute path list.
        Returns an element with the matching attribute.
        (Returns None if such an element cannot be found.)
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
    x = XMLHelper("Sample XML Files/single-source-test.argos")
    # ans = x.get_element_with_path_attribute("footbot_light.implementation")
    # print(ans.get("implementation"))
    x.set_path_attribute("differential_steering.implementation", "hello world")
    print("did it")
    # print(x.get_element("actuators.implementation").get("implementation"))
    x.remove_element()
    # x.write() # to change it on the actual file
