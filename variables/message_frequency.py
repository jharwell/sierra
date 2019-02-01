"""
 Copyright 2018 Nathan White, All rights reserved.

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
        return [set([(".//params/communication", "prob_send", str(m[0])),
                     (".//params/communication", "prob_receive", str(m[1]))]) for m in self.message_prob]

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
        x = 0
        prob_receive = 0

        if "rLow" == attr["receiving_type"]:
            prob_receive = .30
        elif "rMid" == attr["receiving_type"]:
            prob_receive = .60
        elif "rHigh" == attr["receiving_type"]:
            prob_receive = .90
        elif "all" == attr["receiving_type"]:
            prob_receive = -1

        lst = []
        if prob_receive != -1:
            lst = [(0.6,prob_receive)]
        else:
            for y in range(30,100, 30):
                #for y in range(30, 100, 30):
                    #lst.append((x*0.01, y*0.01))
                # 0.6 is selected for prob_send
                lst.append((0.6, y*0.01))
        return lst


    def __init__(self):
        MessageFrequency.__init__(self, gen_variances(criteria_str))

    return type(criteria_str,
                (MessageFrequency,),
                {"__init__": __init__})
