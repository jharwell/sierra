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
Definition:
    {variance_type}{waveform_type}[step_time][.Z{swarm_size}]

    variance_type = {BC,BM,CU}
    waveform_type = {Sine,Square,Sawtooth,Step{U,D},Constant}
    step_time = Timestep the step function should switch (optional)
    swarm_size = The swarm size to use (optional)

Examples:
    - ``BCSine.Z16``: Block carry sinusoidal variance in a swarm of size 16.
    - ``BCStep50000.Z32``: Block carry step variance at 50000 timesteps in a swarm of size 32.
    - ``BCStep50000``: Block carry step variance at 50000 timesteps; swarm size not modified.
"""

from variables.batch_criteria import UnivarBatchCriteria
from variables.swarm_size import SwarmSize
import math
import re
import typing as tp
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


class TemporalVariance(UnivarBatchCriteria):
    """
    A univariate range specifiying the set of temporal variances (and possibly swarm size) to
    use to define the batched experiment. This class is a base class which should (almost) never be
    used on its own. Instead, the ``Factory()`` function should be used to dynamically create
    derived classes expressing the user's desired variance set.

    Attributes:
        variances: List of tuples specifying the waveform characteristics for each type of
                   applied variance. Each tuple is (xml parent path, [type, frequency, amplitude,
                   offset, phase], value).
    """

    def __init__(self, cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 variances: list,
                 swarm_size: int):
        UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)

        self.variances = variances
        self.swarm_size = swarm_size

    def gen_attr_changelist(self) -> list:
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified temporal variances.
        """
        # Swarm size is optional. It can be (1) controlled via this variable, (2) controlled by
        # another variable in a bivariate batch criteria, (3) not controlled at all. For (2), (3),
        # the swarm size can be None.

        if self.swarm_size is not None:
            size_attr = next(iter(SwarmSize(self.cli_arg,
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
        else:
            return [set([
                ("{0}/waveform".format(v[0]), "type", str(v[1])),
                ("{0}/waveform".format(v[0]), "frequency", str(v[2])),
                ("{0}/waveform".format(v[0]), "amplitude", str(v[3])),
                ("{0}/waveform".format(v[0]), "offset", str(v[4])),
                ("{0}/waveform".format(v[0]), "phase", str(v[5]))]) for v in self.variances]

    def sc_graph_labels(self, scenarios: tp.List[str]) -> tp.List[str]:
        return scenarios

    def sc_sort_scenarios(self, scenarios: tp.List[str]) -> tp.List[str]:
        return scenarios  # No sorting needed

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: tp.List[str] = None) -> tp.List[float]:
        # If exp_dirs is passed, then we have been handed a subset of the total # of directories in
        # the batch exp root, and so n_exp() will return more experiments than we actually
        # have. This behavior is needed to correct extract x/y values for bivar experiments.
        if exp_dirs is not None:
            m = len(exp_dirs)
        else:
            m = self.n_exp()

        # zeroth element is the distance to ideal conditions for exp0, which is by definition ideal
        # conditions, so the distance is 0.
        ret = [0]
        ret.extend([vcs.EnvironmentalCS(cmdopts, x)(self, exp_dirs) for x in range(1, m)])
        return ret

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: tp.List[str] = None) -> tp.List[float]:
        return self.graph_xticks(cmdopts, exp_dirs)

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return vcs.method_xlabel(cmdopts["envc_cs_method"])

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> tp.List[str]:
        return ['exp' + str(x) for x in range(0, len(self.gen_attr_changelist()))]

    def pm_query(self, query: str) -> bool:
        return query in ['blocks-collected', 'reactivity', 'adaptability']


class TemporalVarianceParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def parse(self, criteria_str):
        """
        Returns:
            Dictionary with keys:
                variance_type: BC|BM|BU
                xml_parent_path: Parent XPath within template input file
                variance_csv_col: Column within configured .csv containing the variance
                waveform_type: Sine|Square|Sawtooth|StepU|StepD|Constant
                waveform_param: Waveform specific parameter(s) (optional)
                swarm_size: Swarm size to use (optional)

        """
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
        res = re.search("Sine|Square|Sawtooth|Step[UD]|Constant", criteria_str)
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


def Factory(cli_arg, main_config, batch_generation_root, **kwargs):
    """
    Factory to create ``TemporalVariance`` derived classes from the command line definition of batch
    criteria.

    """
    attr = TemporalVarianceParser().parse(cli_arg)

    def gen_variances(cli_arg):

        if "BC" in cli_arg:
            amps = kBCAmps
        elif "BM" in cli_arg:
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
        TemporalVariance.__init__(self, cli_arg, main_config, batch_generation_root,
                                  gen_variances(cli_arg), attr.get("swarm_size", None))

    return type(cli_arg,
                (TemporalVariance,),
                {"__init__": __init__})
