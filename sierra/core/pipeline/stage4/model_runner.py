# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
"""Classes for running project-specific :term:`Models <Model>`.

"""
# Core packages
import copy
import typing as tp
import logging
import pathlib

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import models, types, utils, storage, config


class IntraExpModelRunner:
    """
    Runs all enabled intra-experiment models for all experiments in a batch.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 to_run: tp.List[tp.Union[models.interface.IConcreteIntraExpModel1D,
                                          models.interface.IConcreteIntraExpModel2D]]) -> None:
        self.cmdopts = cmdopts
        self.models = to_run
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 main_config: types.YAMLDict,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_run = utils.exp_range_calc(self.cmdopts,
                                          self.cmdopts['batch_output_root'],
                                          criteria)
        exp_dirnames = criteria.gen_exp_names(self.cmdopts)

        for exp in exp_to_run:
            self._run_models_in_exp(criteria, exp_dirnames, exp)

    def _run_models_in_exp(self,
                           criteria: bc.IConcreteBatchCriteria,
                           exp_dirnames: tp.List[pathlib.Path],
                           exp: pathlib.Path) -> None:
        exp_index = exp_dirnames.index(exp)

        cmdopts = copy.deepcopy(self.cmdopts)
        batch_output_root = pathlib.Path(self.cmdopts["batch_output_root"])
        batch_stat_root = pathlib.Path(self.cmdopts["batch_stat_root"])
        batch_input_root = pathlib.Path(self.cmdopts["batch_input_root"])
        batch_graph_root = pathlib.Path(self.cmdopts["batch_graph_root"])
        batch_model_root = pathlib.Path(self.cmdopts["batch_model_root"])

        cmdopts["exp0_output_root"] = str(batch_output_root / exp_dirnames[0].name)
        cmdopts["exp0_stat_root"] = str(batch_stat_root / exp_dirnames[0].name)

        cmdopts["exp_input_root"] = str(batch_input_root / exp.name)
        cmdopts["exp_output_root"] = str(batch_output_root / exp.name)
        cmdopts["exp_graph_root"] = str(batch_graph_root / exp.name)
        cmdopts["exp_stat_root"] = str(batch_stat_root / exp.name)
        cmdopts["exp_model_root"] = str(batch_model_root / exp.name)

        utils.dir_create_checked(cmdopts['exp_model_root'], exist_ok=True)

        for model in self.models:
            self._run_model_in_exp(criteria, cmdopts, exp_index, model)

    def _run_model_in_exp(self,
                          criteria: bc.IConcreteBatchCriteria,
                          cmdopts: types.Cmdopts,
                          exp_index: int,
                          model: tp.Union[models.interface.IConcreteIntraExpModel1D,
                                          models.interface.IConcreteIntraExpModel2D]) -> None:
        if not model.run_for_exp(criteria, cmdopts, exp_index):
            self.logger.debug("Skip running intra-experiment model from '%s' for exp%s",
                              str(model),
                              exp_index)
            return

        # Run the model
        self.logger.debug("Run intra-experiment model '%s' for exp%s",
                          str(model),
                          exp_index)
        dfs = model.run(criteria, exp_index, cmdopts)
        writer = storage.DataFrameWriter('storage.csv')

        for df, csv_stem in zip(dfs, model.target_csv_stems()):
            path_stem = pathlib.Path(cmdopts['exp_model_root']) / csv_stem

            # Write model legend file so the generated graph can find it
            with utils.utf8open(path_stem.with_suffix(config.kModelsExt['legend']),
                                'w') as f:
                for j, search in enumerate(dfs):
                    if search.values.all() == df.values.all():
                        legend = model.legend_names()[j]
                        f.write(legend)
                        break

            # Write model .csv file
            writer(df,
                   path_stem.with_suffix(config.kModelsExt['model']),
                   index=False)


class InterExpModelRunner:
    """
    Runs all enabled inter-experiment models in a batch.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 to_run: tp.List[models.interface.IConcreteInterExpModel1D]) -> None:
        self.cmdopts = cmdopts
        self.models = to_run
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 main_config: types.YAMLDict,
                 criteria: bc.IConcreteBatchCriteria) -> None:

        cmdopts = copy.deepcopy(self.cmdopts)

        utils.dir_create_checked(
            cmdopts['batch_model_root'], exist_ok=True)
        utils.dir_create_checked(
            cmdopts['batch_graph_collate_root'], exist_ok=True)

        for model in self.models:
            if not model.run_for_batch(criteria, cmdopts):
                self.logger.debug("Skip running inter-experiment model '%s'",
                                  str(model))
                continue

            # Run the model
            self.logger.debug("Run inter-experiment model '%s'", str(model))

            dfs = model.run(criteria, cmdopts)

            for df, csv_stem in zip(dfs, model.target_csv_stems()):
                path_stem = pathlib.Path(cmdopts['batch_model_root']) / csv_stem

                # Write model .csv file
                writer = storage.DataFrameWriter('storage.csv')
                writer(df,
                       path_stem.with_suffix(config.kModelsExt['model']),
                       index=False)

                # 1D dataframe -> line graph with legend
                if len(df.index) == 1:
                    legend_path = path_stem.with_suffix(config.kModelsExt['legend'])

                    # Write model legend file so the generated graph can find it
                    with utils.utf8open(legend_path, 'w') as f:
                        for i, search in enumerate(dfs):
                            if search.values.all() == df.values.all():
                                legend = model.legend_names()[i]
                                f.write(legend)
                                break


__api__ = [
    'IntraExpModelRunner',
    'InterExpModelRunner'
]
