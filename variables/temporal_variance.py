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
from variables.swarm_size import SwarmSize
from variables.temporal_variance_parser import TemporalVarianceParser
import math

kMinHz = 10
kMaxHz = 1000
kMinAmp = 100
kMaxAmp = 1000

kHZ = [x for x in range(kMinHz, kMaxHz + 100, 100)]
kAMPS = [x for x in range(kMinAmp, kMaxAmp + 100, 100)]


class TemporalVariance(BaseVariable):

    """
    Defines the type(s) of temporal variance to apply during simulation.

    Attributes:
      variances(list): List of tuples specifying the waveform characteristics for each type of
      applied variance. Each tuple is (xml parent path, [type, frequency, amplitude, offset, phase],
      value).
    """

    def __init__(self, variances, swarm_size):
        self.variances = variances
        self.swarm_size = swarm_size

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified block priorities.
        """
        size_attr = next(iter(SwarmSize([self.swarm_size]).gen_attr_changelist()[0]))
        return [set([
            size_attr,
            ("{0}/waveform".format(v[0]), "type", str(v[1])),
            ("{0}/waveform".format(v[0]), "frequency", str(v[2])),
            ("{0}/waveform".format(v[0]), "amplitude", str(v[3])),
            ("{0}/waveform".format(v[0]), "offset", str(v[4])),
            ("{0}/waveform".format(v[0]), "phase", str(v[5]))]) for v in self.variances]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


def Factory(criteria_str):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = TemporalVarianceParser().parse(criteria_str.split(".")[1])

    def gen_variances(criteria_str):

        if any(v == attr["waveform_type"] for v in ["Sine, Square, Sawtooth"]):
            return [(attr["xml_parent_path"],
                     attr["waveform_type"],
                     1.0 / hz,
                     amp,
                     amp,
                     0) for hz in kHZ for amp in kAMPS]
        elif "StepD" == attr["waveform_type"]:
            return [(attr["xml_parent_path"],
                     "Square",
                     1 / (2 * attr["waveform_param"]),
                     amp,
                     amp,
                     0) for amp in kAMPS]
        if "StepU" == attr["waveform_type"]:
            return [(attr["xml_parent_path"],
                     "Square",
                     1 / (2 * attr["waveform_param"]),
                     amp,
                     amp,
                     math.pi) for amp in kAMPS]

    def __init__(self):
        TemporalVariance.__init__(self, gen_variances(criteria_str), attr["swarm_size"])

    return type(criteria_str,
                (TemporalVariance,),
                {"__init__": __init__})
