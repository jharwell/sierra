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
import sierra.core.ros.variables.exp_setup as exp


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
        wr_config = XMLWriterConfig([])

        if exp_def.has_tag('./params'):
            self.logger.debug("Using shared XML parameter file")
            wr_config.add({
                'src_root': './params',
                'opath_leaf': config.kROS['param_file_ext'],
                'create_tags': None,
                'dest_parent': None,
                'rename_to': None
            })

        else:
            self.ros_param_server = True

        exp_def.write_config_set(wr_config)

        # Add <master> tag
        if not exp_def.has_tag("./master"):
            exp_def.tag_add(".",
                            "master",
                            {})
        if not exp_def.has_tag("./master/group/[@ns='sierra']"):
            exp_def.tag_add("./master",
                            "group",
                            {
                                'ns': 'sierra'
                            })
        # Add <robot> tag
        if not exp_def.has_tag("./robot"):
            exp_def.tag_add(".",
                            "robot",
                            {})
        if not exp_def.has_tag("./robot/group/[@ns='sierra']"):
            exp_def.tag_add("./robot",
                            "group",
                            {
                                'ns': 'sierra'
                            })

        # Generate core experiment definitions
        self._generate_experiment(exp_def)

        return exp_def

    def _generate_experiment(self, exp_def: XMLLuigi) -> None:
        """
        Generate XML tag changes to setup basic experiment parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        self.logger.debug("Applying exp_setup=%s", self.cmdopts['exp_setup'])

        setup = exp.factory(self.cmdopts["exp_setup"])()
        rms, adds, chgs = scutils.apply_to_expdef(setup, exp_def)

        # Write setup info to file for later retrieval
        scutils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)


class ROSExpRunDefUniqueGenerator:
    """
    Generate XML changes unique to a experimental run within an experiment
    targeting a: term: `ROS`- based platform.
    ARGoS.

    These include:

    - Random seeds for each: term: `Experimental Run`.

    - Unique parameter file for each: term: `Experimental Run`.
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
        return exp_def

    def generate_random(self, exp_def: XMLLuigi) -> None:
        """Generate XML changes for random seeding for a specific: term: `Experimental
        Run` in an: term: `Experiment` during the input generation process.

        """
        self.logger.trace("Generating random seed changes for run%s",
                          self.run_num)

        # Master gets the random seed
        exp_def.tag_add("./master/group/[@ns='sierra']",
                        "param",
                        {
                            "name": "experiment/random_seed",
                            "value": str(self.random_seed)
                        })

        # Each robot gets the random seed
        exp_def.tag_add("./robot/group/[@ns='sierra']",
                        "param",
                        {
                            "name": "experiment/random_seed",
                            "value": str(self.random_seed)
                        })

    def generate_paramfile(self, exp_def: XMLLuigi) -> None:
        """Generate XML changes for the parameter for for a specific
        : term: `Experimental Run` in an: term: `Experiment` during the input
        generation process.

        """
        self.logger.trace("Generating parameter file changes for run%s",
                          self.run_num)

        # Master node gets a copy of the parameter file
        exp_def.tag_add("./master/group/[@ns='sierra']",
                        "param",
                        {
                            "name": "experiment/param_file",
                            "value": self.launch_stem_path + config.kROS['param_file_ext']
                        })

        # Each robot gets a copy of the parameter file
        if not exp_def.has_tag("./robot/group/[@ns='sierra']"):
            exp_def.tag_add("./robot",
                            "group",
                            {
                                "ns": "sierra",
                            })
        exp_def.tag_add("./robot/group/[@ns='sierra']",
                        "param",
                        {
                            "name": "experiment/param_file",
                            "value": self.launch_stem_path + config.kROS['param_file_ext']
                        })


__api__ = [
    'ROSExpDefGenerator',
    'ROSExpRunDefUniqueGenerator'
]
