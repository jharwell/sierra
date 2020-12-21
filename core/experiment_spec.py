# Copyright 2020 John Harwell, All rights reserved.
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

# Core packages
import logging
import typing as tp
import os

# 3rd party packages

# Project packages
import core.variables.batch_criteria as bc
from core.variables import constant_density
from core.utils import ArenaExtent
import core.generators.scenario_generator_parser as sgp
from core.vector import Vector3D


class ExperimentSpec():
    """
    The specification for a single experiment with a batch.

    - Experiment # within the batch
    - Root input directory for all simulation files comprising the experiment
    - Pickle file path for the experiment
    - Arena dimensions for the experiment
    - Full scenario name
    """

    def __init__(self, criteria, exp_num: int, cmdopts: dict) -> None:
        self.exp_num = exp_num
        self.exp_input_root = os.path.join(cmdopts['batch_input_root'],
                                           criteria.gen_exp_dirnames(cmdopts)[exp_num])
        self.exp_def_fpath = os.path.join(self.exp_input_root, "exp_def.pkl")
        self.logger = logging.getLogger(__name__)

        from_bivar_bc1 = False
        from_bivar_bc2 = False
        from_univar_bc = False

        if criteria.is_bivar():
            bivar = tp.cast(bc.BivarBatchCriteria, criteria)
            from_bivar_bc1 = isinstance(bivar.criteria1, constant_density.ConstantDensity)
            from_bivar_bc2 = isinstance(bivar.criteria2, constant_density.ConstantDensity)
        else:
            from_univar_bc = isinstance(criteria, constant_density.ConstantDensity)

        # Need to get per-experiment arena dimensions from batch criteria, as they might be
        # different for each experiment
        if from_univar_bc:
            self.arena_dim = criteria.arena_dims()[exp_num]
            self.scenario_name = criteria.exp_scenario_name(exp_num)
            self.logger.debug("Obtained scenario dimensions '%s' from univariate batch criteria",
                              self.arena_dim)
        elif from_bivar_bc1 or from_bivar_bc2:
            self.arena_dim = criteria.arena_dims()[exp_num]
            self.logger.debug("Obtained scenario dimensions '%s' bivariate batch criteria",
                              self.arena_dim)
            self.scenario_name = criteria.exp_scenario_name(exp_num)
        else:  # Defaultc case: scenario dimensions read from cmdline
            kw = sgp.ScenarioGeneratorParser.reparse_str(cmdopts['scenario'])
            self.arena_dim = ArenaExtent(Vector3D(kw['arena_x'], kw['arena_y'], kw['arena_z']))
            self.logger.debug("Read scenario dimensions %s from cmdline spec",
                              self.arena_dim)

            self.scenario_name = cmdopts['scenario']


__api__ = ['ExperimentSpec']
