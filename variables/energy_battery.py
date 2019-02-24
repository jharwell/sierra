"""
 Copyright 2019 Anthony Chen, All rights reserved.

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
from variables.energy_battery_parser import EnergyBatteryParser

class EnergyBattery(BaseVariable):

    """
    Defines a

    Attributes:
        energy_method(list): List of tuples specifying the energy efficiency method
        characteristics for the robot/energy_subsystem. Each tuple is
        (EEE_method, activated, labella, liu).

    """

    def __init__(self, energy_method):
        self.energy_method = energy_method

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation for the specified communication paramaters.
        """

        return [set([(".//params/energy", "EEE", str(e[0])),
                     (".//params/energy", "activated", str(e[1])),
                     (".//params/energy", "labella", str(e[2])),
                     (".//params/energy", "liu", str(e[3]))]) for e in self.energy_method]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []

def Factory(criteria_str):
    """
    Creates swarm size classes from the command line definition of batch criteria.
    """
    attr = EnergyBatteryParser().parse(criteria_str.split(".")[1])

    def gen_variances(criteria_str):

        lst = []

        if attr["activate"] == "afalse":
            lst.append(("Null-informed","false","false","false"))
        elif attr["activate"] == "atrue":
            lab = attr["lab"][1:len(attr["lab"])]
            wliu = attr["wliu"][1:len(attr["wliu"])]
            if attr["EEE_method"] == "Null":
                lst.append(("Null-informed","true",lab,wliu))
            elif attr["EEE_method"] == "Ill":
                lst.append(("Ill-informed","true",lab,wliu))
            elif attr["EEE_method"] == "Well":
                lst.append(("Well-informed","true",lab,wliu))

        return lst


    def __init__(self):
        EnergyBattery.__init__(self, gen_variances(criteria_str))

    return type(criteria_str,
                (MessageFrequency,),
                {"__init__": __init__})
