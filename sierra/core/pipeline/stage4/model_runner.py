# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
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
from sierra.core import models, types, utils, storage, config, batchroot, exproot


class IntraExpModelRunner:
    """
    Runs all enabled intra-experiment models for all experiments in a batch.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 pathset: batchroot.PathSet,
                 to_run: tp.List[tp.Union[models.interface.IConcreteIntraExpModel1D,
                                          models.interface.IConcreteIntraExpModel2D]]) -> None:
        self.cmdopts = cmdopts
        self.models = to_run
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_run = utils.exp_range_calc(self.cmdopts["exp_range"],
                                          self.pathset.output_root,
                                          criteria)
        exp_dirnames = criteria.gen_exp_names()

        for exp in exp_to_run:
            self._run_models_in_exp(criteria, exp_dirnames, exp)

    def _run_models_in_exp(self,
                           criteria: bc.IConcreteBatchCriteria,
                           exp_dirnames: tp.List[pathlib.Path],
                           exp: pathlib.Path) -> None:
        exp_index = exp_dirnames.index(exp)

        exproots = exproot.PathSet(self.pathset, exp.name, exp_dirnames[0].name)

        utils.dir_create_checked(exproots.model_root, exist_ok=True)

        for model in self.models:
            self._run_model_in_exp(criteria,
                                   self.cmdopts,
                                   exproots,
                                   exp_index,
                                   model)

    def _run_model_in_exp(self,
                          criteria: bc.IConcreteBatchCriteria,
                          cmdopts: types.Cmdopts,
                          pathset: exproot.PathSet,
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
        dfs = model.run(criteria, exp_index, cmdopts, pathset)
        writer = storage.DataFrameWriter('storage.csv')

        for df, csv_stem in zip(dfs, model.target_csv_stems()):
            path_stem = pathset.model_root / csv_stem

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
                 pathset: batchroot.PathSet,
                 to_run: tp.List[models.interface.IConcreteInterExpModel1D]) -> None:
        self.pathset = pathset
        self.cmdopts = cmdopts
        self.models = to_run
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 criteria: bc.IConcreteBatchCriteria) -> None:

        cmdopts = copy.deepcopy(self.cmdopts)

        utils.dir_create_checked(self.pathset.model_root, exist_ok=True)
        utils.dir_create_checked(self.pathset.graph_collate_root, exist_ok=True)

        for model in self.models:
            if not model.run_for_batch(criteria, cmdopts):
                self.logger.debug("Skip running inter-experiment model '%s'",
                                  str(model))
                continue

            # Run the model
            self.logger.debug("Run inter-experiment model '%s'", str(model))

            dfs = model.run(criteria, cmdopts, self.pathset)

            for df, csv_stem in zip(dfs, model.target_csv_stems()):
                path_stem = self.model_root / csv_stem

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


__all__ = [
    'IntraExpModelRunner',
    'InterExpModelRunner'
]
