"""
 Copyright 2018 John Harwell, All rights reserved.

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

from variables.base_variable import BaseVariable
from variables.message_frequency_parser import MessageFrequencyParser


class MessageFrequency(BaseVariable):

    """
    Defines a probability for sending/receiving messages

    Attributes:
      message_prob(list): List (X,Y) probabilities, where X is for sending, and
                        Y is for recieving.
    """

    def __init__(self, message_prob):
        self.message_prob = message_prob

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation for the specified communication paramaters.
        """
        return [set([(".//params/communication", "chance_to_send_communication", str(m[0])),
                     (".//params/communication", "chance_to_recieve_communication", str(m[1]))]) for m in self.message_prob]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []

def Factory(criteria_str):
    """
    Creates swarm size classes from the command line definition of batch criteria.
    """
    attr = MessageFrequencyParser().parse(criteria_str.split(".")[1])

    def gen_variances(criteria_str):
        x_start = 0
        x_end = 0
        y_start = 0
        y_end = 0

        if "sLow" == attr["sending_type"]:
            x_start = 20
            x_end = 45
        elif "sMid" == attr["sending_type"]:
            x_start = 50
            x_end = 75
        elif "sHigh" == attr["sending_type"]:
            x_start = 80
            x_end = 105

        if "rLow" == attr["receiving_type"]:
            y_start = 20
            y_end = 45
        elif "rMid" == attr["receiving_type"]:
            y_start = 50
            y_end = 75
        elif "rHigh" == attr["receiving_type"]:
            y_start = 80
            y_end = 105
        lst = []
        for x in range(x_start, x_end, 5):
            for y in range(y_start, y_end, 5):
                lst.append((x*0.01,y*0.01))
        return lst


    def __init__(self):
        MessageFrequency.__init__(self, gen_variances(criteria_str))

    return type(criteria_str,
                (MessageFrequency,),
                {"__init__": __init__})
