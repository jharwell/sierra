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
r"""
Definition:
    C{cardinality}.F{Factor}[.{dynamics_type}{prob}[...]]

    - cardinality - The # of different values of each of the specified dynamics types to to test
      with (starting with the one on the cmdline). This defines the cardinality of the batched
      experiment.

    - Factor - The factor by which the starting value of all dynamics types specified on the cmdline
      are increased for each each experiment (i.e., value in last experiment in batch will be
      ``<start value> + cardinality``; a linear increase).

    - dynamics_type - {B|D|M|R}.

      - ``B`` - Adds birth dynamics to the population. Has no effect by itself, as it specifies a
        pure birth process with :math:`\lambda=\infty`, :math:`\mu_{b}`=``prob`` (a queue with an
        infinite # of robots in it which robots periodically leave from), resulting in dynamic swarm
        sizes which will increase from N...N over time. Can be specified with along with ``D|M|R``,
        in which case swarm sizes will increase according to the birth rate up until N, given N
        robots at the start of simulation.

      - ``D`` - Adds death dynamics to the population. By itself, it specifies a pure death process
        with :math:`\lambda_{d}`=``prob``, and :math:`\mu_{d}`=`\infty` (a queue which robots enter
        but never leave), resulting in dynamic swarm sizes which will decrease from N...1 over
        time. Can be specified along with ``B|M|R``.

      - ``M|R`` - Adds malfunction/repair dynamics to the population. If ``M`` dynamics specified,
        ``R`` dynamics must also be specified, and vice versa. Together they specify the dynamics of
        the swarm as robots temporarily fail, and removed from simulation, and then later are
        re-introduced after they have been repaired (a queue with :math:`\lambda_{m}` arrival rate
        and :math:`\mu_{r}` repair rate). Can be specified along with ``B|D`.


    The specified :math:`\lambda` or :math:`\mu` are the rate parameters of the exponential
    distribution used to distribute the event times of the Poisson process governing swarm sizes,
    *NOT* Poisson process parameter, which is their mean; e.g.,
    :math:`\lambda=\frac{1}{\lambda_{d}}` for death dynamics.

Examples:

    - ``C10.F2p0.B0p001``: 10 levels of population variability applied using a pure birth process
      with a 0.001 parameter, which will be linearly varied in [0.001,0.001*2.0*10]. For all
      experiments, the initial swarm is not controlled directly; the value in template input file if
      not controlled by another variable.

    - ``C4.F3p0.D0p001``: 4 levels of population variability applied using a pure death process with
      a 0.001 parameter, which will be linearly varied in [0.001,0.001*3.0*4]. For all experiments,
      the initial swarm is not controlled directly; the value in template input file if not
      controlled by another variable.

    - ``C8.F4p0.B0p001.D0p005``: 8 levels of population variability applied using a birth-death
      process with a 0.001 parameter for birth and a 0.005 parameter for death, which will be
      linearly varied in [0.001,0.001*4.0*8] and [0.005, 0.005*4.0*8] respectively. For all
      experiments, the initial swarm is not controlled directly; the value in template input file if
      not controlled by another variable.

    - ``C2.F1p5.M0p001.R0p005``: 2 levels of population variability applied using a
      malfunction-repair process with a 0.001 parameter for malfunction and a 0.005 parameter for
      repair which will be linearly varied in [0.001, 0.001*1.5*2] and [0.005, 0.005*1.5*2]
      respectively. For all experiments, the initial swarm is not controlled directly; the value in
      template input file if not controlled by another variable.

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
                 dynamics: tp.List[tp.Tuple[str, int]]):
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)
        self.dynamics_types = dynamics_types
        self.dynamics = dynamics

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes for population dynamics.
        """
        # Note the # of decimal places used--these rates can get pretty small, and we do NOT want to
        # round/truncate unecessarily, because that can change behavior in statistical equilibrium.
        dynamics = [{(".//temporal_variance/population_dynamics",
                      t[0],
                      str('%3.9f' % t[1])) for t in d} for d in self.dynamics]
        return dynamics

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

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        return self.graph_xticks(cmdopts, exp_dirs)

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return "Average Fraction of Time Robots Allocated To Task"

    def pm_query(self, pm: str) -> bool:
        return pm in ['blocks-transported', 'robustness-size']

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
        ret = {}

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

    def __init__(self):
        PopulationDynamics.__init__(self,
                                    cli_arg,
                                    main_config,
                                    batch_generation_root,
                                    attr['dynamics'],
                                    gen_dynamics())

    return type(cli_arg,
                (PopulationDynamics,),
                {"__init__": __init__})
