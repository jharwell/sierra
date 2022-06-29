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
import typing as tp
import os
import logging

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D
import sierra.core.config
import sierra.core.plugin_manager as pm
from sierra.core import types


class ExperimentSpec():
    """
    The specification for a single experiment with a batch.

    In the interest of DRY, this class collects the following common components:

    - Experiment # within the batch

    - Root input directory for all :term:`Experimental Run` input files
      comprising the :term:`Experiment`

    - Pickle file path for the experiment

    - Arena dimensions for the experiment

    - Full scenario name
    """

    def __init__(self,
                 criteria: bc.IConcreteBatchCriteria,
                 exp_num: int,
                 cmdopts: types.Cmdopts) -> None:
        self.exp_num = exp_num
        self.exp_input_root = os.path.join(cmdopts['batch_input_root'],
                                           criteria.gen_exp_dirnames(cmdopts)[exp_num])
        self.exp_def_fpath = os.path.join(self.exp_input_root,
                                          sierra.core.config.kPickleLeaf)
        self.logger = logging.getLogger(__name__)
        self.criteria = criteria

        from_bivar_bc1 = False
        from_bivar_bc2 = False
        from_univar_bc = False

        if criteria.is_bivar():
            bivar = tp.cast(bc.BivarBatchCriteria, criteria)
            from_bivar_bc1 = hasattr(bivar.criteria1,
                                     'exp_scenario_name')
            from_bivar_bc2 = hasattr(bivar.criteria2,
                                     'exp_scenario_name')
        else:
            from_univar_bc = hasattr(criteria,
                                     'exp_scenario_name')

        # Need to get per-experiment arena dimensions from batch criteria, as
        # they might be different for each experiment
        if from_univar_bc:
            self.arena_dim = criteria.arena_dims()[exp_num]
            self.scenario_name = criteria.exp_scenario_name(exp_num)
            self.logger.debug("Read scenario dimensions '%s' from univariate batch criteria",
                              self.arena_dim)
        elif from_bivar_bc1 or from_bivar_bc2:
            self.arena_dim = criteria.arena_dims()[exp_num]
            self.logger.debug("Read scenario dimensions '%s' bivariate batch criteria",
                              self.arena_dim)
            self.scenario_name = criteria.exp_scenario_name(exp_num)

        else:  # Default case: scenario dimensions read from cmdline
            sgp = pm.module_load_tiered(project=cmdopts['project'],
                                        path='generators.scenario_generator_parser')
            kw = sgp.ScenarioGeneratorParser().to_dict(cmdopts['scenario'])
            self.arena_dim = ArenaExtent(
                Vector3D(kw['arena_x'], kw['arena_y'], kw['arena_z']))
            self.logger.debug("Read scenario dimensions %s from cmdline spec",
                              self.arena_dim)

            self.scenario_name = cmdopts['scenario']


__api__ = ['ExperimentSpec']
