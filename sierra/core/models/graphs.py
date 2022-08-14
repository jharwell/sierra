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
"""
Graphs which can always be generated, irrespective of model specifics.

For example, you can always compare the model value to the empirical value, and
plot the difference as error.
"""
# Core packages
import os
import pathlib

# 3rd party packages

# Project packages
from sierra.core.graphs.heatmap import HeatmapSet
from sierra.core import utils, config, storage


class IntraExpModel2DGraphSet():
    """
    Generates 4 :class:`~sierra.core.graphs.heatmap.Heatmap` plots.

    - One for the empirical data
    - One for the stddev of the empirical data
    - One for the model prediction
    - One for the difference between the model and the empirical data
    """
    @staticmethod
    def model_exists(exp_model_root: pathlib.Path, target_stem: str):
        leaf = target_stem + config.kModelsExt['model']
        return utils.path_exists(exp_model_root / leaf)

    def __init__(self,
                 exp_stat_root: pathlib.Path,
                 exp_model_root: pathlib.Path,
                 exp_graph_root: pathlib.Path,
                 target_stem: str,
                 target_title: str,
                 **kwargs):
        self.exp_stat_root = exp_stat_root
        self.exp_model_root = exp_model_root
        self.exp_graph_root = exp_graph_root
        self.target_stem = target_stem
        self.target_title = target_title
        self.kwargs = kwargs

    def generate(self):
        stat_path = self.exp_stat_root / self.target_stem
        graph_path = self.exp_graph_root / self.target_stem
        model_path = self.exp_model_root / self.target_stem

        data_ipath = stat_path.with_suffix(config.kStats['mean'].exts['mean'])

        data_opath = self.exp_graph_root / \
            (self.target_stem + '-HM').with_suffix(config.kImageExt)

        stddev_ipath = stat_path.with_suffix(config.kStats['conf95'].exts['stddev'])
        stddev_opath = graph_path.with_name(
            self.target_stem + '-HM-stddev' + config.kImageExt)

        model_ipath = model_path.with_suffix(config.kModelsExt['model'])
        model_opath = graph_path.with_name(
            self.target_stem + '-HM-model' + config.kImageExt)

        model_error_ipath = model_path.with_name(
            self.target_stem + '-HM-model-error' + config.kStats['mean'].exts['mean'])
        model_error_opath = model_path.with_name(
            self.target_stem + '-HM-model-error' + config.kImageExt)

        # Write the error .csv to the filesystem
        reader = storage.DataFrameReader('storage.csv')
        writer = storage.DataFrameWriter('storage.csv')
        data_df = reader(data_ipath)
        model_df = reader(model_ipath)
        writer(model_df - data_df, model_error_ipath, index=False)

        HeatmapSet(ipaths=[data_ipath, stddev_ipath, model_ipath, model_error_ipath],
                   opaths=[data_opath, stddev_opath,
                           model_opath, model_error_opath],
                   titles=[self.target_title,
                           self.target_title + ' (Stddev)',
                           self.target_title + ' (Model)',
                           self.target_title + ' (Model Error)'],
                   xlabel='X',
                   ylabel='Y',
                   **self.kwargs).generate()
