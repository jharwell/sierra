# Copyright 2020 John Harwell, All rights reserved.
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


class DynamicsParser():
    """
    Base class for some dynamics parsers to reduce code duplication.
    """

    def __init__(self) -> None:
        pass

    def specs_dict(self) -> tp.Dict[str, tp.Any]:
        raise NotImplementedError

    def __call__(self,
                 criteria_str: str) -> dict:
        ret = {
            'dynamics': list(),
            'factor': float(),
            'dynamics_types': list()
        }
        specs_dict = self.specs_dict()

        # Parse cardinality
        res = re.search(r".C[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad cardinality for dynamics in criteria '{0}'".format(criteria_str)
        ret['cardinality'] = int(res.group(0)[2:])

        # Parse factor characteristic
        res = re.search(r'F[0-9]+p[0-9]+', criteria_str)
        assert res is not None, \
            "FATAL: Bad Factor specification in criteria '{0}'".format(criteria_str)
        characteristic = float(res.group(0)[1:].split('p')[0])
        mantissa = float("0." + res.group(0)[1:].split('p')[1])

        ret['factor'] = characteristic + mantissa

        # Parse dynamics parameters
        specs = criteria_str.split('.')[3:]
        dynamics = []
        dynamics_types = []

        for spec in specs:
            # Parse characteristic
            res = re.search('[0-9]+p', spec)
            assert res is not None, \
                "FATAL: Bad characteristic specification in criteria '{0}'".format(
                    criteria_str)
            characteristic = float(res.group(0)[0:-1])

            # Parser mantissa
            res = re.search('p[0-9]+', spec)
            assert res is not None, \
                "FATAL: Bad mantissa specification in criteria '{0}'".format(
                    criteria_str)
            mantissa = float("0." + res.group(0)[1:])

            for k in specs_dict.keys():
                if k in spec:
                    dynamics.append((specs_dict[k], characteristic + mantissa))
                    dynamics_types.append(k)

        ret['dynamics'] = dynamics
        ret['dynamics_types'] = dynamics_types

        return ret
