# Copyright 2019 John Harwell, All rights reserved.
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
Classes for the temporal variance batch criteria. See :ref:`ln-bc-tv` for usage documentation.

"""

# Core packages
import math
import typing as tp
import logging

# 3rd party packages
import implements

# Project packages
import core.variables.batch_criteria as bc
from core.variables.population_size import PopulationSize
from core.perf_measures import vcs
from core.variables.temporal_variance_parser import TemporalVarianceParser
from core.xml_luigi import XMLAttrChange, XMLAttrChangeSet


@implements.implements(bc.IConcreteBatchCriteria)
class TemporalVariance(bc.UnivarBatchCriteria):
    """
    A univariate range specifiying the set of temporal variances (and possibly swarm size) to
    use to define the batched experiment. This class is a base class which should (almost) never be
    used on its own. Instead, the ``factory()`` function should be used to dynamically create
    derived classes expressing the user's desired variance set.

    Attributes:
        variances: List of tuples specifying the waveform characteristics for each type of
                   applied variance. Cardinality of each tuple is 3, and defined as follows:

                   - xml parent path: The path to the parent element in the XML tree.
                   - [type, frequency, amplitude, offset, phase]: Waveform parameters.
                   - value: Waveform specific parameters (optional, will be None if not used for the
                            selected variance)
    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_input_root: str,
                 variance_type: str,
                 variances: tp.List[tp.Tuple[str,
                                             str,
                                             float,
                                             tp.Any,
                                             float,
                                             float]],
                 population: int) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)

        self.variance_type = variance_type
        self.variances = variances
        self.population = population
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified temporal variances.
        """
        if not self.attr_changes:
            self.attr_changes = [XMLAttrChangeSet(XMLAttrChange("{0}/waveform".format(v[0]),
                                                                "type",
                                                                str(v[1])),
                                                  XMLAttrChange("{0}/waveform".format(v[0]),
                                                                "frequency",
                                                                str(v[2])),
                                                  XMLAttrChange("{0}/waveform".format(v[0]),
                                                                "amplitude",
                                                                str(v[3])),
                                                  XMLAttrChange("{0}/waveform".format(v[0]),
                                                                "offset",
                                                                str(v[4])),
                                                  XMLAttrChange("{0}/waveform".format(v[0]),
                                                                "phase",
                                                                str(v[5]))) for v in self.variances]

            # Swarm size is optional. It can be (1) controlled via this variable, (2) controlled by
            # another variable in a bivariate batch criteria, (3) not controlled at all. For (2),
            # (3), the swarm size can be None.
            if self.population is not None:
                size_chgs = PopulationSize(self.cli_arg,
                                           self.main_config,
                                           self.batch_input_root,
                                           [self.population]).gen_attr_changelist()[0]
                for exp_chgs in self.attr_changes:
                    exp_chgs |= size_chgs

        return self.attr_changes

    def calc_reactivity_scaling(self, ideal_var: float, expx_var: float) -> float:
        # For motion throttling while robots carry blocks, the variances are always percents between
        # 0 and 1.
        if self.variance_type in ['BC', 'M']:
            if expx_var > ideal_var:
                return 1.0 - abs(expx_var - ideal_var)
            else:  # expx_var <= ideal_var:
                return 1.0 + abs(expx_var - ideal_var)
        elif self.variance_type == 'BM':
            return ideal_var / expx_var

        else:
            return 0.0

    def graph_xticks(self,
                     cmdopts: tp.Dict[str, tp.Any],
                     exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[float]:

        # If exp_dirs is passed, then we have been handed a subset of the total # of directories in
        # the batch exp root, and so n_exp() will return more experiments than we actually
        # have. This behavior is needed to correct extract x/y values for bivar experiments.
        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        m = len(exp_dirs)

        return [round(vcs.EnvironmentalCS(self.main_config, cmdopts, x)(self, exp_dirs), 4)
                for x in range(0, m)]

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, tp.Any],
                          exp_dirs: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        return list(map(str, self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        return vcs.method_xlabel(cmdopts["envc_cs_method"])

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, tp.Any]) -> tp.List[str]:
        return ['exp' + str(x) for x in range(0, len(self.gen_attr_changelist()))]

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'flexibility']

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        return True


def factory(cli_arg: str,
            main_config: tp.Dict[str, tp.Any],
            batch_input_root: str,
            **kwargs) -> TemporalVariance:
    """
    Factory to create :class:`TemporalVariance` derived classes from the command line definition of
    batch criteria.

    """
    attr = TemporalVarianceParser()(cli_arg)

    def gen_variances(attr: tp.Dict[str, tp.Any]) -> tp.List[tp.Tuple[str,
                                                                      str,
                                                                      float,
                                                                      tp.Any,
                                                                      float,
                                                                      float]]:

        amps_key = attr['variance_type'] + '_amp'
        try:
            amps = main_config['perf']['flexibility'][amps_key]
            hzs = main_config['perf']['flexibility']['hz']
        except KeyError:
            msg = "'hz' or '{0}' not found in 'flexibility' section of main config file for project".format(
                amps_key)
            logging.fatal(msg)
            raise

        variances = [(attr["xml_parent_path"],
                      "Constant",
                      0.0,
                      amps[0],
                      0.0,
                      0.0)]
        if any(v == attr["waveform_type"] for v in ["Sine", "Square", "Sawtooth"]):

            variances.extend([(attr["xml_parent_path"],
                               attr["waveform_type"],
                               hz,
                               amp,
                               amp,
                               0.0) for hz in hzs for amp in amps[1:]])

        elif attr["waveform_type"] == "StepD":
            variances.extend([(attr["xml_parent_path"],
                               "Square",
                               1 / (2 * attr["waveform_param"]),
                               amp,
                               0.0,
                               0.0) for amp in amps[1:]])

        if attr["waveform_type"] == "StepU":
            variances.extend([(attr["xml_parent_path"],
                               "Square",
                               1 / (2 * attr["waveform_param"]),
                               amp,
                               amp,
                               math.pi) for amp in amps[1:]])
        return variances

    def __init__(self: TemporalVariance) -> None:
        TemporalVariance.__init__(self,
                                  cli_arg,
                                  main_config,
                                  batch_input_root,
                                  attr['variance_type'],
                                  gen_variances(attr),
                                  attr.get("population", None))

    return type(cli_arg,
                (TemporalVariance,),
                {"__init__": __init__})   # type: ignore


__api__ = [
    'TemporalVariance'
]
