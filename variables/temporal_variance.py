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
      applied variance. Each tuple is (xml_path, type, frequency, amplitude).
    """

    def __init__(self, variances):
        self.variances = variances

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified block priorities.
        """
        return [set([
            ("{0}/waveform", "type".format(v[0]), v[1]),
            ("{0}/waveform", "frequency".format(v[0]), v[2]),
            ("{0}/waveform", "amplitude".format(v[0]), v[3]),
            ("{0}/waveform", "offset".format(v[0]), v[3])]) for v in self.variances]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


class BlockCarrySine(TemporalVariance):
    def __init__(self):
        super().__init__([(".//actuation/block_carry_throttle",
                           "Sine",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockCarrySquare(TemporalVariance):
    def __init__(self):
        super().__init__([(".//actuation/block_carry_throttle",
                           "Square",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockCarrySawtooth(TemporalVariance):
    def __init__(self):
        super().__init__([(".//actuation/block_carry_throttle",
                           "Sawtooth",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockCarryStep50000(TemporalVariance):
    def __init__(self):
        super().__init__([(".//actuation/block_carry_throttle",
                           "Square",
                           1.0 / 50000,
                           amp) for amp in kAMPS])


class BlockCarryConstant(TemporalVariance):
    def __init__(self):
        super().__init__([(".//actuation/block_carry_throttle",
                           "Constant",
                           0.0,
                           amp) for amp in kAMPS])


class BlockManipulationSine(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/blocks/manipulation_penalty",
                           "Sine",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockManipulationSquare(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/blocks/manipulation_penalty",
                           "Square",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockManipulationSawtooth(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/blocks/manipulation_penalty",
                           "Sawtooth",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class BlockManipulationStep50000(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/blocks/manipulation_penalty",
                           "Square",
                           1.0 / 50000,
                           amp) for amp in kAMPS])


class BlockManipulationConstant(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/blocks/manipulation_penalty",
                           "Constant",
                           0.0,
                           amp) for amp in kAMPS])


class CacheUsageSine(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/static_caches/usage_penalty",
                           "Sine",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class CacheUsageSquare(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/static_caches/usage_penalty",
                           "Square",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class CacheUsageSawtooth(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/static_caches/usage_penalty",
                           "Sawtooth",
                           1.0 / hz,
                           amp) for hz in kHZ for amp in kAMPS])


class CacheUsageStep50000(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/static_caches/usage_penalty",
                           "Square",
                           1.0 / 50000,
                           amp) for amp in kAMPS])


class CacheUsageConstant(TemporalVariance):
    def __init__(self):
        super().__init__([(".//arena_map/static_caches/usage_penalty",
                           "Constant",
                           0.0,
                           amp) for amp in kAMPS])
