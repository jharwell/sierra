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

import numpy as np
from base_criteria import BaseCriteria


class EstimationAlpha(BaseCriteria):
    """
    Define a list of floating point values in [0,1] to test with.
    Attributes:
      range_list(list): List of values for estimation alpha.
    """

    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline."""
        return [[("params.task_executive.estimation.alpha", s)] for s in np.arange(0.1, 0.95, 0.05)]
