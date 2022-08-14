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
Contains all SIERRA hard-coded configuration in one place.
"""

# Core packages
import logging
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types

################################################################################
# Matplotlib Configuration
################################################################################


def mpl_init():
    # Turn off MPL messages when the log level is set to DEBUG or
    # higher. Otherwise you get HUNDREDS. Must be before import to suppress
    # messages which occur during import.
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    import matplotlib as mpl

    mpl.rcParams['lines.linewidth'] = 3
    mpl.rcParams['lines.markersize'] = 10
    mpl.rcParams['figure.max_open_warning'] = 10000
    mpl.rcParams['axes.formatter.limits'] = (-4, 4)

    # Use latex to render all math, so that it matches how the math renders in
    # papers.
    mpl.rcParams['text.usetex'] = True

    # Set MPL backend (headless for non-interactive use). Must be BEFORE
    # importing pyplot reduce import loading time.
    mpl.use('agg')

    import matplotlib.pyplot as plt

    # Set MPL style
    plt.style.use('seaborn-colorblind')


# Actually initialize matplotlib
mpl_init()

################################################################################
# General Configuration
################################################################################


kImageExt = '.png'

kRenderFormat = '.mp4'

kPickleExt = '.pkl'
kPickleLeaf = 'exp_def' + kPickleExt
kRandomSeedsLeaf = "seeds" + kPickleExt

kGraphDPI = 100

kGraphBaseSize = 10.0  # inches

kGraphTextSizeSmall: types.IntDict = {
    'title': 24,
    'xyz_label': 18,
    'tick_label': 12,
    'legend_label': 18
}

kGraphTextSizeLarge: types.IntDict = {
    'title': 36,
    'xyz_label': 24,
    'tick_label': 24,
    'legend_label': 32
}

# These are the file extensions that files read/written by a given storage
# plugin should have. Once processed by SIERRA they are written out as CSV files
# with new extensions contextualizing them.
kStorageExt: types.StrDict = {
    'csv': '.csv'
}

kStats: tp.Dict[str, types.StatisticsSpec] = {
    # The default for averaging
    'mean': types.StatisticsSpec({'mean': '.mean'}),

    # For calculating 95% confidence intervals
    'conf95': types.StatisticsSpec({'stddev': '.stddev'}),

    # For calculating box and whisker plots
    'bw': types.StatisticsSpec({'median': '.median',
                                'q1': '.q1',
                                'q3': '.q3',
                                'whislo': '.whislo',
                                'whishi': '.whishi',
                                'cilo': '.cilo',
                                'cihi': '.cihi'
                                })
}

kModelsExt: types.StrDict = {
    'model': '.model',
    'legend': '.legend'
}

kRendering = {
    'argos': {
        'frames_leaf': 'frames',
    }
}
kARGoS: tp.Dict[str, tp.Any] = {
    'physics_iter_per_tick': 10,
    'min_version': 'beta53',
    'launch_cmd': 'argos3',
    'launch_file_ext': '.argos',
    'n_secs_per_run': 5000,  # seconds
    'n_ticks_per_sec': 5,

    # These are the cell sizes for use with the spatial_hash method for the
    # dynamics2D engine. Since that method should only be used with lots of
    # robots (per the docs), we set a cell a little larger than the robot.
    'spatial_hash2D': {
        'foot-bot': 0.5,
        'e-puck': 0.5,
    }
}


kROS: types.SimpleDict = {
    'launch_cmd': 'roslaunch',
    'launch_file_ext': '.launch',
    'param_file_ext': '.params',
    'n_ticks_per_sec': 5,
    'n_secs_per_run': 1000,  # seconds
    'port_base': 11235,
    'inter_run_pause': 60  # seconds
}

kYAML = types.YAMLConfigFileSpec(main='main.yaml',
                                 controllers='controllers.yaml',
                                 models='models.yaml',
                                 stage5='stage5.yaml')

kGazebo = {
    'launch_cmd': 'gazebo',
    'min_version': '11.0.0',
    'physics_iter_per_tick': 1000,

}

kGNUParallel:  types.StrDict = {
    'cmdfile_stem': 'commands',
    'cmdfile_ext': '.txt'
}

kExperimentalRunData = {
    # Default # datapoints in each .csv of one-dimensional data.
    'n_datapoints_1D': 50
}

kPlatform = {
    'ping_timeout': 10  # seconds
}
