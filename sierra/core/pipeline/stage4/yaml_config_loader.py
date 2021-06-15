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
import os
import logging
import typing as tp

# 3rd party packages
import yaml

# Project packages
import sierra.core.utils


class YAMLConfigLoader():
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self, cmdopts: tp.Dict[str, tp.Any]) -> tp.Dict[str, tp.Dict[str, str]]:
        inter_LN_config = {}
        intra_LN_config = {}
        intra_HM_config = {}

        project_inter_LN = os.path.join(cmdopts['project_config_root'],
                                        'inter-graphs-line.yaml')
        project_intra_LN = os.path.join(cmdopts['project_config_root'],
                                        'intra-graphs-line.yaml')
        project_intra_HM = os.path.join(cmdopts['project_config_root'],
                                        'intra-graphs-hm.yaml')

        if sierra.core.utils.path_exists(project_intra_LN):
            self.logger.info("Loading intra-experiment linegraph config for project '%s'",
                             cmdopts['project'])
            inter_LN_config = yaml.load(open(project_intra_LN), yaml.FullLoader)

        if sierra.core.utils.path_exists(project_inter_LN):
            self.logger.info("Loading inter-experiment linegraph config for project '%s'",
                             cmdopts['project'])
            intra_LN_config = yaml.load(open(project_inter_LN), yaml.FullLoader)

        if sierra.core.utils.path_exists(project_intra_HM):
            self.logger.info("Loading intra-experiment heatmap config for project '%s'",
                             cmdopts['project'])
            intra_HM_config = yaml.load(open(project_intra_HM), yaml.FullLoader)

        return {
            'intra_LN': intra_LN_config,
            'intra_HM': intra_HM_config,
            'inter_LN': inter_LN_config
        }
