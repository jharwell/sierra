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
import generators.stateless
import generators.stateful
import generators.single_source
import generators.powerlaw
import generators.random


def GeneratorFactory(generator_pair, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        self.controller_changes = eval(generator_pair[0])(*args, **kwargs)
        if 2 == len(generator_pair):
            self.scenario_changes = eval(generator_pair[1])(*args, **kwargs)

    def generate(self):
        if 2 == len(generator_pair):
            self.scenario_changes.generate(self.controller_changes.generate())
        else:
            self.controller_changes.generate_and_save()

    print("Created joint generator class '{0}'".format('+'.join(generator_pair)))
    return type('+'.join(generator_pair), (object,), {"__init__": __init__,
                                                      "generate": generate
                                                      })(*args, **kwargs)
