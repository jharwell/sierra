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
Classes for generating XML changes to the :term:`ROS` input file independent
of any :term:`Project`; i.e., changes which are platform-specific, but
applicable to all projects using ROS with a real robot execution environment.

"""
# Core packages
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core.xml import XMLLuigi
from sierra.core.experiment.spec import ExperimentSpec
from sierra.core import types, ros


class PlatformExpDefGenerator(ros.generators.ROSExpDefGenerator):
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
        super().__init__(spec, controller, cmdopts, **kwargs)

        self.logger = logging.getLogger(__name__)

    def generate(self) -> XMLLuigi:
        exp_def = super().generate()
        return exp_def


class PlatformExpRunDefUniqueGenerator(ros.generators.ROSExpRunDefUniqueGenerator):
    pass


__api__ = [
    'PlatformExpDefGenerator',
    'PlatformExpRunDefUniqueGenerator'
]
