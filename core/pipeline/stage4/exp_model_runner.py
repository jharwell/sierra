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
Classes for running project-specific models in a general purpose way within a batched experiment.
"""
# Core packages
import os
import copy
import logging

# 3rd party packages

# Project packages
import core.utils
import core.variables.batch_criteria as bc
from core.graphs.batch_ranged_graph import BatchRangedGraph
from models.execution_record import ExecutionRecord


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

        records = ExecutionRecord()

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
                if not model.run_for_exp(criteria, cmdopts, i) or model.previously_run(i):
                    logging.debug("Skip running intra-experiment model '%s' for exp%s",
                                  model.config['pyfile'],
                                  i)
                    records.intra_record_add(model.config['pyfile'], i)
                    continue
                elif records.intra_record_exists(model.config['pyfile'], i):
                    logging.debug("Retrieve results for previously run intra-experiment model '%s' for exp%s",
                                  model.config['pyfile'],
                                  i)
                    continue

                # Run the model
                logging.debug("Run intra-experiment model '%s' for exp%s",
                              model.config['pyfile'],
                              i)
                df = model.run(cmdopts, criteria, i)
                path_stem = os.path.join(cmdopts['exp_model_root'],
                                         model.target_csv_stem())

                # 1D dataframe -> line graph with legend
                if len(df.index) == 1:
                    # Write model legend file so the generated graph can find it
                    with open(path_stem + '.legend', 'w') as f:
                        f.write(model.legend_name())

                # Write model .csv file
                core.utils.pd_csv_write(df, path_stem + '.model', index=False)


class InterExpModelRunner:
    """
    Runs all enabled inter-experiment models in a batch.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self, cmdopts: dict, models: list) -> None:
        self.cmdopts = cmdopts
        self.models = models

    def __call__(self,
                 main_config: dict,
                 criteria: bc.IConcreteBatchCriteria) -> None:

        cmdopts = copy.deepcopy(self.cmdopts)

        cmdopts['batch_collate_root'] = os.path.abspath(os.path.join(self.cmdopts['batch_output_root'],
                                                                     main_config['sierra']['collate_csv_leaf']))
        cmdopts["batch_collate_graph_root"] = os.path.abspath(os.path.join(self.cmdopts['batch_graph_root'],
                                                                           main_config['sierra']['collate_graph_leaf']))
        core.utils.dir_create_checked(cmdopts['batch_model_root'], exist_ok=True)
        core.utils.dir_create_checked(cmdopts['batch_collate_graph_root'], exist_ok=True)

        records = ExecutionRecord()

        for model in self.models:
            if not model.run_for_batch(criteria, cmdopts):
                logging.debug("Skip running inter-experiment model '%s",
                              model.config['pyfile'])
                records.inter_record_add(model.config['pyfile'])
                continue
            elif records.inter_record_exists(model.config['pyfile']):
                logging.debug("Retrieve results for previously run inter-experiment model '%s'",
                              model.config['pyfile'])
                continue

            # Run the model
            logging.debug("Run inter-experiment model '%s'", model.config['pyfile'])

            df = model.run(cmdopts, criteria)
            path_stem = os.path.join(cmdopts['batch_model_root'], model.target_csv_stem())

            # Write model .csv file
            core.utils.pd_csv_write(df, path_stem + '.csv', index=False)

            if not os.path.exists(os.path.join(cmdopts['batch_collate_root'],
                                               model.target_csv_stem() + '.csv')):
                logging.info("Generate graph for unattached model '%s'", model.config['pyfile'])
                BatchRangedGraph(input_fpath=path_stem + '.csv',
                                 output_fpath=os.path.join(cmdopts["batch_collate_graph_root"],
                                                           model.target_csv_stem() + '.png'),
                                 title='Model Error',
                                 xlabel=criteria.graph_xlabel(cmdopts),
                                 ylabel='error',
                                 xticks=criteria.graph_xticks(cmdopts)).generate()

            else:
                # Write model .csv file
                core.utils.pd_csv_write(df, path_stem + '.model', index=False)

                # 1D dataframe -> line graph with legend
                if len(df.index) == 1:
                    # Write model legend file so the generated graph can find it
                    with open(path_stem + '.legend', 'w') as f:
                        f.write(model.legend_name())