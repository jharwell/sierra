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

mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.rcParams['axes.formatter.limits'] = (-4, 4)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
mpl.use('Agg')

# Project packages

kImageExt = '.png'

kRenderFormat = '.mp4'

kPickleExt = '.pkl'

kPickleLeaf = 'exp_def' + kPickleExt

kGraphDPI = 100

kGraphBaseSize = 5.0  # inches

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

    'bxp': '.bxp' + kPickleExt,
}
