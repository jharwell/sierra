# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
#
"""
Classes for running project-specific models in a general purpose way within a single experiment in a
batch.
"""

import os
import copy
import logging

import pandas as pd

import core.utils
import core.variables.batch_criteria as bc


class BatchedIntraExpModelRunner:
    """
    Runs all enabled intra-experiment models for all experiments in a batch.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self, cmdopts: dict, models: list) -> None:
        self.cmdopts = cmdopts
        self.models = models

    def __call__(self,
                 main_config: dict,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        exp_to_run = core.utils.exp_range_calc(self.cmdopts,
                                               self.cmdopts['batch_output_root'],
                                               criteria)

        for i, exp in enumerate(exp_to_run):
            exp = os.path.split(exp)[1]
            cmdopts = copy.deepcopy(self.cmdopts)
            cmdopts["exp_input_root"] = os.path.join(self.cmdopts['batch_input_root'], exp)
            cmdopts["exp_output_root"] = os.path.join(self.cmdopts['batch_output_root'], exp)
            cmdopts["exp_graph_root"] = os.path.join(self.cmdopts['batch_graph_root'], exp)
            cmdopts["exp_avgd_root"] = os.path.join(cmdopts["exp_output_root"],
                                                    main_config['sierra']['avg_output_leaf'])
            cmdopts["exp_model_root"] = os.path.join(cmdopts['batch_model_root'], exp)
            core.utils.dir_create_checked(cmdopts['exp_model_root'], exist_ok=True)

            for model in self.models:
                if not model.run_for_exp(i):
                    continue

                logging.debug("Run model '%s' for exp%s", model.config['src']['py'], i)
                df = model.run(cmdopts, criteria, i)
                path = os.path.join(cmdopts['exp_model_root'],
                                    model.config['target']['csv_stem'] + '.model')
                target_df = pd.DataFrame(index=df.index)

                target_df[model.config['target']['col']] = df[model.config['target']['col']]
                core.utils.pd_csv_write(target_df, path, index=False)
