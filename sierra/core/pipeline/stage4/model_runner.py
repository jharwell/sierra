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
"""Classes for running project-specific models in a general purpose way within
a batch experiment.

"""
# Core packages
import os
import copy
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import models, types, utils, storage


class IntraExpModelRunner:
    """
    Runs all enabled intra-experiment models for all experiments in a batch.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 models: tp.List[tp.Union[models.interface.IConcreteIntraExpModel1D,
                                          models.interface.IConcreteIntraExpModel2D]]) -> None:
        self.cmdopts = cmdopts
        self.models = models
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 main_config: types.YAMLDict,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_run = utils.exp_range_calc(self.cmdopts,
                                          self.cmdopts['batch_output_root'],
                                          criteria)
        exp_dirnames = criteria.gen_exp_dirnames(self.cmdopts)

        for i, exp in enumerate(exp_to_run):
            exp = os.path.split(exp)[1]
            exp_index = exp_dirnames.index(exp)

            cmdopts = copy.deepcopy(self.cmdopts)
            cmdopts["exp0_output_root"] = os.path.join(self.cmdopts["batch_output_root"],
                                                       exp_dirnames[0])
            cmdopts["exp0_stat_root"] = os.path.join(self.cmdopts["batch_stat_root"],
                                                     exp_dirnames[0])

            cmdopts["exp_input_root"] = os.path.join(
                self.cmdopts['batch_input_root'], exp)
            cmdopts["exp_output_root"] = os.path.join(
                self.cmdopts['batch_output_root'], exp)
            cmdopts["exp_graph_root"] = os.path.join(
                self.cmdopts['batch_graph_root'], exp)
            cmdopts["exp_stat_root"] = os.path.join(
                self.cmdopts["batch_stat_root"], exp)
            cmdopts["exp_model_root"] = os.path.join(
                cmdopts['batch_model_root'], exp)

            utils.dir_create_checked(
                cmdopts['exp_model_root'], exist_ok=True)

            for model in self.models:
                if not model.run_for_exp(criteria, cmdopts, exp_index):
                    self.logger.debug("Skip running intra-experiment model from '%s' for exp%s",
                                      str(model),
                                      exp_index)
                    continue

                # Run the model
                self.logger.debug("Run intra-experiment model '%s' for exp%s",
                                  str(model),
                                  exp_index)
                dfs = model.run(criteria, exp_index, cmdopts)
                for df, csv_stem in zip(dfs, model.target_csv_stems()):
                    path_stem = os.path.join(
                        cmdopts['exp_model_root'], csv_stem)

                    # Write model legend file so the generated graph can find it
                    with open(path_stem + '.legend', 'w') as f:
                        for i, search in enumerate(dfs):
                            if search.values.all() == df.values.all():
                                legend = model.legend_names()[i]
                                f.write(legend)
                                break

                    # Write model .csv file
                    storage.DataFrameWriter('storage.csv')(
                        df, path_stem + '.model', index=False)


class InterExpModelRunner:
    """
    Runs all enabled inter-experiment models in a batch.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 models: tp.List[models.interface.IConcreteInterExpModel1D]) -> None:
        self.cmdopts = cmdopts
        self.models = models
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
                path_stem = os.path.join(cmdopts['batch_model_root'], csv_stem)

                # Write model .csv file
                storage.DataFrameWriter('storage.csv')(
                    df, path_stem + '.model', index=False)

                # 1D dataframe -> line graph with legend
                if len(df.index) == 1:
                    # Write model legend file so the generated graph can find it
                    with open(path_stem + '.legend', 'w') as f:
                        for i, search in enumerate(dfs):
                            if search.values.all() == df.values.all():
                                legend = model.legend_names()[i]
                                f.write(legend)
                                break


__api__ = [
    'IntraExpModelRunner',
    'InterExpModelRunner'
]
