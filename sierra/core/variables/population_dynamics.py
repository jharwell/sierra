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

# Core packages
import typing as tp
import os

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
import sierra.core.utils
import sierra.core.variables.dynamics_parser as dp
from sierra.core.xml_luigi import XMLAttrChange, XMLAttrChangeSet
import sierra.core.config
from sierra.core.xml_luigi import XMLLuigi
import sierra.core.variables.time_setup as ts


@implements.implements(bc.IConcreteBatchCriteria)
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
                 batch_input_root: str,
                 dynamics_types: tp.List[str],
                 dynamics: tp.List[tp.Set[tp.Tuple[str, float]]]) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)
        self.dynamics_types = dynamics_types
        self.dynamics = dynamics
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate list of sets of changes for population dynamics.
        """
        # Note the # of decimal places used--these rates can get pretty small, and we do NOT want to
        # round/truncate unecessarily, because that can change behavior in statistical equilibrium.
        if not self.attr_changes:  # empty
            for d in self.dynamics:
                self.attr_changes.append(XMLAttrChangeSet(*{XMLAttrChange(".//temporal_variance/population_dynamics",
                                                                          t[0],
                                                                          str('%3.9f' % t[1])) for t in d}))
        return self.attr_changes

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, tp.Any]) -> list:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: tp.Dict[str, tp.Any],
                     exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        # If exp_dirs is passed, then we have been handed a subset of the total # of directories in
        # the batch exp root, and so n_exp() will return more experiments than we actually
        # have. This behavior is needed to correctly extract x/y values for bivariate experiments.
        #
        # We use range() instead of the actual PD values so that this batch criteria works
        # well with box and whisker plots around each data point. This is OK because we also
        # the generation of the range of values that become the xticks, and we KNOW they are
        # linearly spaced.
        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        return [float(i) for i in range(len(exp_dirs))]

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, tp.Any],
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        ticks = []

        exp0_def = XMLAttrChangeSet.unpickle(os.path.join(self.batch_input_root,
                                                          exp_dirs[0],
                                                          sierra.core.config.kPickleLeaf))
        T_Sbar0 = PopulationDynamics.calc_untasked_swarm_system_time(exp0_def)

        for d in exp_dirs:
            exp_def = XMLAttrChangeSet.unpickle(os.path.join(self.batch_input_root,
                                                             d,
                                                             sierra.core.config.kPickleLeaf))

            # If we had pure death dynamics, the tasked swarm time is 0 in the steady state, so we
            # use lambda_d as the ticks instead, which is somewhat more meaningful.
            if self.is_pure_death_dynamics():
                lambda_d, _, _, _ = PopulationDynamics.extract_rate_params(exp_def)
                ticks.append(lambda_d)
            else:
                T_Sbar = PopulationDynamics.calc_untasked_swarm_system_time(exp_def)

                ticks.append(round(T_Sbar0 / T_Sbar, 4))

        return list(map(str, ticks))

    def graph_xlabel(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        if self.is_pure_death_dynamics():
            return "Death Rate"
        else:
            return "Population Variance"

    def graph_ylabel(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        return "Superlinearity"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'robustness_pd']

    def is_pure_death_dynamics(self) -> bool:
        return 'D' in self.dynamics_types and 'B' not in self.dynamics_types

    @staticmethod
    def calc_untasked_swarm_system_time(exp_def: XMLAttrChangeSet) -> float:
        params = ts.ARGoSTimeSetup.extract_time_params(exp_def)
        T = params['T_in_secs'] * params['ticks_per_sec']
        lambda_d, mu_b, lambda_m, mu_r = PopulationDynamics.extract_rate_params(exp_def)

        # Pure death dynamics with a service rate of infinity. The "how long is a robot part of a
        # tasked swarm" calculation is only valid for stable queueing systems, with well defined
        # arrival and service rates (i.e. not 0 and not infinite).
        if lambda_d > 0.0 and mu_b == 0.0:
            return T

        # mu/lambda for combined queue
        lambda_Sbar = lambda_d + lambda_m
        mu_Sbar = mu_b + mu_r

        # L_Sbar = # Robots NOT currently in the swarm S.
        try:
            rho_Sbar = lambda_Sbar / mu_Sbar
        except ZeroDivisionError:
            return 0.0

        L_Sbar = rho_Sbar ** 2 / (1 - rho_Sbar)

        # W_Sbar = waiting time in the Sbar queue.
        W_Sbar = L_Sbar / lambda_Sbar

        # W = waiting time in Sbar system (includes service time), and therefore time NOT in S.
        W = W_Sbar + 1 / mu_Sbar

        return W

    @staticmethod
    def extract_rate_params(exp_def) -> tp.Tuple[float, float, float, float]:
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


class PopulationDynamicsParser(dp.DynamicsParser):
    """
    Enforces the cmdline definition of the :class`PopulationDynamics` batch criteria described in
    :ref:`ln-bc-population-dynamics`.
    """

    def specs_dict(self) -> tp.Dict[str, str]:
        return {'B': 'birth_mu',
                'D': 'death_lambda',
                'M': 'malfunction_lambda',
                'R': 'repair_mu'
                }


def factory(cli_arg: str,
            main_config: tp.Dict[str, tp.Any],
            batch_input_root: str,
            **kwargs) -> PopulationDynamics:
    """
    Factory to create ``PopulationDynamics`` derived classes from the command line definition.

    """
    attr = PopulationDynamicsParser()(cli_arg)

    def gen_dynamics() -> tp.List[tp.Set[tp.Tuple[str, float]]]:
        dynamics = [{(d[0], d[1] + d[1] * x * float(attr['factor']))
                     for d in attr['dynamics']} for x in range(0, attr['cardinality'])]
        return dynamics

    def __init__(self) -> None:
        PopulationDynamics.__init__(self,
                                    cli_arg,
                                    main_config,
                                    batch_input_root,
                                    attr['dynamics_types'],
                                    gen_dynamics())

    return type(cli_arg,  # type: ignore
                (PopulationDynamics,),
                {"__init__": __init__})


__api__ = [
    'PopulationDynamics'
]
