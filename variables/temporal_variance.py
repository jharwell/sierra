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

from variables.batch_criteria import BatchCriteria
from variables.swarm_size import SwarmSize
from variables.temporal_variance_parser import TemporalVarianceParser
import math
from perf_measures import vcs

kMinHz = 1000
kHzDelta = 2000
kMaxHz = 4000

kMinBMAmp = 100
kBMAmpDelta = 100
kMaxBMAmp = 1000

# Max amplitudie is only 1/2 of the 0.9 desired maximum because all square waveforms also have an
# offset.
kMinBCAmp = 0.1
kBCAmpDelta = 0.1
kMaxBCAmp = 0.5

# kHZ = [x for x in range(kMinHz, kMaxHz + kHzDelta, kHzDelta)]
kHZ = [0, 8000, 16000, 32000]
# kBMAmps = [x for x in range(kMinBMAmp, kMaxBMAmp + kBMAmpDelta, kBMAmpDelta)]
kBMAmps = [10, 100, 200, 400, 800]
# kBCAmps = [kMinBCAmp + x * kBCAmpDelta for x in range(0, int(kMaxBCAmp / kMinBCAmp))]
kBCAmps = [0, 0.05, 0.1, 0.2, 0.4]


class TemporalVariance(BatchCriteria):

    """
    Defines the type(s) of temporal variance to apply during simulation.

    Attributes:
      variances(list): List of tuples specifying the waveform characteristics for each type of
      applied variance. Each tuple is (xml parent path, [type, frequency, amplitude, offset, phase],
      value).
    """

    def __init__(self, cmdline_str, main_config, batch_generation_root,
                 variances, swarm_size):
        BatchCriteria.__init__(self, cmdline_str, main_config, batch_generation_root)

        self.variances = variances
        self.swarm_size = swarm_size

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified temporal variances.
        """
        size_attr = next(iter(SwarmSize(self.cmdline_str,
                                        self.main_config,
                                        self.batch_generation_root,
                                        [self.swarm_size]).gen_attr_changelist()[0]))
        return [set([
            size_attr,
            ("{0}/waveform".format(v[0]), "type", str(v[1])),
            ("{0}/waveform".format(v[0]), "frequency", str(v[2])),
            ("{0}/waveform".format(v[0]), "amplitude", str(v[3])),
            ("{0}/waveform".format(v[0]), "offset", str(v[4])),
            ("{0}/waveform".format(v[0]), "phase", str(v[5]))]) for v in self.variances]

    def sc_graph_labels(self, scenarios):
        return scenarios

    def sc_sort_scenarios(self, scenarios):
        return scenarios  # No sorting needed

    def graph_xvals(self, cmdopts):
        return [vcs.EnvironmentalCS(cmdopts, x)(self) for x in range(0, self.n_exp())]

    def graph_xlabel(self, cmdopts):
        return vcs.method_xlabel(cmdopts["envc_cs_method"])

    def gen_exp_dirnames(self, cmdopts):
        return ['exp' + str(x) for x in range(0, len(self.gen_attr_changelist()))]


def Factory(cmdline_str, main_config, batch_generation_root):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = TemporalVarianceParser().parse(cmdline_str)

    def gen_variances(cmdline_str):

        if "BC" in cmdline_str:
            amps = kBCAmps
        elif "BM" in cmdline_str:
            amps = kBMAmps

        # All variances need to have baseline/ideal conditions for comparison, which is a small
        # constant penalty
        variances = [(attr["xml_parent_path"],
                      "Constant",
                      kHZ[0],
                      amps[0],
                      0,
                      0)]

        if any(v == attr["waveform_type"] for v in ["Sine", "Square", "Sawtooth"]):
            variances.extend([(attr["xml_parent_path"],
                               attr["waveform_type"],
                               1.0 / hz,
                               amp,
                               amp,
                               0) for hz in kHZ[1:] for amp in amps[1:]])
        elif "StepD" == attr["waveform_type"]:
            variances.extend([(attr["xml_parent_path"],
                               "Square",
                               1 / (2 * attr["waveform_param"]),
                               amp,
                               0,
                               0) for amp in amps[1:]])

        if "StepU" == attr["waveform_type"]:
            variances.extend([(attr["xml_parent_path"],
                               "Square",
                               1 / (2 * attr["waveform_param"]),
                               amp,
                               amp,
                               math.pi) for amp in amps[1:]])
        return variances

    def __init__(self):
        TemporalVariance.__init__(self, cmdline_str, main_config, batch_generation_root,
                                  gen_variances(cmdline_str), attr["swarm_size"])

    return type(cmdline_str,
                (TemporalVariance,),
                {"__init__": __init__})
