# Copyright 2020 John Harwell, All rights reserved.
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
Classes for the population dynamics batch criteria. See :ref:`ln-bc-population-dynamics` for usage
documentation.
"""

import typing as tp
import re
import math
import os

from core.variables import batch_criteria as bc
import core.utils


class PopulationDynamics(bc.UnivarBatchCriteria):
    """
    A univariate range of population dynamics used to define batched experiments. This class is a
    base class which should (almost) never be used on its own. Instead, the ``factory()`` function
    should be used to dynamically create derived classes expressing the user's desired dynamics
    distribution.

    Attributes:
        dynamics_type: The type of population dynamics.
        dynamics: List of tuples specifying XML changes for each variation of population dynamics.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_generation_root: str,
                 dynamics_types: tp.List[tp.Tuple[str, int]],
                 dynamics: tp.List[tp.Tuple[str, int]]) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
        self.dynamics_types = dynamics_types
        self.dynamics = dynamics

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes for population dynamics.
        """
        # Note the # of decimal places used--these rates can get pretty small, and we do NOT want to
        # round/truncate unecessarily, because that can change behavior in statistical equilibrium.

        changes = []  # type: list
        for d in self.dynamics:
            changes.append({(".//temporal_variance/population_dynamics",
                             t[0],
                             str('%3.9f' % t[1])) for t in d})
        return changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> list:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ticks = []
        for d in exp_dirs:
            exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                               d,
                                                               'exp_def.pkl'))
            explen, expticks = PopulationDynamics.extract_explen(exp_def)
            dlambda, bmu, mlambda, rmu = PopulationDynamics.extract_rate_params(exp_def)
            s = dlambda + mlambda - (bmu + rmu)
            w = 1.0 / s if s > 0.0 else (explen * expticks)
            ticks.append(round(w / (explen * expticks), 4))

        if cmdopts['plot_log_xaxis']:
            return [math.log2(x) for x in ticks]
        else:
            return ticks

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, str],
                          exp_dirs: list = None) -> tp.List[str]:
        return list(map(str, self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Average Fraction of Time Robots Allocated To Task"

    def graph_ylabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Superlinearity"

    def pm_query(self, pm: str) -> bool:
        return pm in ['blocks-transported', 'robustness']

    @staticmethod
    def extract_rate_params(exp_def):
        """
        Extract and return the (death, birth, malfunction, and repair) rate parameters for use in
        calculating queueing theoretic limits for the specified experiment. If any of them were not
        used in the batched experiment, they will have value 0.0.

        """
        # OK to have these not defined for a particular batched experiment
        repair_mu = 0.0
        malfunction_lambda = 0.0
        birth_mu = 0.0
        death_lambda = 0.0

        for _, attr, value in exp_def:
            if 'death_lambda' in attr:
                death_lambda = float(value)
            if 'birth_mu' in attr:
                birth_mu = float(value)
            if 'malfunction_lambda' in attr:
                malfunction_lambda = float(value)
            if 'repair_mu' in attr:
                repair_mu = float(value)

        return (death_lambda, birth_mu, malfunction_lambda, repair_mu)

    @staticmethod
    def extract_explen(exp_def):
        """
        Extract and return the (experiment length in seconds, ticks per second) for the specified
        experiment for use in calculating queueing theoretic limits.
        """
        for path, attr, value in exp_def:
            if 'experiment' in path:
                if 'length' in attr:
                    explen = int(value)
                if 'ticks_per_second' in attr:
                    expticks = int(value)
        return (explen, expticks)


class PopulationDynamicsParser():
    """
    Enforces the cmdline definition of the criteria described in the module docstring.
    """

    def __call__(self, criteria_str) -> dict:
        ret = {
            'dynamics': list(),
            'factor': float()
        }

        # Parse cardinality
        res = re.search(r".C[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad cardinality for population dynamics in criteria '{0}'".format(criteria_str)
        ret['cardinality'] = int(res.group(0)[2:])

        # Parse factor characteristic
        res = re.search(r'F[0-9]+p[0-9]+', criteria_str)
        assert res is not None, \
            "FATAL: Bad Factor specification in criteria '{0}'".format(criteria_str)
        characteristic = float(res.group(0)[1:].split('p')[0])
        mantissa = float("0." + res.group(0)[1:].split('p')[1])

        ret['factor'] = characteristic + mantissa

        # Parse birth/death process parameters
        specs = criteria_str.split('.')[2:]
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
    Factory to create ``PopulationDynamics`` derived classes from the command line definition.

    """
    attr = PopulationDynamicsParser()(cli_arg)

    def gen_dynamics():
        # ideal conditions = no dynamics
        dynamics = [{(d[0], 0.0) for d in attr['dynamics']}]
        dynamics.extend([{(d[0], d[1] + d[1] * x * float(attr['factor']))
                          for d in attr['dynamics']} for x in range(0, attr['cardinality'])])
        return dynamics

    def __init__(self) -> None:
        PopulationDynamics.__init__(self,
                                    cli_arg,
                                    main_config,
                                    batch_generation_root,
                                    attr['dynamics'],
                                    gen_dynamics())

    return type(cli_arg,
                (PopulationDynamics,),
                {"__init__": __init__})


__api__ = [
    'PopulationDynamics'
]
