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
import typing as tp


class FlexibilityParser():
    """
    Enforces the cmdline definition of the :class:`Flexibility` batch criteria.

    This is its own file due to an otherwise circular import dependence between it and vcs.

    """

    def __call__(self, criteria_str: str) -> tp.Dict[str, str]:
        """
        Returns:
            Dictionary with the following keys:
                - variance_type: BC|BM
                - xml_parent_path: Parent XPath within template input file
                - variance_csv_col: Column within configured .csv containing the variance
                - waveform_type: Sine|Square|Sawtooth|StepU|StepD|Constant
                - waveform_param: Waveform specific parameter(s) (optional)
                - swarm_size: Swarm size to use (optional)

        """
        ret = {}
        xml_parent = {
            'BC': './/temporal_variance/blocks/carry_throttle',
            'BM': './/temporal_variance/blocks/manipulation_penalty',
        }
        variance_col = {
            'BC': "swarm_motion_throttle",
            'BM': "env_block_manip",
        }
        # Parse variance type
        res = re.search("BC|BM", criteria_str)
        assert res is not None, "FATAL: Bad variance type in criteria '{0}'".format(criteria_str)
        ret['variance_type'] = res.group(0)
        ret['xml_parent_path'] = xml_parent[ret['variance_type']]
        ret['variance_csv_col'] = variance_col[ret['variance_type']]

        # Parse waveform type
        res = re.search("Sine|Square|Sawtooth|Step[UD]|Constant", criteria_str)
        assert res is not None, "FATAL: Bad waveform type in criteria '{0}'".format(criteria_str)
        ret['waveform_type'] = res.group(0)

        if 'Step' in ret['waveform_type']:
            res = re.search("Step[UD][0-9]+", criteria_str)
            assert res is not None, "FATAL: Bad step specification type in criteria '{0}'".format(
                criteria_str)
            ret['waveform_param'] = int(res.group(0)[5:])

        # Parse swarm size (optional)
        res = re.search(r"\.Z[0-9]+", criteria_str)
        if res is not None:
            ret['swarm_size'] = int(res.group(0)[2:])

        return ret
