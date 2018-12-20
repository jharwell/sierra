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


class TemporalVarianceParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    <variance_type><waveform_type>[step time]Z<swarm_size>

    variance_type = {BC,BM,CU}
    waveform_type = {Sine,Square,Sawtooth,Step{U,D},Constant}

    For example:

    BCSineZ16 -> Block carry sinusoidal variance in a swarm of size 16.
    BCStep50000Z32 -> Block carry step variance at 50000 timesteps in a swarm of size 32.
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.variance_type_parse(criteria_str))
        ret.update(self.waveform_parse(criteria_str))
        ret.update(self.swarm_size_parse(criteria_str))
        return ret

    def variance_type_parse(self, criteria_str):
        """
        Parse the temporal variance type out of the batch criteria string. Valid values are:

        BC - Block carry
        BM - Block manipulation
        CU - Cache Usage (static only for now)
        """
        ret = {}
        t = criteria_str[:2]
        ret["variance_type"] = t

        if "BC" == t:
            ret["xml_parent_path"] = ".//actuation/block_carry_throttle"
            ret["variance_csv_col"] = "swarm_motion_throttle"
        elif "BM" == t:
            ret["xml_parent_path"] = ".//arena_map/blocks/manipulation_penalty"
            ret["variance_csv_col"] = "env_block_manip"
        elif "CU" == t:
            ret["xml_parent_path"] = ".//arena_map/caches/static/usage_penalty"
            ret["variance_csv_col"] = "env_cache_usage"
        return ret

    def waveform_parse(self, criteria_str):
        """
        Parse the waveform type and possible associated param from the batch criteria string. Valid
        waveform types are:

        - Sine
        - Square
        - Constant
        - Sawtooth
        - Step{U,D}<TStep>

        Immediately proceeding 'Step' is the timestep on which the variance should suddenly change.
        """
        ret = {}
        ret["waveform_type"] = None
        ret["waveform_param"] = None

        for c in ["Sine", "Square", "Constant", "Sawtooth"]:
            index = criteria_str.find(c)
            if -1 != index:
                ret["waveform_type"] = c[index:len(c)]

        # Must be 'StepX'
        if ret["waveform_type"] is None:
            if -1 != criteria_str.find("StepU"):
                ret["waveform_type"] = "StepU"
                t_start = criteria_str.find("StepU") + len("StepU")
            else:
                ret["waveform_type"] = "StepD"
                t_start = criteria_str.find("StepD") + len("StepD")

            t_i = t_start + 1
            while criteria_str[t_i].isdigit():
                t_i += 1

            ret["waveform_param"] = int(criteria_str[t_start:t_i])
        return ret

    def swarm_size_parse(self, criteria_str):
        """
        Parse the swarm size from the batch criteria string. Valid values are positive integers.
        """
        ret = {}
        start = criteria_str.find("Z") + 1
        ret["swarm_size"] = int(criteria_str[start:])
        return ret
