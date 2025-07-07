#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import time
import datetime
import typing as tp
import logging
import copy

# 3rd party packages
import yaml

# Project packages
from sierra.core import config, utils, types, batchroot, storage, models, exproot
from sierra.core.variables import batch_criteria as bc
from sierra.core import plugin as pm

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    intra = _load_models(main_config, cmdopts, "intra")

    _logger.info("Running %d intra-experiment models...", len(intra))
    start = time.time()
    IntraExpModelRunner(cmdopts, pathset, intra)(criteria)
    elapsed = int(time.time() - start)
    sec = datetime.timedelta(seconds=elapsed)
    _logger.info("Intra-experiment models finished in %s", str(sec))

    inter = _load_models(main_config, cmdopts, "inter")

    _logger.info("Running %d inter-experiment models...", len(inter))
    start = time.time()

    InterExpModelRunner(cmdopts, pathset, inter)(criteria)

    elapsed = int(time.time() - start)
    sec = datetime.timedelta(seconds=elapsed)
    _logger.info("Inter-experiment models finished in %s", str(sec))


def _load_models(
    main_config: types.YAMLDict, cmdopts: types.Cmdopts, model_type: str
) -> tp.List[
    tp.Union[
        models.interface.IConcreteInterExpModel1D,
        models.interface.IConcreteIntraExpModel1D,
    ]
]:
    project_models = cmdopts["project_config_root"] / config.kYAML.models
    models = []

    if not utils.path_exists(project_models):
        _logger.debug(
            "No models to load for project %s: %s does not exist",
            cmdopts["project"],
            project_models,
        )
        return []

    _logger.info("Loading models for project '%s'", cmdopts["project"])

    models_config = yaml.load(utils.utf8open(project_models), yaml.FullLoader)
    pm.models.initialize(
        cmdopts["project"], pathlib.Path(cmdopts["project_model_root"])
    )

    # All models present in the .yaml file are enabled/set to run
    # unconditionally
    available = pm.models.available_plugins()
    _logger.debug(
        "Project %s has %d available model plugins",
        cmdopts["project"],
        len(available),
    )

    for module_name in pm.models.available_plugins():
        # No models specified--nothing to do
        if models_config.get("models") is None:
            continue

        for conf in models_config["models"]:
            if conf["pyfile"] == module_name:

                _logger.debug("Model %s enabled by configuration", module_name)
                pm.models.load_plugin(module_name)
                model_name = f"models.{module_name}"
                module = pm.models.get_plugin_module(model_name)
                _logger.debug(
                    ("Configured model plugin %s has %d models"),
                    model_name,
                    len(module.available_models(model_type)),
                )

                for avail in module.available_models(model_type):
                    model = getattr(module, avail)(main_config, conf)
                    models.append(model)

            else:
                _logger.debug("Model %s disabled by configuration", module_name)

    if len(models) > 0:
        _logger.info(
            "Loaded %s models for project %s",
            len(models),
            cmdopts["project"],
        )

    return models


class IntraExpModelRunner:
    """
    Runs all enabled intra-experiment models for all experiments in a batch.
    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        to_run: tp.List[
            tp.Union[
                models.interface.IConcreteIntraExpModel1D,
                models.interface.IConcreteIntraExpModel2D,
            ]
        ],
    ) -> None:
        self.cmdopts = cmdopts
        self.models = to_run
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.XVarBatchCriteria) -> None:
        exp_dirnames = criteria.gen_exp_names()
        exp_to_run = utils.exp_range_calc(
            self.cmdopts["exp_range"], self.pathset.output_root, exp_dirnames
        )

        for exp in exp_to_run:
            self._run_models_in_exp(criteria, exp_dirnames, exp)

    def _run_models_in_exp(
        self,
        criteria: bc.XVarBatchCriteria,
        exp_dirnames: tp.List[pathlib.Path],
        exp: pathlib.Path,
    ) -> None:
        exp_index = exp_dirnames.index(exp)

        exproots = exproot.PathSet(self.pathset, exp.name, exp_dirnames[0].name)

        utils.dir_create_checked(exproots.model_root, exist_ok=True)

        for model in self.models:
            self._run_model_in_exp(criteria, self.cmdopts, exproots, exp_index, model)

    def _run_model_in_exp(
        self,
        criteria: bc.XVarBatchCriteria,
        cmdopts: types.Cmdopts,
        pathset: exproot.PathSet,
        exp_index: int,
        model: tp.Union[
            models.interface.IConcreteIntraExpModel1D,
            models.interface.IConcreteIntraExpModel2D,
        ],
    ) -> None:
        if not model.run_for_exp(criteria, cmdopts, exp_index):
            self.logger.debug(
                "Skip running intra-experiment model from '%s' for exp%s",
                str(model),
                exp_index,
            )
            return

        # Run the model
        self.logger.debug(
            "Run intra-experiment model '%s' for exp%s", str(model), exp_index
        )
        dfs = model.run(criteria, exp_index, cmdopts, pathset)

        for df, csv_stem in zip(dfs, model.target_csv_stems()):
            path_stem = pathset.model_root / csv_stem

            # Write model legend file so the generated graph can find it
            with utils.utf8open(
                path_stem.with_suffix(config.kModelsExt["legend"]), "w"
            ) as f:
                for j, search in enumerate(dfs):
                    if search.values.all() == df.values.all():
                        legend = model.legend_names()[j]
                        f.write(legend)
                        break

            # Write model .csv file
            storage.df_write(
                df,
                path_stem.with_suffix(config.kModelsExt["model"]),
                "storage.csv",
                index=False,
            )


class InterExpModelRunner:
    """
    Runs all enabled inter-experiment models in a batch.
    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        to_run: tp.List[models.interface.IConcreteInterExpModel1D],
    ) -> None:
        self.pathset = pathset
        self.cmdopts = cmdopts
        self.models = to_run

    def __call__(self, criteria: bc.XVarBatchCriteria) -> None:

        cmdopts = copy.deepcopy(self.cmdopts)

        utils.dir_create_checked(self.pathset.model_root, exist_ok=True)
        utils.dir_create_checked(self.pathset.graph_collate_root, exist_ok=True)

        for model in self.models:
            if not model.run_for_batch(criteria, cmdopts):
                self.logger.debug(
                    "Skip running inter-experiment model '%s'", str(model)
                )
                continue

            # Run the model
            self.logger.debug("Run inter-experiment model '%s'", str(model))

            dfs = model.run(criteria, cmdopts, self.pathset)

            for df, csv_stem in zip(dfs, model.target_csv_stems()):
                path_stem = self.model_root / csv_stem

                # Write model .csv file
                storage.df_write(
                    df,
                    path_stem.with_suffix(config.kModelsExt["model"]),
                    "storage.csv",
                    index=False,
                )

                # 1D dataframe -> line graph with legend
                if len(df.index) == 1:
                    legend_path = path_stem.with_suffix(config.kModelsExt["legend"])

                    # Write model legend file so the generated graph can find it
                    with utils.utf8open(legend_path, "w") as f:
                        for i, search in enumerate(dfs):
                            if search.values.all() == df.values.all():
                                legend = model.legend_names()[i]
                                f.write(legend)
                                break
