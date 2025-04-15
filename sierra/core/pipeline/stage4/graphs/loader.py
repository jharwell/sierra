# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Functionality for loading stage 4 configuration from YAML.
"""
# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core import types, utils

_logger = logging.getLogger(__name__)


def load_config(cmdopts: types.Cmdopts) -> tp.Dict[str, types.YAMLDict]:
    """Load YAML configuration for :term:`Project` graphs to be generated.

       Load YAML configuratoin for graphs.

       This includes:

       - intra-experiment linegraphs

       - inter-experiment linegraphs

       - intra-experiment heatmaps

       - inter-experiment heatmaps (bivariate batch criteria only)

       Returns:

           Dictionary of loaded configuration with keys for ``intra_LN,
           inter_LN, intra_HM, inter_HM``.

      This function can be extended/overriden using a :term:`Project` hook. See
      :ref:`tutorials/project/hooks` for details.

    """
    inter_LN_config = {}
    intra_LN_config = {}
    intra_HM_config = {}
    inter_HM_config = {}

    root = pathlib.Path(cmdopts['project_config_root'])
    project_inter_LN = root / 'inter-graphs-line.yaml'
    project_intra_LN = root / 'intra-graphs-line.yaml'
    project_intra_HM = root / 'intra-graphs-hm.yaml'
    project_inter_HM = root / 'inter-graphs-hm.yaml'

    if utils.path_exists(project_intra_LN):
        _logger.info("Intra-experiment linegraph config for project '%s' from %s",
                     cmdopts['project'],
                     project_intra_LN)
        with utils.utf8open(project_intra_LN) as f:
            intra_LN_config = yaml.load(f, yaml.FullLoader)

    if utils.path_exists(project_inter_LN):
        _logger.info("Inter-experiment linegraph config for project '%s' from %s",
                     cmdopts['project'],
                     project_inter_LN)
        with utils.utf8open(project_inter_LN) as f:
            inter_LN_config = yaml.load(f, yaml.FullLoader)

    if utils.path_exists(project_intra_HM):
        _logger.info("Intra-experiment heatmap config for project '%s' from %s",
                     cmdopts['project'],
                     project_intra_HM)
        with utils.utf8open(project_intra_HM) as f:
            intra_HM_config = yaml.load(f, yaml.FullLoader)

    if utils.path_exists(project_inter_HM):
        _logger.info("Inter-experiment heatmap config for project '%s' from %s",
                     cmdopts['project'],
                     project_inter_HM)
        with utils.utf8open(project_inter_HM) as f:
            inter_HM_config = yaml.load(f, yaml.FullLoader)

    return {
        'intra_LN': intra_LN_config,
        'intra_HM': intra_HM_config,
        'inter_LN': inter_LN_config,
        'inter_HM': inter_HM_config
    }


__all__ = [
    'load_config'
]
