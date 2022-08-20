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
"""Interface classes for the mathematical models framework in SIERRA.

Models can be run and added to any configured graph during stage 4.

"""

# Core packages
import typing as tp

# 3rd party packages
import pandas as pd
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types


class IConcreteIntraExpModel1D(implements.Interface):
    """Interface for one-dimensional models.

    1D models are those that generate a single time series from zero or more
    experimental outputs within a *single* :term:`Experiment`. Models will be
    rendered as lines on a
    :class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`. Models
    "target" one or more CSV files which are already configured to be generated,
    and will show up as additional lines on the generated graph.

    """

    def run(self,
            criteria: bc.IConcreteBatchCriteria,
            exp_num: int,
            cmdopts: types.Cmdopts) -> tp.List[pd.DataFrame]:
        """Run the model and generate a list of dataframes.

        Each dataframe can (potentially) target different graphs. All dataframes
        should contain a single column named ``model``, with each row of the
        dataframe containing the model prediction at the :term:`Experimental
        Run` interval corresponding to the row (e.g., row 7 contains the model
        prediction for interval 7).

        """
        raise NotImplementedError

    def run_for_exp(self,
                    criteria: bc.IConcreteBatchCriteria,
                    cmdopts: types.Cmdopts,
                    exp_num: int) -> bool:
        """
        Determine if the model should be run for the specified experiment.

        Some models may only be valid/make sense to run for a subset of
        experiments within a batch, so models can be selectively executed with
        this function.
        """
        raise NotImplementedError

    def target_csv_stems(self) -> tp.List[str]:
        """Return a list of CSV file stems that the model is targeting.

         File stem = path sans directory path and extension.
        """
        raise NotImplementedError

    def legend_names(self) -> tp.List[str]:
        """Compute names for the model predictions for the target graph legend.

        Applicable to:

        - :class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`

        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        Return the UUID string of the model name.
        """
        raise NotImplementedError


class IConcreteIntraExpModel2D(implements.Interface):
    """Interface for two-dimensional models.

    2D models are those that generate a list of 2D matrices, forming a 2D time
    series. Can be built from zero or more experimental outputs from a *single*
    :term:`Experiment`. Models "target" one or more CSV files which are already
    configured to be generated, and will show up as additional lines on the
    generated graph.

    """

    def run(self,
            criteria: bc.IConcreteBatchCriteria,
            exp_num: int,
            cmdopts: types.Cmdopts) -> tp.List[pd.DataFrame]:
        """Run the model and generate a list of dataframes.

        Each dataframe can (potentially) target a different graph. Each
        dataframe should be a NxM grid (with N not necessarily equal to M). All
        dataframes do not have to be the same dimensions. The index of a given
        dataframe in a list should correspond to the model value for
        interval/timestep.

        """
        raise NotImplementedError

    def run_for_exp(self,
                    criteria: bc.IConcreteBatchCriteria,
                    cmdopts: types.Cmdopts,
                    exp_num: int) -> bool:
        """Determine if a model should be run for the specified experiment.

        Some models may only be valid/make sense to run for a subset of
        experiments within a batch, so models can be selectively executed with
        this function.

        """
        raise NotImplementedError

    def target_csv_stems(self) -> tp.List[str]:
        """Return a list of CSV file stems that the model is targeting.

         File stem = path sans directory path and extension.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        Return the UUID string of the model name.
        """
        raise NotImplementedError


class IConcreteInterExpModel1D(implements.Interface):
    """Interface for one-dimensional models.

    1D models are those that generate a single time series from any number of
    experimental outputs across *all* experiments in a batch(or from another
    source). Models will be rendered as lines on a
    :class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`.  Models
    "target" one or more CSV files which are already configured to be generated,
    and will show up as additional lines on the generated graph.

    """

    def run(self,
            criteria: bc.IConcreteBatchCriteria,
            cmdopts: types.Cmdopts) -> tp.List[pd.DataFrame]:
        """Run the model and generate list of dataframes.

        Each dataframe can (potentially) target a different graph. Each
        dataframe should contain a single row, with one column for the predicted
        value of the model for each experiment in the batch.

        """
        raise NotImplementedError

    def run_for_batch(self,
                      criteria: bc.IConcreteBatchCriteria,
                      cmdopts: types.Cmdopts) -> bool:
        """
        Determine if the model should be run for the specified batch criteria.

        Some models may only be valid/make sense to run for some batch criteria,
        so models can be selectively executed with this function.
        """
        raise NotImplementedError

    def target_csv_stems(self) -> tp.List[str]:
        """Return a list of CSV file stems that the model is targeting.

         File stem = path sans directory path and extension.
        """
        raise NotImplementedError

    def legend_names(self) -> tp.List[str]:
        """Compute names for the model predictions for the target graph legend.

        Applicable to:

        - ~sierra.core.graphs.summary_line_graph.SummaryLineGraph`

        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        Return the UUID string of the model name.
        """
        raise NotImplementedError


__api__ = ['IConcreteIntraExpModel1D',
           'IConcreteIntraExpModel2D',
           'IConcreteInterExpModel1D']
