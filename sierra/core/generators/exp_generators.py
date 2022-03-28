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
"""Experiment generation classes, generating definitions common to all batch
experiments, as well as definitions generated by the
controller+scenario. Generated definitions from batch criteria are not handled
here.

"""

# Core packages
import os
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages
import sierra.core.generators.generator_factory as gf
import sierra.core.xml
from sierra.core.experiment.spec import ExperimentSpec
from sierra.core import types
import sierra.core.variables.batch_criteria as bc


class BatchExpDefGenerator:
    """Generate experiment definitions for a :term:`Batch Experiment`.

    Does not create the batch experiment after generation.

    Attributes:

        batch_config_template: Path (relative to current dir or absolute) to the
                               root template XML configuration file.

        batch_input_root: Root directory for all generated XML input files all
                               experiments should be stored (relative to current
                               dir or absolute). Each experiment will get a
                               directory within this root to store the xml input
                               files for the set of :term:`Experimental Runs
                               <Experimental Run>` comprising an
                               :term:`Experiment`; directory name determined by
                               the batch criteria used.

        batch_output_root: Root directory for all experiment outputs (relative
                           to current dir or absolute). Each experiment will get
                           a directory 'exp<n>' in this directory for its
                           outputs.

        criteria: :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  derived object instance created from cmdline definition.

        controller_name: Name of controller generator to use.

        scenario_basename: Name of scenario generator to use.

    """

    def __init__(self,
                 criteria: bc.IConcreteBatchCriteria,
                 controller_name: str,
                 scenario_basename: str,
                 cmdopts: types.Cmdopts) -> None:
        self.batch_config_template = cmdopts['template_input_file']
        assert os.path.isfile(self.batch_config_template),\
            "'{0}' is not a valid file".format(self.batch_config_template)

        self.batch_config_leaf, _ = os.path.splitext(
            os.path.basename(self.batch_config_template))
        self.batch_config_extension = None

        self.batch_input_root = os.path.abspath(cmdopts['batch_input_root'])
        self.batch_output_root = os.path.abspath(cmdopts['batch_output_root'])

        self.controller_name = controller_name
        self.scenario_basename = scenario_basename
        self.criteria = criteria
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def generate_defs(self) -> tp.List[sierra.core.xml.XMLLuigi]:
        """
        Generates and returns a list of experiment definitions (one for each
        experiment in the batch), which can used to create the batch
        experiment.
        """
        chgs = self.criteria.gen_attr_changelist()
        adds = self.criteria.gen_tag_addlist()

        assert len(chgs) == 0 or len(adds) == 0,\
            "Batch criteria cannot add AND change XML tags"

        if len(chgs) != 0:
            mods_for_batch = chgs
        else:
            mods_for_batch = adds

        # Create and run generators
        defs = []
        for i in range(0, len(mods_for_batch)):
            generator = self._create_exp_generator(i)
            self.logger.debug("Generating scenario+controller changes from generator '%s' for exp%s",
                              self.cmdopts['joint_generator'],
                              i)

            defs.append(generator.generate())

        return defs

    def _create_exp_generator(self, exp_num: int):
        """
        Create the generator for a particular experiment from the
        scenario+controller definitions specified on the command line.

        Arguments:
            exp_num: Experiment number in the batch
        """

        spec = ExperimentSpec(self.criteria, exp_num, self.cmdopts)

        scenario = gf.scenario_generator_create(controller=self.controller_name,
                                                spec=spec,
                                                template_input_file=os.path.join(spec.exp_input_root,
                                                                                 self.batch_config_leaf),
                                                cmdopts=self.cmdopts)

        controller = gf.controller_generator_create(controller=self.controller_name,
                                                    config_root=self.cmdopts['project_config_root'],
                                                    cmdopts=self.cmdopts,
                                                    spec=spec)

        generator = gf.joint_generator_create(scenario=scenario,
                                              controller=controller)
        self.cmdopts['joint_generator'] = generator.joint_name
        return generator


__api__ = [
    'BatchExpDefGenerator',
]
