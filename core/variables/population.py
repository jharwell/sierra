# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
#
# SIERRA is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SIERRA.  If not, see <http://www.gnu.org/licenses/
"""
Definition:
    {Population dynamics}.{increment_type}{N}[.{dynamics_type}{prob}[...]]

    - Population dynamics - {static, dynamic}. If ``static``, then the swarm size does not change
      dynamic as the simulation progresses. If ``dynamic``, it can.

    - increment_type - {Log,Linear}. If ``Log``, then swarm sizes for each experiment are
      distributed 1...N by powers of 2. If ``Linear`` then swarm sizes for each experiment are
      distributed linearly between 1...N, split evenly into 10 different sizes.

    - N - The maximum swarm size.

    - dynamics_type - {B|D}. Only required if population dynamics was ``dynamic``.

      - ``B`` - Adds birth dynamics to the population. By itself, it specifies a pure birth process
                with lambda ``prob``, resulting in dynamic swarm sizes which will increase from
                1...N over time. Can be specified with ``D|M|R``.

      - ``D`` - Adds death dynamics to the population. By itself, it specifies a pure death process
                with lambda ``prob``, resulting in dynamic swarm sizes which will decrease from
                N...1 over time. Can be specified with ``B|M|R``

      - ``M|R`` - Adds malfunction/repair dynamics to the population. If specified, ``R`` dynamics
                  must also be specified, and vice versa. Together they specify the dynamics of the
                  swarm as robots temporarily fail, and removed from simulation, and then later are
                  re-introduced after they have been repaired. Can be specified with ``B|D``

Examples:
    - ``static.Log1024``: Static swarm sizes 1...1024

    - ``static.Linear1000``: Static swarm sizes 100...1000

    - ``dynamic.Log64.B0p001``: Dynamic swarm sizes with a pure birth process with a 0.001
      parameter.

    - ``dynamic.Log64.D0p001``: Dynamic swarm sizes with a pure head process with a 0.001 parameter

    - ``dynamic.Log64.B0p001.D0p005``: Dynamic swarm sizes with a birth-death process with a 0.001
        parameter for birth and a 0.005 parameter for death.

    - ``dynamic.Log64.M0p001.R0p005``: Dynamic swarm sizes with a malfunction-repair process with a
        0.001 parameter for malfunction and a 0.005 parameter for repair.
"""

import typing as tp
import re
import math

from core.variables import batch_criteria as bc


class Population(bc.UnivarBatchCriteria):
    """
    A univariate range of swarm sizes and population dynamics used to define batched
    experiments. This class is a base class which should (almost) never be used on its own. Instead,
    the ``factory()`` function should be used to dynamically create derived classes expressing the
    user's desired size distribution.

    Attributes:
        size_list: List of integer swarm sizes defining the range of the variable for the batched
                   experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 size_list: tp.List[str],
                 dynamics_type: str,
                 dynamics: tp.List[tp.Tuple[str, int]]):
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
        self.size_list = size_list
        self.dynamics_type = dynamics_type
        self.dynamics = dynamics

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes for swarm sizes and population dynamics.
        """
        if self.dynamics_type == 'static':
            return [set([(".//arena/distribute/entity", "quantity", str(s))]) for s in self.size_list]
        else:
            # If birth dynamics enabled, always start with swarm size of 1. Ideally would be 0, but
            # ARGoS won't start with 0 robots.
            if any(['birth_mu' in b[0] for b in self.dynamics]):
                changes = [set([(".//arena/distribute/entity", "quantity", str(1)),
                                (".//population_dynamics", "max_size", str(s))])
                           for s in self.size_list]
            else:  # Non birth dynamics
                changes = [set([(".//arena/distribute/entity", "quantity", str(s)),
                                (".//population_dynamics", "max_size", str(s))])
                           for s in self.size_list]

            dynamics = {(".//temporal_variance/population_dynamics",
                         d[0],
                         str('%3.9f' % d[1])) for d in self.dynamics}

            for c in changes:
                c |= dynamics
            return changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> list:
        changes = self.gen_attr_changelist()
        dirs = []
        for chg in changes:
            d = ''
            for _, attr, value in chg:
                if 'quantity' in attr:
                    d += 'size' + value
            dirs.append(d)
        if not cmdopts['named_exp_dirs']:
            return ['exp' + str(x) for x in range(0, len(dirs))]
        else:
            return dirs

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        ret = self.populations(cmdopts, exp_dirs)

        if cmdopts['plot_log_xaxis']:
            return [math.log2(x) for x in ret]
        else:
            return ret

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        return self.graph_xticks(cmdopts, exp_dirs)

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Swarm Size"

    def pm_query(self, pm: str) -> bool:
        return pm in ['blocks-collected', 'scalability', 'self-org']


class PopulationParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def __call__(self, criteria_str) -> dict:
        ret = {}

        # Parse population dynamics
        res = re.search("static|dynamic", criteria_str)
        assert res is not None, \
            "FATAL: Bad population dynamics specification in criteria '{0}'".format(criteria_str)
        ret['dynamics_type'] = res.group(0)

        # Parse increment type
        res = re.search("Log|Linear", criteria_str)
        assert res is not None, \
            "FATAL: Bad size increment specification in criteria '{0}'".format(criteria_str)
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad population max in criteria '{0}'".format(criteria_str)
        ret['max_size'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(ret['max_size'] / 10.0)

        # Parse birth/death process parameters
        if ret['dynamics_type'] == 'dynamic':
            specs = criteria_str.split('.')[3:]
            dynamics = []
            for spec in specs:
                # Parse characteristic
                res = re.search('[0-9]+', spec)
                assert res is not None, \
                    "FATAL: Bad lambda characteristic specification in criteria '{0}'".format(
                        criteria_str)
                characteristic = float(res.group(0))

                # Parser mantissa
                res = re.search('p[0-9]+', spec)
                assert res is not None, \
                    "FATAL: Bad lambda mantissa specification in criteria '{0}'".format(
                        criteria_str)
                mantissa = float("0." + res.group(0)[1:])

                if 'B' in spec:
                    dynamics.append(('birth_mu', characteristic + mantissa))
                elif 'D' in spec:
                    dynamics.append(('death_lambda', characteristic + mantissa))
                elif 'M' in spec:
                    dynamics.append(('malfunction_lambda', characteristic + mantissa))
                elif 'R' in spec:
                    dynamics.append(('repair_mu', characteristic + mantissa))

            ret['dynamics'] = dynamics

        return ret


def factory(cli_arg: str, main_config: tp.Dict[str, str], batch_generation_root: str, **kwargs):
    """
    factory to create ``Population`` derived classes from the command line definition of batch
    criteria.

    """
    attr = PopulationParser()(cli_arg)

    def gen_max_sizes():
        """
        Generates the maximum swarm sizes for each experiment in a batch. This is not the same as
        the starting swarm size, if birth population dynamics are enabled.
        """
        if attr["increment_type"] == 'Linear':
            return [attr["linear_increment"] * x for x in range(1, 11)]
        elif attr["increment_type"] == 'Log':
            return [2 ** x for x in range(0, int(math.log2(attr["max_size"])) + 1)]

    def __init__(self):
        Population.__init__(self,
                            cli_arg,
                            main_config,
                            batch_generation_root,
                            gen_max_sizes(),
                            attr['dynamics_type'],
                            attr.get('dynamics', None))

    return type(cli_arg,
                (Population,),
                {"__init__": __init__})
