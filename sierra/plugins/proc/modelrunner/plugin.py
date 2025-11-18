#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Functionality for runner different types of models.

See :ref:`plugins/proc/modelrunner` for usage documentation.

"""
# Core packages
import pathlib
import time
import datetime
import typing as tp
import logging

# 3rd party packages
import yaml

# Project packages
from sierra.core import config, utils, types, batchroot, storage, exproot
from sierra.core.variables import batch_criteria as bc
from sierra.core import plugin as pm
from sierra.core.models import interface

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Run all intra- and inter-exp models.
    """
    models = _load_models(main_config, cmdopts, "intra")

    _logger.info("Running %d intra-experiment models...", len(models))
    start = time.time()
    _run_intra_exp(cmdopts, pathset, models, criteria)
    elapsed = int(time.time() - start)
    sec = datetime.timedelta(seconds=elapsed)
    _logger.info("Intra-experiment models finished in %s", str(sec))

    models = _load_models(main_config, cmdopts, "inter")

    _logger.info("Running %d inter-experiment models...", len(models))
    start = time.time()

    _run_inter_exp(cmdopts, pathset, models, criteria)

    elapsed = int(time.time() - start)
    sec = datetime.timedelta(seconds=elapsed)
    _logger.info("Inter-experiment models finished in %s", str(sec))


def _load_models(
    main_config: types.YAMLDict, cmdopts: types.Cmdopts, model_type: str
) -> dict[str, tp.Union[dict[str, tp.Any]]]:
    project_models = (
        pathlib.Path(cmdopts["project_config_root"]) / config.PROJECT_YAML.models
    )
    loaded = {}

    _logger.info("Loading %s-exp models for project %s", model_type, cmdopts["project"])

    models_config = yaml.load(utils.utf8open(project_models), yaml.FullLoader)

    # This is ALL model plugins found by SIERRA.
    loaded_model_plugins = [
        p
        for p in pm.pipeline.loaded_plugins()
        if pm.pipeline.loaded_plugins()[p]["type"] == "model"
    ]
    _logger.debug(
        "%d loaded model plugins on SIERRA_PLUGIN_PATH", len(loaded_model_plugins)
    )

    for plugin_name in loaded_model_plugins:
        # This is all available models for a specific plugin
        module = pm.module_load(plugin_name)
        available_models = module.sierra_models(model_type)
        _logger.debug(
            "Loaded model plugin %s has %d %s-exp models: %s",
            plugin_name,
            len(available_models) if available_models else 0,
            model_type,
            available_models,
        )
        if models_config.get(f"{model_type}-exp"):
            for conf in models_config[f"{model_type}-exp"]:

                # Class name of the model is the last part of the dot-separated
                # path, and plays no part in module lookup in the python
                # interpreter.
                model_name = conf["name"].split(".")[-1]

                # The part of the model name which is relative to the plugin
                # directory in which it should be found.
                model_module_relpath = ".".join(conf["name"].split(".")[:-1])
                model_path = "{}.{}".format(plugin_name, model_module_relpath)
                model_fullpath = f"{model_module_relpath}.{model_name}"
                if pm.module_exists(model_path):
                    _logger.debug(
                        "Loading %s-exp model %s using path %s: YAML configuration match",
                        model_type,
                        model_name,
                        model_module_relpath,
                    )
                    model_params = {
                        k: v for k, v in conf.items() if k not in ["name", "targets"]
                    }
                    loaded[model_fullpath] = {
                        "targets": conf["targets"],
                        "legend": (
                            conf["legend"]
                            if "legend" in conf
                            else ["Model Prediction" for t in conf["targets"]]
                        ),
                        "model": getattr(pm.module_load(model_path), model_name)(
                            model_params
                        ),
                    }

        else:
            _logger.debug("All %s-exp models disabled: no configuration", model_type)

    if len(loaded) > 0:
        _logger.info(
            "Loaded %s-exp %s models for project %s",
            len(loaded),
            model_type,
            cmdopts["project"],
        )

    return loaded


def _run_intra_exp(
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    to_run: dict[str, dict[str, tp.Any]],
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Run all enabled intra-experiment models for all experiments in a batch.
    """
    exp_dirnames = criteria.gen_exp_names()
    exp_to_run = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, exp_dirnames
    )

    for exp in exp_to_run:
        exp_index = exp_dirnames.index(exp.name)
        exproots = exproot.PathSet(pathset, exp.name, exp_dirnames[0])

        utils.dir_create_checked(exproots.model_root, exist_ok=True)

        for blob in to_run.values():
            _run_intra_single_in_exp(criteria, cmdopts, exproots, exp_index, blob)


def _run_intra_single_in_exp(
    criteria: bc.XVarBatchCriteria,
    cmdopts: types.Cmdopts,
    pathset: exproot.PathSet,
    exp_index: int,
    blob: dict[str, tp.Union[interface.IIntraExpModel1D, list[str]]],
) -> None:
    model = blob["model"]
    targets = blob["targets"]
    if not model.should_run(criteria, cmdopts, exp_index):
        _logger.debug(
            "Skip running intra-experiment model from '%s' for exp%s",
            str(model),
            exp_index,
        )
        return

    # Run the model
    _logger.debug(
        "Run intra-experiment model %s for %s",
        str(model),
        pathset.input_root.name,
    )
    dfs = model.run(criteria, exp_index, cmdopts, pathset)
    legend = blob["legend"]

    for df, target in zip(dfs, targets):
        path_stem = pathset.model_root / target

        # Write model legend file so the generated graph can find it
        idx = dfs.index(df)
        with utils.utf8open(
            path_stem.with_suffix(config.MODELS_EXT["legend"]), "w"
        ) as f:
            f.write(legend[idx])

        # Write model .csv file
        storage.df_write(
            df,
            path_stem.with_suffix(config.MODELS_EXT["model"]),
            "storage.csv",
            index=False,
        )


def _run_inter_exp(
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    to_run: dict[str, tp.Any],
    criteria: bc.XVarBatchCriteria,
) -> None:
    utils.dir_create_checked(pathset.model_interexp_root, exist_ok=True)

    for blob in to_run.values():
        model = blob["model"]
        legend = blob["legend"]
        targets = blob["targets"]

        if not model.should_run(criteria, cmdopts):
            _logger.debug("Skip running inter-experiment model '%s'", str(model))
            continue

        # Run the model
        _logger.debug("Run inter-experiment model '%s'", str(model))

        dfs = model.run(criteria, cmdopts, pathset)

        for df, csv_stem in zip(dfs, targets):
            path_stem = pathset.model_interexp_root / csv_stem
            utils.dir_create_checked(path_stem.parent, exist_ok=True)

            # Write model .csv file
            storage.df_write(
                df,
                path_stem.with_suffix(config.MODELS_EXT["model"]),
                "storage.csv",
                index=True,
            )

            idx = dfs.index(df)
            with utils.utf8open(
                path_stem.with_suffix(config.MODELS_EXT["legend"]), "w"
            ) as f:
                f.write(legend[idx])


__all__ = ["proc_batch_exp"]
