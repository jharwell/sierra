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
"""
Parser for the :class:`TemporalVariance` batch criteria. This is its own file due to an otherwise
circular import dependence between it and vcs.
"""

import re


class TemporalVarianceParser():
    """
    Enforces the cmdline definition of the :class:`TemporalVariance` batch criteria.

    """

    def __call__(self, criteria_str: str) -> dict:
        """
        Returns:
            Dictionary with the following keys:
                - variance_type: BC|BM|M
                - xml_parent_path: Parent XPath within template input file
                - variance_csv_col: Column within configured .csv containing the variance
                - waveform_type: Sine|Square|Sawtooth|StepU|StepD|Constant
                - waveform_param: Waveform specific parameter(s) (optional)
                - population: Swarm size to use (optional)

        """
        ret = {
            'variance_type': "",
            'xml_parent_path': "",
            'variance_csv_col': "",
            'waveform_type': "",
            'waveform_param': "",
            'population': 0
        }
        xml_parent = {
            'M': './/env_dynamics/motion_throttle',
            'BC': './/env_dynamics/blocks/carry_throttle',
            'BM': './/env_dynamics/blocks/manipulation_penalty',
        }
        variance_col = {
            # I do not currently distinguish between different types of swarm motion throttle,
            # though that may be added in the future.
            'BC': "swarm_motion_throttle",
            'M': "swarm_motion_throttle",
            'BM': "env_block_manip",

        }
        # Parse variance type
        res = re.search("BC|BM|M", criteria_str)
        assert res is not None, "FATAL: Bad variance type in criteria '{0}'".format(criteria_str)
        variance_type = str(res.group(0))
        ret['variance_type'] = variance_type
        ret['xml_parent_path'] = xml_parent[variance_type]
        ret['variance_csv_col'] = variance_col[variance_type]

        # Parse waveform type
        res = re.search("Sine|Square|Sawtooth|Step[UD]|Constant", criteria_str)
        assert res is not None, "FATAL: Bad waveform type in criteria '{0}'".format(criteria_str)
        waveform_type = str(res.group(0))

        if 'Step' in waveform_type:
            res = re.search("Step[UD][0-9]+", criteria_str)
            assert res is not None, \
                "FATAL: Bad step specification type in criteria '{0}'".format(
                    criteria_str)
            ret['waveform_param'] = int(res.group(0)[5:])
        ret['waveform_type'] = waveform_type

        # Parse swarm size (optional)
        res = re.search(r"\.Z[0-9]+", criteria_str)
        if res is not None:
            ret['population'] = int(res.group(0)[2:])

        return ret
