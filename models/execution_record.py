# Copyright 2020 John Harwell, All rights reserved.
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
#
"""
Classes tracking model execution.
"""
# Core packages

# 3rd party packages
from singleton_decorator import singleton

# Project packages


@singleton
class ExecutionRecord():
    """
    Singleton data class tracking which models have been run during an invocation of SIERRA in order
    to allow for "simple" models to be re-used in larger more complex models without need to be
    re-run (advantageous of the model is computationally expensive to run).
    """

    def __init__(self):
        self.intra = dict()  # tp.Dict[str, tp.List[int]]
        self.inter = dict()  # tp.Dict[str, bool]

    def intra_record_add(self, name: str, exp_num: int):
        if not name in self.intra.keys():
            self.intra[name] = []
        self.intra[name].append(exp_num)

    def intra_record_exists(self, name: str, exp_num: int):
        return exp_num in self.intra.get(name, [])

    def inter_record_add(self, name: str):
        self.inter[name] = True

    def inter_record_exists(self, name: str):
        return self.intra.get(name, False)
