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
"""Classes for generating common XML modifications to :term:`ROS1` input files.

I.e., changes which are platform-specific, but applicable to all projects using
ROS with a real robot execution environment.

"""
# Core packages
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.experiment import spec, xml, definition
from sierra.core import types, ros1, config, utils


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

        self.logger.debug("Writing separate <master> launch file")
        exp_def.write_config.add({
            'src_parent': '.',
            'src_tag': 'master',
            'opath_leaf': '_master' + config.kROS['launch_file_ext'],
            'create_tags': None,
            'rename_to': 'launch',
            'dest_parent': None
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

        return exp_def


class PlatformExpRunDefUniqueGenerator(ros1.generators.ROSExpRunDefUniqueGenerator):
    def __init__(self,
                 *args,
                 **kwargs) -> None:
        ros1.generators.ROSExpRunDefUniqueGenerator.__init__(
            self, *args, **kwargs)

    def generate(self, exp_def: definition.XMLExpDef):
        exp_def = super().generate(exp_def)
        main_path = pathlib.Path(self.cmdopts['project_config_root'],
                                 config.kYAML.main)

        with utils.utf8open(main_path) as f:
            main_config = yaml.load(f, yaml.FullLoader)

        n_robots = utils.get_n_robots(main_config,
                                      self.cmdopts,
                                      self.launch_stem_path.parent,
                                      exp_def)

        for i in range(0, n_robots):
            prefix = main_config['ros']['robots'][self.cmdopts['robot']]['prefix']
            exp_def.write_config.add({
                'src_parent': "./robot",
                'src_tag': f"group/[@ns='{prefix}{i}']",
                'opath_leaf': f'_robot{i}' + config.kROS['launch_file_ext'],
                'create_tags': [xml.TagAdd.as_root('launch', {})],
                'dest_parent': ".",
                'rename_to': None,
                'child_grafts': ["./robot/group/[@ns='sierra']"]
            })

        self.generate_random(exp_def)
        self.generate_paramfile(exp_def)

        return exp_def


__api__ = [
    'PlatformExpDefGenerator',
    'PlatformExpRunDefUniqueGenerator'


]
