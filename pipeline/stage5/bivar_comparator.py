# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
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


from .bivar_intra_scenario_comparator import BivarIntraScenarioComparator


class BivarComparator:
    """
    Compares controllers on different criteria across/within different scenarios.
    """

    def __call__(self, controllers, graph_config, batch_criteria, output_roots, cmdopts,
                 main_config, norm_comp):
        BivarIntraScenarioComparator(controllers,
                                     graph_config['intra_scenario']['graphs'],
                                     output_roots['cc_csvs'],
                                     output_roots['cc_graphs'],
                                     cmdopts,
                                     main_config, norm_comp)(batch_criteria)
