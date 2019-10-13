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
"""
Definition:
    {density}.I{Arena Size Increment}

    density              = <integer>p<integer> (i.e. 5p0 for 5.0)
    Arena Size Increment = Size in meters that the X and Y dimensions should increase by in between
                           experiments. Larger values here will result in larger arenas and more
                           robots being simulated at a given density. Must be an integer.

Examples:
    ``1p0.I16``: Constant density of 1.0. Arena dimensions will increase by 16 in both X and Y for
    each experiment in the batch.
"""

import re
import typing as tp
import variables.batch_criteria as bc
from variables.arena_shape import RectangularArena
import os
import utils
from variables.block_distribution import TypeRandom, TypeSingleSource, TypeDualSource, TypeQuadSource
import generators.scenario_generator_parser as sgp


class ConstantDensity(bc.UnivarBatchCriteria):
    """
    A univariate range specifiying the swarm density (ratio of swarm size to arena size) to hold
    constant as swarm and arena size are increased. This class is a base class which should (almost)
    never be used on its own. Instead, the ``Factory()`` function should be used to dynamically
    create derived classes expressing the user's desired density.

    Does not change the # blocks/block manifest.

    Attributes:
      target_density: The target swarm density.
      dimensions: List of (X,Y) dimensions to use (creates rectangular arenas).
      dist_type: The type of block distribution to use.
      changes: List of sets of changes to apply to generate the specified arena sizes.
    """

    # How many experiments to run for the given density value, in which the arena size is increased
    # from its initial value according to parsed parameters.
    kExperimentsPerDensity = 10

    def __init__(self, cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 target_density: float,
                 dimensions: tp.List[tuple],
                 dist_type: str):
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
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

    def gen_attr_changelist(self) -> list:
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

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> tp.List[str]:
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

    def sc_graph_labels(self, scenarios: tp.List[str]) -> tp.List[str]:
        return [s[-5:-2].replace('p', '.') for s in scenarios]

    def sc_sort_scenarios(self, scenarios: tp.List[str]) -> tp.List[str]:
        return sorted(scenarios,
                      key=lambda s: float(s.split('-')[2].split('.')[0][0:3].replace('p', '.')))

    def graph_xvals(self, cmdopts: tp.Dict[str, str]) -> tp.List[float]:
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

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Swarm Density"

    def pm_query(self, query) -> bool:
        return query in ['blocks-collected', 'scalability', 'self-org']

    def exp_scenario_name(self, exp_num: int) -> str:
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


class ConstantDensityParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def parse(self, cli_arg) -> dict:
        """
        Returns:
            Dictionary with keys:
                target_density: Floating point value of parsed target density
                arena_size_inc: Integer increment for arena size

        """
        ret = {}
        # Need to have 1 dot/2 parts
        assert 3 == len(cli_arg.split('.')),\
            "Bad criteria formatting in criteria '{0}': must have 2 sections, separated by '.'".format(
                cli_arg)

        # Parse density
        density = cli_arg.split('.')[1]
        res = re.search('[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density characteristic specification in criteria '{0}'".format(cli_arg)

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density mantissa specification in criteria '{0}'".format(cli_arg)
        mantissa = float("0." + res.group(0)[1:])

        ret['target_density'] = characteristic + mantissa

        # Parse arena size increment
        increment = cli_arg.split('.')[2]
        res = re.search('I[0-9]+', increment)
        assert res is not None, \
            "FATAL: Bad arena increment specification in criteria '{0}'".format(cli_arg)

        ret['arena_size_inc'] = int(res.group(0)[1:])

        return ret


def Factory(cli_arg: str, main_config:
            tp.Dict[str, str],
            batch_generation_root: str,
            **kwargs):
    """
    Factory to create ``ConstantDensity`` derived classes from the command line definition of batch
    criteria.

    """
    attr = ConstantDensityParser().parse(cli_arg)
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
                                 cli_arg,
                                 main_config,
                                 batch_generation_root,
                                 attr["target_density"],
                                 dims,
                                 kw['dist_type'])

    return type(cli_arg,
                (ConstantDensity,),
                {"__init__": __init__})
