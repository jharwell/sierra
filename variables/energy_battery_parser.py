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


class EnergyBatteryParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    <EEE type><activated><labella><liu>

    - EEE_type = {Null, Ill, Well}
    - activated = {atrue, afalse}
    - labella = {ltrue, lfalse}
    - wliu = {wtrue, wfalse}

    For example:

    Null -> Energy Battery Allocation used but stops when enters EEE
    Ill -> Energy Battery Allocation used but keeps adapting when enters EEE
    Well -> Energy Battery Allocation used but delays more when enters EEE
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.increment_type_parse(criteria_str))
        return ret

    def increment_type_parse(self, criteria_str):
        """

        """
        ret = {}

        for s in ["Null", "Ill", "Well"]:
            index = criteria_str.find(s)
            if index != -1:
                ret["EEE_method"] = criteria_str[index:len(s)]

        for s in ["atrue", "afalse"]:
            index = criteria_str.find(s)
            if index != -1:
                ret["activate"] = criteria_str[index:len(s)]

        for s in ["ltrue", "lfalse"]:
            index = criteria_str.find(s)
            if index != -1:
                ret["lab"] = criteria_str[index:len(s)]

        for s in ["wtrue", "wfalse"]:
            index = criteria_str.find(s)
            if index != -1:
                ret["wliu"] = criteria_str[index:len(s)]

        return ret
