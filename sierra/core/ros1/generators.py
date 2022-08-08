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
"""Classes for generating XML changes common to all :term:`ROS1` platforms.

I.e., changes which are platform-specific, but applicable to all projects using
ROS1.

"""
# Core packages
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.experiment import definition, spec, xml
import sierra.core.utils as scutils
from sierra.core import types, config
import sierra.core.ros1.variables.exp_setup as exp


class ROSExpDefGenerator():
    """Generates XML changes to input files that common to all ROS experiments.

     ROS1 requires up to 2 input files per run:

    - The launch file containing robot definitions, world definitions (for
      simulations only).

    - The parameter file for project code (optional).

    Putting everything in 1 file would require extensively using the ROS1
    parameter server which does NOT accept parameters specified in XML--only
    YAML. So requiring some conventions on the .launch input file seemed more
    reasonable.

    Attributes:

        controller: The controller used for the experiment.
        cmdopts: Dictionary of parsed cmdline parameters.

    """

    def __init__(self,
                 exp_spec: spec.ExperimentSpec,
                 controller: str,
                 cmdopts: types.Cmdopts,
                 **kwargs) -> None:
        self.controller = controller
        self.spec = exp_spec
        self.cmdopts = cmdopts
        self.template_input_file = kwargs['template_input_file']
        self.kwargs = kwargs
        self.ros_param_server = False
        self.logger = logging.getLogger(__name__)

    def generate(self) -> definition.XMLExpDef:
        exp_def = definition.XMLExpDef(input_fpath=self.template_input_file)
        wr_config = xml.WriterConfig([])

        if exp_def.has_tag('./params'):
            self.logger.debug("Using shared XML parameter file")
            wr_config.add({
                'src_parent': '.',
                'src_tag': 'params',
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

    def _generate_experiment(self, exp_def: definition.XMLExpDef) -> None:
        """
        Generate XML tag changes to setup basic experiment parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        self.logger.debug("Applying exp_setup=%s", self.cmdopts['exp_setup'])
        robots_need_timekeeper = 'ros1robot' in self.cmdopts['platform']

        # Barrier start not needed in simulation
        use_barrier_start = ('ros1robot' in self.cmdopts['platform'] and
                             not self.cmdopts["no_master_node"])

        setup = exp.factory(self.cmdopts["exp_setup"],
                            use_barrier_start,
                            robots_need_timekeeper)()
        rms, adds, chgs = scutils.apply_to_expdef(setup, exp_def)

        # Write setup info to file for later retrieval
        scutils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)


class ROSExpRunDefUniqueGenerator:
    """
    Generate XML changes unique to a experimental runs for ROS experiments.

    These include:

    - Random seeds for each: term: `Experimental Run`.

    - Unique parameter file for each: term: `Experimental Run`.
    """

    def __init__(self,
                 run_num: int,
                 run_output_path: pathlib.Path,
                 launch_stem_path: pathlib.Path,
                 random_seed: int,
                 cmdopts: types.Cmdopts) -> None:

        self.run_output_path = run_output_path
        self.launch_stem_path = launch_stem_path
        self.random_seed = random_seed
        self.cmdopts = cmdopts
        self.run_num = run_num
        self.logger = logging.getLogger(__name__)

    def generate(self, exp_def: definition.XMLExpDef):
        return exp_def

    def generate_random(self, exp_def: definition.XMLExpDef) -> None:
        """Generate XML changes for random seeding for an experimental run.

        """
        self.logger.trace("Generating random seed changes for run%s",  # type: ignore
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

    def generate_paramfile(self, exp_def: definition.XMLExpDef) -> None:
        """Generate XML changes for the parameter file for an experimental run.

        """
        self.logger.trace("Generating parameter file changes for run%s",  # type: ignore
                          self.run_num)

        param_file = self.launch_stem_path.with_suffix(config.kROS['param_file_ext'])

        # Master node gets a copy of the parameter file
        exp_def.tag_add("./master/group/[@ns='sierra']",
                        "param",
                        {
                            "name": "experiment/param_file",
                            "value": str(param_file)
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
                            "value": str(param_file)
                        })


__api__ = [
    'ROSExpDefGenerator',
    'ROSExpRunDefUniqueGenerator'
]
