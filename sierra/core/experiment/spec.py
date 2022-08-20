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
import logging
import pathlib

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D
import sierra.core.plugin_manager as pm
from sierra.core import types, config
from sierra.core.experiment import xml


class SimpleBatchScaffoldSpec():
    def __init__(self,
                 criteria: bc.BatchCriteria,
                 log: bool = False) -> None:
        self.criteria = criteria
        self.chgs = criteria.gen_attr_changelist()
        self.adds = criteria.gen_tag_addlist()
        self.rms = criteria.gen_tag_rmlist()
        self.logger = logging.getLogger(__name__)

        self.n_exps = 0

        self.mods = []
        self.is_compound = False

        assert len(self.rms) == 0,\
            "Batch criteria cannot remove XML tags"

        if self.chgs:
            self.mods = self.chgs
            self.n_exps = len(self.chgs)
            if log:
                self.logger.info(("Calculating scaffold: cli='%s': Modify %s "
                                  "XML tags per experiment"),
                                 self.criteria.cli_arg,
                                 len(self.chgs[0]))
        elif self.adds:
            self.mods = self.adds
            self.n_exps = len(self.adds)
            if log:
                self.logger.info(("Calculating scaffold: cli='%s': Add %s XML "
                                  "tags per experiment"),
                                 self.criteria.cli_arg,
                                 len(self.adds[0]))
        else:
            raise RuntimeError(("This spec can't be used with compound "
                                "scaffolding"))

    def __iter__(self) -> tp.Iterator[tp.Union[xml.AttrChangeSet,
                                               xml.TagAddList]]:
        return iter(self.mods)

    def __len__(self) -> int:
        return self.n_exps


class CompoundBatchScaffoldSpec():
    def __init__(self,
                 criteria: bc.BatchCriteria,
                 log: bool = False) -> None:
        self.criteria = criteria
        self.chgs = criteria.gen_attr_changelist()
        self.adds = criteria.gen_tag_addlist()
        self.rms = criteria.gen_tag_rmlist()
        self.logger = logging.getLogger(__name__)

        self.n_exps = 0

        self.is_compound = True
        self.mods = []

        assert len(self.rms) == 0,\
            "Batch criteria cannot remove XML tags"

        if self.chgs and self.adds:
            for addlist in self.adds:
                for chgset in self.chgs:
                    t = addlist, chgset
                    self.mods.append(t)
                    self.n_exps += 1

            if log:
                self.logger.info(("Calculating scaffold: cli='%s': Add  "
                                  "%s XML tags AND modify %s XML tags per "
                                  "per experiment"),
                                 self.criteria.cli_arg,
                                 len(self.adds[0]),
                                 len(self.chgs[0]))

        else:
            raise RuntimeError(("This spec can only be used with compound "
                                "scaffolding"))

    def __len__(self) -> int:
        return self.n_exps


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
        exp_name = criteria.gen_exp_names(cmdopts)[exp_num]

        self.exp_input_root = pathlib.Path(cmdopts['batch_input_root'], exp_name)
        self.exp_def_fpath = self.exp_input_root / config.kPickleLeaf

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
            self.arena_dim = criteria.arena_dims(cmdopts)[exp_num]
            self.scenario_name = criteria.exp_scenario_name(exp_num)
            self.logger.debug("Read scenario dimensions '%s' from univariate batch criteria",
                              self.arena_dim)
        elif from_bivar_bc1 or from_bivar_bc2:
            self.arena_dim = criteria.arena_dims(cmdopts)[exp_num]
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


def scaffold_spec_factory(criteria: bc.BatchCriteria,
                          **kwargs) -> tp.Union[SimpleBatchScaffoldSpec,
                                                CompoundBatchScaffoldSpec]:
    chgs = criteria.gen_attr_changelist()
    adds = criteria.gen_tag_addlist()

    if chgs and adds:
        logging.debug("Create compound batch experiment scaffolding for '%s'",
                      criteria.cli_arg)
        return CompoundBatchScaffoldSpec(criteria, **kwargs)
    else:
        logging.debug("Create simple batch experiment scaffolding for '%s'",
                      criteria.cli_arg)
        return SimpleBatchScaffoldSpec(criteria, **kwargs)


__api__ = ['ExperimentSpec']
