"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

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

from pipeline.stage1 import PipelineStage1
from pipeline.stage2 import PipelineStage2
from pipeline.stage3 import PipelineStage3
from pipeline.stage4 import PipelineStage4
from pipeline.stage5 import PipelineStage5


class ExpPipeline:

    """
    Automation for running ARGoS robotic simulation experiments in parallel

    Implements the following pipeline for single OR batched experiments:

    1. Generate a set of XML configuration files from a template suitable for
       input into ARGoS that contain user-specified modifications.
    2. Run the specified  # of experiments in parallel using GNU Parallel on
       the provided set of hosts on MSI (or on a single personal computer for testing).
    3. Average the .csv results of the simulation runs together.
    4. Generate a user-defined set of graphs based on the averaged results for each
       experiment, and possibly across experiments for batches.
    5. Compare controllers that have been tested with the same experiment batch across different
       performance measures.
    """

    def __init__(self, args, input_generator):
        self.args = args
        self.cmdopts = {
            'output_root': self.args.output_root,
            'graph_root': self.args.graph_root,
            'sierra_root': self.args.sierra_root,
            'generation_root': self.args.generation_root,
            'generator': self.args.generator,
            'envc_cs_method': self.args.envc_cs_method,
            'with_hists': self.args.with_hists,
            'plot_applied_vc': self.args.plot_applied_vc,
            'perf_measures': self.args.perf_measures,
            'reactivity_cs_method': self.args.reactivity_cs_method,
            'adaptability_cs_method': self.args.adaptability_cs_method,
            'exp_graphs': self.args.exp_graphs,
            'template_config_file': self.args.template_config_file,
            'time_setup': self.args.time_setup,
            'batch_exp_range': self.args.batch_exp_range,
            'exec_method': self.args.exec_method
        }
        if self.args.batch_criteria is None:
            self.cmdopts['criteria_category'] = None
            self.cmdopts['criteria_def'] = None
        else:
            self.cmdopts['criteria_category'] = self.args.batch_criteria.split('.')[0]
            self.cmdopts['criteria_def'] = '.'.join(self.args.batch_criteria.split('.')[1:])

        self.input_generator = input_generator

    def generate_inputs(self):
        PipelineStage1(self.cmdopts, self.input_generator).run()

    def run_experiments(self):
        PipelineStage2(self.cmdopts).run()

    def average_results(self):
        PipelineStage3(self.cmdopts).run()

    def generate_graphs(self):
        PipelineStage4(self.cmdopts).run()

    def compare_controllers(self):
        if self.args.comp_controllers is not 'all':
            PipelineStage5(self.cmdopts, self.args.comp_controllers).run()
        else:
            PipelineStage5(self.cmdopts, None).run()

    def run(self):

        if 1 in self.args.pipeline:
            self.generate_inputs()

        if 2 in self.args.pipeline:
            self.run_experiments()

        if 3 in self.args.pipeline:
            self.average_results()

        if 4 in self.args.pipeline:
            self.generate_graphs()

        # not part of default pipeline
        if 5 in self.args.pipeline:
            self.compare_controllers()
