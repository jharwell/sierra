# Copyright 2021 John Harwell, All rights reserved.
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
Classes for generating common XML changes for all :term:`ROS`-based
:term:`Platforms <Platform>`; i.e., changes which are platform-specific,
but applicable to all projects using ROS.
"""
# Core packages
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core.xml import XMLLuigi, XMLWriterConfig
from sierra.core.experiment.spec import ExperimentSpec
import sierra.core.utils as scutils
from sierra.core import types, config
import sierra.core.ros.variables.time_setup as ts


class ROSExpDefGenerator():
    """
    Attributes:
        controller: The controller used for the experiment.
        cmdopts: Dictionary of parsed cmdline parameters.
    """

    def __init__(self,
                 spec: ExperimentSpec,
                 controller: str,
                 cmdopts: types.Cmdopts,
                 **kwargs) -> None:
        self.controller = controller
        self.spec = spec
        self.cmdopts = cmdopts
        self.template_input_file = kwargs['template_input_file']
        self.kwargs = kwargs
        self.ros_param_server = False
        self.logger = logging.getLogger(__name__)

    def generate(self) -> XMLLuigi:
        """
        Generates XML changes to simulation input files that are common to all
        experiments.

        ROS requires up to 2 input files per run:

       - The launch file containing robot definitions, world definitions (for
         simulations only).

       - The parameter file for project code (optional).

       Putting everything in 1 file would require extensively using the
       ROS parameter server which does NOT accept parameters specified in
       XML--only YAML. So requiring some conventions on the .launch
       input file seemed more reasonable.

        """
        exp_def = XMLLuigi(input_fpath=self.template_input_file)
        launch_ext = config.kROS['launch_file_ext']
        params_ext = config.kROS['param_file_ext']
        if exp_def.has_tag('./params'):
            self.logger.debug("Using separate %s and %s files",
                              launch_ext,
                              params_ext)

            exp_def.write_config_set(XMLWriterConfig({'./launch': launch_ext,
                                                      './params': params_ext}))

        else:
            self.logger.debug("Using ROS parameter server/single %s file",
                              launch_ext)
            exp_def.write_config_set(XMLWriterConfig({'./launch': launch_ext}))
            self.ros_param_server = True

        # Setup experiment
        self._generate_experiment(exp_def)

        # Setup simulation time
        self._generate_time(exp_def)

        return exp_def

    def _generate_time(self, exp_def: XMLLuigi) -> None:
        """
        Generate XML changes to setup simulation time parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        self.logger.debug("Applying time_setup=%s", self.cmdopts['time_setup'])

        tsetup = ts.factory(self.cmdopts["time_setup"], self.ros_param_server)()
        rms, adds, chgs = scutils.apply_to_expdef(tsetup, exp_def)

        # Write time setup info to file for later retrieval
        scutils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)

    def _generate_experiment(self, exp_def: XMLLuigi) -> None:
        """
        Generate XML tag changes to setup basic experiment parameters.

        Does not write generated changes to the simulation definition pickle
        file.
        """
        self.logger.debug("Generating experiment changes (all runs)")

        if not self.ros_param_server:
            exp_def.tag_add("./params", "sierra", {}, False)
            exp_def.tag_add("./params/sierra",
                            "experiment",
                            {
                                "length": "-1",
                                "ticks_per_sec": "-1"
                            })
        else:
            exp_def.tag_add("./launch",
                            "param",
                            {
                                "name": "sierra/experiment/length",
                                "value": "-1",
                            })
            exp_def.tag_add("./launch",
                            "param",
                            {
                                "name": "sierra/experiment/ticks_per_sec",
                                "value": "-1",
                            })

        # Add SIERRA time keeper
        exp_def.tag_add("./launch",
                        "node",
                        {
                            "name": "sierra_timekeeper",
                            "pkg": "sierra_rosbridge",
                            "type": "sierra_timekeeper.py",
                            "required": "true"
                        },
                        False)


class ROSExpRunDefUniqueGenerator:
    """
    Generate XML changes unique to a experimental run within an experiment
    targeting a :term:`ROS`-based platform.
    ARGoS.

    These include:

    - Random seeds for each :term:`Experimental Run`.

    - Unique parameter file for each :term:`Experimental Run`.
    """

    def __init__(self,
                 run_num: int,
                 run_output_path: str,
                 launch_stem_path: str,
                 random_seed: int,
                 cmdopts: types.Cmdopts) -> None:

        self.run_output_path = run_output_path
        self.launch_stem_path = launch_stem_path
        self.random_seed = random_seed
        self.cmdopts = cmdopts
        self.run_num = run_num
        self.logger = logging.getLogger(__name__)

    def generate(self, exp_def: XMLLuigi):
        # Setup random seed
        self._generate_random(exp_def)

        # Setup parameter file
        self._generate_paramfile(exp_def)

    def _generate_random(self, exp_def: XMLLuigi) -> None:
        """Generate XML changes for random seeding for a specific :term:`Experimental
        Run` in an :term:`Experiment` during the input generation process.

        """
        self.logger.trace("Generating random seed changes for run%s",
                          self.run_num)

        # Set the random seed in the input file
        if exp_def.has_tag('./params'):
            exp_def.attr_add("./params/sierra/experiment",
                             "random_seed",
                             str(self.random_seed))
        else:
            exp_def.tag_add("./launch",
                            "param",
                            {
                                "name": "sierra/experiment/random_seed",
                                "value": str(self.random_seed)
                            })

    def _generate_paramfile(self, exp_def: XMLLuigi) -> None:
        """Generate XML changes for the parameter for for a specific
        :term:`Experimental Run` in an :term:`Experiment` during the input
        generation process.

        """
        self.logger.trace("Generating parameter file changes for run%s",
                          self.run_num)

        exp_def.tag_add("./launch",
                        "param",
                        {
                            "name": "sierra/experiment/param_file",
                            "value": self.launch_stem_path + config.kROS['param_file_ext']
                        })


__api__ = [
    'ROSExpDefGenerator',
    'ROSExpRunDefUniqueGenerator'
]
