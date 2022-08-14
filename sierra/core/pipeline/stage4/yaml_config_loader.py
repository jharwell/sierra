# Copyright 2021 John Harwell, All rights reserved.
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
import yaml

# Project packages
from sierra.core import types, utils


class YAMLConfigLoader():
    """Load YAML configuration for :term:`Project` graphs to be generated.

    This class can be extended/overriden using a :term:`Project` hook. See
    :ref:`ln-sierra-tutorials-project-hooks` for details.

    Attributes:
        logger: The handle to the logger for this class. If you extend this
                class, you should save/restore this variable in tandem with
                overriding it in order to get loggingmessages have unique
                logger names between this class and your derived class, in order
                to reduce confusion.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self, cmdopts: types.Cmdopts) -> tp.Dict[str, types.YAMLDict]:
        """
        Load YAML configuratoin for graphs.

        This includes:

        - intra-experiment linegraphs

        - inter-experiment linegraphs

        - intra-experiment heatmaps

        - inter-experiment heatmaps (bivariate batch criteria only)

        Returns:

            Dictionary of loaded configuration with keys for ``intra_LN,
            inter_LN, intra_HM, inter_HM``.
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
            self.logger.info("Intra-experiment linegraph config for project '%s' from %s",
                             cmdopts['project'],
                             project_intra_LN)
            with utils.utf8open(project_intra_LN) as f:
                intra_LN_config = yaml.load(f, yaml.FullLoader)

        if utils.path_exists(project_inter_LN):
            self.logger.info("Inter-experiment linegraph config for project '%s' from %s",
                             cmdopts['project'],
                             project_inter_LN)
            with utils.utf8open(project_inter_LN) as f:
                inter_LN_config = yaml.load(f, yaml.FullLoader)

        if utils.path_exists(project_intra_HM):
            self.logger.info("Intra-experiment heatmap config for project '%s' from %s",
                             cmdopts['project'],
                             project_intra_HM)
            with utils.utf8open(project_intra_HM) as f:
                intra_HM_config = yaml.load(f, yaml.FullLoader)

        if utils.path_exists(project_inter_HM):
            self.logger.info("Inter-experiment heatmap config for project '%s' from %s",
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


__api__ = [
    'YAMLConfigLoader'
]
