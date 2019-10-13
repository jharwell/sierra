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
#
import variables.batch_criteria as bc
from variables.arena_shape import RectangularArena
from variables.constant_density_parser import ConstantDensityParser
import os
import utils
from variables.block_distribution import TypeRandom, TypeSingleSource, TypeDualSource, TypeQuadSource
import generators.scenario_generator_parser as sgp


def Calculate(n_robots, arena_x, arena_y):
    """Calculate the swarm density \rho, from Hamann2013."""
    return n_robots / int(arena_x) * int(arena_y)


class ConstantDensity(bc.UnivarBatchCriteria):
    """
    Defines a range of swarm and arena sizes to test with such that the ratio of swarm size to arena
    size is always the. Does not change the # blocks/block manifest.

    Attributes:
      target_density(list): The target swarm density.
      dimensions(list): List of (X,Y) dimensions to use (creates rectangular arenas).
      dist_type(str): The type of block distribution to use.
      changes(list): List of sets of changes to apply to generate the specified arena sizes.
    """

    # How many experiments to run for the given density value, in which the arena size is increased
    # from its initial value according to parsed parameters.
    kExperimentsPerDensity = 10

    def __init__(self, cmdline_str, main_config, batch_generation_root,
                 target_density, dimensions, dist_type):
        bc.UnivarBatchCriteria.__init__(self, cmdline_str, main_config, batch_generation_root)
        self.target_density = target_density
        self.dimensions = dimensions
        self.dist_type = dist_type
        self.changes = RectangularArena(dimensions).gen_attr_changelist()

        dist_types = {
            'SS': 'TypeSingleSource',
            'DS': 'TypeDualSource',
            'QS': 'TypeQuadSource',
            'RN': 'TypeRandom'
        }

        for changeset in self.changes:
            for c in eval(dist_types[self.dist_type])().gen_attr_changelist():
                changeset = changeset | c

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes to input file to set the # robots for a set of arena
        sizes such that the swarm density is constant. Robots are approximated as point masses.
        """
        for changeset in self.changes:
            for c in changeset:
                if c[0] == ".//arena" and c[1] == "size":
                    x, y, z = c[2].split(',')
                    # ARGoS won't start if there are 0 robots, so you always need to put at least
                    # 1.
                    n_robots = max(1, (int(x) * int(y)) * (self.target_density / 100.0))
                    changeset.add((".//arena/distribute/entity", "quantity", str(int(n_robots))))
                    break
        return self.changes

    def gen_exp_dirnames(self, cmdopts):
        changes = self.gen_attr_changelist()
        density = self.def_str.split('.')[1]
        dirs = []
        for chg in changes:
            d = ''
            for path, attr, value in chg:
                if 'quantity' in attr:
                    d += density + '+size' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs']:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def sc_graph_labels(self, scenarios):
        return [s[-5:-2].replace('p', '.') for s in scenarios]

    def sc_sort_scenarios(self, scenarios):
        return sorted(scenarios,
                      key=lambda s: float(s.split('-')[2].split('.')[0][0:3].replace('p', '.')))

    def graph_xvals(self, cmdopts):
        densities = []
        for i in range(0, self.n_exp()):
            pickle_fpath = os.path.join(self.batch_generation_root,
                                        self.gen_exp_dirnames(i),
                                        "exp_def.pkl")
            exp_def = utils.unpickle_exp_def(pickle_fpath)
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    n_robots = int(e[2])
                if e[0] == ".//arena" and e[1] == "size":
                    x, y, z = e[2].split(",")
            densities.append(n_robots / (int(x) * int(y)))
        return densities

    def graph_xlabel(self, cmdopts):
        return "Swarm Density"

    def pm_query(self, query):
        return query in ['blocks-collected', 'scalability', 'self-org']

    def exp_scenario_name(self, exp_num):
        """
        Given the exp number in the batch, compute a valid, parsable scenario name. It is necessary
        to query this criteria after generating the changelist in order to create generator classes
        for each experiment in the batch with the correct name and definition.

        Normally controller+scenario are used to look up all necessary changes for the specified
        arena size, but for this criteria the specified scenario is the base scenario (i.e. the
        starting arena dimensions), and the correct arena dimensions for a given exp must be found
        via lookup with THIS function).
        """
        dims = map(str, list(self.dimensions[exp_num]))
        return self.dist_type + '.' + 'x'.join(dims)


def Factory(cmdline_str, main_config, batch_generation_root, **kwargs):
    """
    Creates swarm density classes from the command line definition of batch criteria.
    """
    attr = ConstantDensityParser().parse(cmdline_str)
    kw = sgp.ScenarioGeneratorParser.reparse_str(kwargs['scenario'])

    if "SS" == kw['dist_type'] or "DS" == kw['dist_type']:
        dims = [(x, int(x / 2)) for x in range(kw['arena_x'],
                                               kw['arena_x'] +
                                               ConstantDensity.kExperimentsPerDensity *
                                               kw['arena_x'],
                                               attr['arena_size_inc'])]
    elif "QS" == kw['dist_type'] or "RN" == kw['dist_type']:
        dims = [(x, x) for x in range(kw['arena_x'],
                                      kw['arena_x'] + ConstantDensity.kExperimentsPerDensity *
                                      kw['arena_x'],
                                      attr['arena_size_inc'])]
    else:
        raise NotImplementedError(
            "Unsupported block dstribution for constant density experiments: Only SS,DS,QS,RN supported")

    def __init__(self):
        ConstantDensity.__init__(self,
                                 cmdline_str,
                                 main_config,
                                 batch_generation_root,
                                 attr["target_density"],
                                 dims,
                                 kw['dist_type'])

    return type(cmdline_str,
                (ConstantDensity,),
                {"__init__": __init__})
