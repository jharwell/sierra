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

import os
import random
import argparse
import subprocess
import re
from csv_class import CSV
from xml_file_generator import XMLFileGenerator

class BaseGraphGenerator:

    """
    Generates basic/common graphs desired by all experiments.

    Attributes:
      output_save_path(str): Root directory for simulation outputs(sort of a
                             scratch directory). Can be relative or absolute.
      graph_save_path(str): Root directory(relative or absolute) of where the
                            generated graphs should be saved.
    """

    def __init__(self, config_save_path, output_save_path, graph_save_path):

        # where the output data should be stored
        if output_save_path is None:
            output_save_path = os.path.join(os.path.dirname(
                self.config_save_path), "Generated_Output")
        self.output_save_path = os.path.abspath(output_save_path)

        # where the graphs should be stored
        if graph_save_path is None:
            graph_save_path = os.path.join(os.path.dirname(
                self.config_save_path), "Generated_Graph_Files")
        self.graph_save_path = os.path.abspath(graph_save_path)
