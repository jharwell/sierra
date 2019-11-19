# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/


import re


class TemporalVarianceParser():
    """
    Parses the command line definition of batch criteria. The string must be formatted as:

    {variance_type}{<waveform_type}[step time][.Z{swarm_size}]

    variance_type = {BC,BM,CU}
    waveform_type = {Sine,Square,Sawtooth,Step{U,D},Constant}

    For example:

    BCSine.Z16 -> Block carry sinusoidal variance in a swarm of size 16.
    BCStep50000.Z32 -> Block carry step variance at 50000 timesteps in a swarm of size 32.
    BCStep50000 -> Block carry step variance at 50000 timesteps; swarm size not modified.
    """

    def parse(self, criteria_str):
        ret = {}
        xml_parent = {
            'BC': './/temporal_variance/blocks/carry_throttle',
            'BM': './/temporal_variance/blocks/manipulation_penalty',
            'CU': './/temporal_variance/caches/usage_penalty'
        }
        variance_col = {
            'BC': "swarm_motion_throttle",
            'BM': "env_block_manip",
            'CU': "env_cache_usage"
        }
        # Parse variance type
        res = re.search("BC|BM|BU", criteria_str)
        assert res is not None, "FATAL: Bad variance type in criteria '{0}'".format(criteria_str)
        ret['variance_type'] = res.group(0)
        ret['xml_parent_path'] = xml_parent[ret['variance_type']]
        ret['variance_csv_col'] = variance_col[ret['variance_type']]

        # Parse waveform type
        res = re.search("Sine|Suare|Sawtooth|Step[UD]|Constant", criteria_str)
        assert res is not None, "FATAL: Bad waveform type in criteria '{0}'".format(criteria_str)
        ret['waveform_type'] = res.group(0)

        if 'Step' in ret['waveform_type']:
            res = re.search("Step[UD][0-9]+", criteria_str)
            assert res is not None, "FATAL: Bad step specification type in criteria '{0}'".format(
                criteria_str)
            ret['waveform_param'] = int(res.group(0)[5:])

        # Parse swarm size (optional)
        res = re.search(r".Z[0-9]+", criteria_str)
        if res is not None:
            ret['swarm_size'] = int(res.group(0)[2:])

        return ret
