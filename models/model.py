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
Base classes for the mathematical models that SIERRA can generate and add to any configured graph
during stage 4.
"""

import pandas as pd
import implements


class IConcreteModel(implements.Interface):
    def run(self, cmdopts: dict, criteria, exp_num: int) -> pd.DataFrame:
        """
        Run the model and generate a dataframe from the results. If this is a 1D model, then the
        dataframe should be a single row. If this is a 2D model, then the dataframe should be a NxM
        grid (with N not necessarily equal to M).
        """

    def run_for_exp(self, i: int) -> bool:
        """
        Some models may only be valid/make sense to run for a subset of experiments within a batch,
        so experiments can be selectively executed with this function.
        """


__api__ = ['IConcreteModel']
