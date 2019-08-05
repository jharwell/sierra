"""
 Copyright 2018 John Harwell, All rights reserved.

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

from generators.exp_input_generator import ExpInputGenerator


class BaseGenerator(ExpInputGenerator):
    """
    Generates simulation input changes needed for all depth1 controllers.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save):
        """
        xml_luigi = super().generate_common_defs()
        xml_luigi.attribute_change(".//loop_functions", "label", "depth1_loop_functions")

        # Only present if rendering is enabled
        if xml_luigi.has_tag(".//qt-opengl"):
            xml_luigi.attribute_change(".//qt-opengl", "user_functions", "depth1_qt_user_functions")

        return xml_luigi


class GP_DPOGenerator(BaseGenerator):
    """
    Generates simulation input changes common needed for all GP_DPO controllers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save):
        """
        xml_luigi = super().generate()
        xml_luigi.tag_change(".//controllers", "__template__", "gp_dpo_controller")
        return xml_luigi


class GP_MDPOGenerator(BaseGenerator):
    """
    Generates simulation input changes common needed for all GP_MDPO controllers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save):
        """
        xml_luigi = super().generate()
        xml_luigi.tag_change(".//controllers", "__template__", "gp_mdpo_controller")
        return xml_luigi


class GP_ODPOGenerator(BaseGenerator):
    """
    Generates simulation input changes common needed for all GP_ODPO controllers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save):
        """
        xml_luigi = super().generate()
        xml_luigi.tag_change(".//controllers", "__template__", "gp_odpo_controller")
        return xml_luigi


class GP_OMDPOGenerator(BaseGenerator):
    """
    Generates simulation input changes common needed for all GP_OMDPO controllers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save):
        """
        xml_luigi = super().generate()
        xml_luigi.tag_change(".//controllers", "__template__", "gp_omdpo_controller")
        return xml_luigi
