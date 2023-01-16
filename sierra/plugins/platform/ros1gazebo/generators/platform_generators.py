# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for generating common XML modifications for :term:`ROS1+Gazebo`.

I.e., changes which are platform-specific, but applicable to all projects using
the platform.

"""
# Core packages
import logging

# 3rd party packages

# Project packages
from sierra.core.experiment import spec, definition
from sierra.core import types, ros1, config


class PlatformExpDefGenerator(ros1.generators.ROSExpDefGenerator):
    """
    Init the object.

    Attributes:

        controller: The controller used for the experiment.

        cmdopts: Dictionary of parsed cmdline parameters.
    """

    def __init__(self,
                 exp_spec: spec.ExperimentSpec,
                 controller: str,
                 cmdopts: types.Cmdopts,
                 **kwargs) -> None:
        super().__init__(exp_spec, controller, cmdopts, **kwargs)
        self.logger = logging.getLogger(__name__)

    def generate(self) -> definition.XMLExpDef:
        exp_def = super().generate()

        exp_def.write_config.add({
            'src_parent': ".",
            'src_tag': "master",
            'opath_leaf': "_master" + config.kROS['launch_file_ext'],
            'create_tags': None,
            'dest_parent': None,
            'rename_to': 'launch'
        })

        exp_def.write_config.add({
            'src_parent': ".",
            'src_tag': "robot",
            'opath_leaf': "_robots" + config.kROS['launch_file_ext'],
            'create_tags': None,
            'dest_parent': None,
            'rename_to': 'launch'
        })

        # Setup gazebo experiment
        self._generate_gazebo_core(exp_def)

        # Setup gazebo visualization
        self._generate_gazebo_vis(exp_def)

        return exp_def

    def _generate_gazebo_core(self, exp_def: definition.XMLExpDef) -> None:
        """
        Generate XML tag changes to setup Gazebo core experiment parameters.

        Does not write generated changes to the run definition pickle
        file.
        """
        self.logger.debug("Generating Gazebo experiment changes (all runs)")

        # Start Gazebo/ROS in debug mode to make post-mortem analysis easier.
        exp_def.tag_add("./master/include",
                        "arg",
                        {
                            "name": "verbose",
                            "value": "true"
                        })

        # Terminate Gazebo server whenever the launch script that invoked it
        # exits.
        exp_def.tag_add("./master/include",
                        "arg",
                        {
                            "name": "server_required",
                            "value": "true"
                        })

        # Don't record stuff
        exp_def.tag_remove("./master/include", "arg/[@name='headless']")
        exp_def.tag_remove("./master/include", "arg/[@name='recording']")

        # Don't start paused
        exp_def.tag_remove("./master/include", "arg/[@name='paused']")

        # Don't start gazebo under gdb
        exp_def.tag_remove("./master/include", "arg/[@name='debug']")

    def _generate_gazebo_vis(self, exp_def: definition.XMLExpDef) -> None:
        """
        Generate XML changes to configure Gazebo visualizations.

        Does not write generated changes to the simulation definition pickle
        file.
        """
        exp_def.tag_remove_all("./master/include", "arg/[@name='gui']")
        exp_def.tag_add("./master/include",
                        "arg",
                        {
                            "name": "gui",
                            "value": "false"
                        })


class PlatformExpRunDefUniqueGenerator(ros1.generators.ROSExpRunDefUniqueGenerator):
    def __init__(self,
                 *args,
                 **kwargs) -> None:
        ros1.generators.ROSExpRunDefUniqueGenerator.__init__(
            self, *args, **kwargs)

    def generate(self, exp_def: definition.XMLExpDef):
        exp_def = super().generate(exp_def)

        self.generate_random(exp_def)
        self.generate_paramfile(exp_def)


__api__ = [
    'PlatformExpDefGenerator',
    'PlatformExpRunDefUniqueGenerator'
]
