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


class MessageFrequencyParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    <send type><receive type>

    - send_type = {sLow, sMid, sHigh}
    - receive_type = {rLow, rMid, rHigh}

    For example:

    sLowrHigh -> low sending rate, but high receiving rate
    sHighrMid -> high sending rate, but medium receiving rate
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.increment_type_parse(criteria_str))
        return ret

    def increment_type_parse(self, criteria_str):
        """
        Parse the sending and receiving types. Valid types are

        _Low, _Mid, _High - Which respectively define how each (sending and
                         receiving) will probabilistically guage whether to
                         perform its action. NOTE: _ is replaced with s and r
                         for sending and receiving respectively.
        """
        ret = {}

        for s in ["sLow", "sMid", "sHigh"]:
            index = criteria_str.find(s)
            if -1 != index:
                ret["sending_type"] = criteria_str[0:len(s)]
                send_length = len(ret["sending_type"])

        ret["receiving_type"] = criteria_str[send_length:len(criteria_str)]

        return ret
