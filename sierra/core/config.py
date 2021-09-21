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

# 3rd party packages
import matplotlib as mpl
import matplotlib.pyplot as plt


# Project packages

################################################################################
# Matplotlib Configuration
################################################################################
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.rcParams['axes.formatter.limits'] = (-4, 4)

# Use latex to render all math, so that it matches how the math renders in papers.
mpl.rcParams['text.usetex'] = True

# mpl.rcParams["axes.prop_cycle"] = plt.cycler("color", plt.cm.tab20.colors)

# Turn off MPL messages when the log level is set to DEBUG. Otherwise you get HUNDREDS.
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Set MPL backend (headless for non-interactive use)
mpl.use('Agg')

# Set MPL style
mpl.style.use('seaborn-colorblind')

################################################################################
# General Configuration
################################################################################

kImageExt = '.png'

kRenderFormat = '.mp4'

kPickleExt = '.pkl'

kPickleLeaf = 'exp_def' + kPickleExt

kARGoSFramesLeaf = 'frames'

kGraphDPI = 100

kGraphBaseSize = 10.0  # inches

kGraphTextSizeSmall = {
    'title': 24,
    'xyz_label': 18,
    'tick_label': 12,
    'legend_label': 18
}
kGraphTextSizeLarge = {
    'title': 36,
    'xyz_label': 24,
    'tick_label': 24,
    'legend_label': 32
}

kStatsExtensions = {
    # The default
    'mean': '.csv',

    # For calculating 95% confidence intervals
    'stddev': '.stddev',

    # For calculating box and whisker plots
    'min': '.min',
    'max': '.max',
    'median': '.median',
    'q1': '.q1',
    'q3': '.q3',
    'whislo': '.whislo',
    'whishi': '.whishi',
    'cilo': '.cilo',
    'cihi': '.cihi',
}

kARGoS = {
    'duration': 5000,  # seconds
    'ticks_per_second': 5,
    'min_version': 'beta53'
}

kSimulationData = {
    # Default # datapoints in each .csv of one-dimensional data.
    'n_datapoints_1D': 50
}