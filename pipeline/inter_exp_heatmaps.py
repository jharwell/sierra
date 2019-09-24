"""
Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

from perf_measures.heatmaps import PerformanceDensityHeatmap


class InterExpHeatmaps:
    """
    Generates heatmaps from collated .csv data within a batched experiment.
    """

    def generate(self, cmdopts, inter_perf_csv, batch_criteria):
        PerformanceDensityHeatmap(cmdopts, inter_perf_csv).generate(batch_criteria)
