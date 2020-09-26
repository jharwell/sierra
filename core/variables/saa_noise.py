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
Classes for the SAA noise batch criteria. See :ref:`ln-bc-saa-noise` for usage documentation.

"""

import re
import typing as tp

import implements
import numpy as np

import core.variables.batch_criteria as bc
from core.variables.population_size import PopulationSize


@implements.implements(bc.IConcreteBatchCriteria)
class SAANoise(bc.UnivarBatchCriteria):
    """
    A univariate range specifiying the set of noise ranges for Sensors And Actuators (SAA), and
    possibly swarm size to use to define the batched experiment. This class is a base class which
    should (almost) never be used on its own. Instead, the ``factory()`` function should be used to
    dynamically create derived classes expressing the user's desired variance set.

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
                 batch_generation_root: str,
                 variances: list,
                 population: int,
                 noise_type: str) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)

        self.variances = variances
        self.population = population
        self.noise_type = noise_type
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> list:
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified noise ranges.
        """
        if not self.attr_changes:
            self.attr_changes = [{(v2[0], v2[1], v2[2]) for v2 in v1} for v1 in self.variances]

            # Swarm size is optional. It can be (1) controlled via this variable, (2) controlled by
            # another variable in a bivariate batch criteria, (3) not controlled at all. For (2),
            # (3), the swarm size can be None.
            if self.population is not None:
                size_chgs = PopulationSize(self.cli_arg,
                                           self.main_config,
                                           self.batch_generation_root,
                                           [self.population]).gen_attr_changelist()[0]
                for exp_chgs in self.attr_changes:
                    exp_chgs |= size_chgs

        return self.attr_changes

    def graph_xticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:
        xticks_range = []

        if self.__gaussian_sources():
            if self.main_config['perf']['robustness']['gaussian_ticks_src'] == 'mean':
                xticks_range = self.main_config['perf']['robustness']['gaussian_ticks_mean_range']
            else:
                xticks_range = self.main_config['perf']['robustness']['gaussian_ticks_stddev_range']
        elif self.__uniform_sources():
            xticks_range = self.main_config['perf']['robustness']['uniform_ticks_range']

        # If exp_dirs is passed, then we have been handed a subset of the total # of directories in
        # the batch exp root, and so n_exp() will return more experiments than we actually
        # have. This behavior is needed to correctly extract x/y values for bivariate experiments.
        if exp_dirs is not None:
            return np.linspace(xticks_range[0], xticks_range[1], num=len(exp_dirs))
        else:
            return np.linspace(xticks_range[0], xticks_range[1], num=len(self.variances))

    def graph_xticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:

        if self.__uniform_sources():
            xticks = self.graph_xticks(cmdopts, exp_dirs)
            return ["U(-{0},{0})".format(round(t, 3)) for t in xticks]
        elif self.__gaussian_sources():
            mean_xticks = []
            stddev_xticks = []

            xticks_mean_range = self.main_config['perf']['robustness']['gaussian_ticks_mean_range']
            xticks_stddev_range = self.main_config['perf']['robustness']['gaussian_ticks_stddev_range']

            if exp_dirs is not None:
                mean_xticks = np.linspace(xticks_mean_range[0],
                                          xticks_mean_range[1],
                                          num=len(exp_dirs))
                stddev_xticks = np.linspace(xticks_stddev_range[0],
                                            xticks_stddev_range[1],
                                            num=len(exp_dirs))

            else:
                mean_xticks = np.linspace(xticks_mean_range[0],
                                          xticks_mean_range[1],
                                          num=len(self.variances))
                stddev_xticks = np.linspace(xticks_stddev_range[0],
                                            xticks_stddev_range[1],
                                            num=len(self.variances))

            levels = zip(mean_xticks, stddev_xticks)
            return ["G({0},{1})".format(round(mean, 3), round(stddev, 3)) for mean, stddev in levels]
        else:
            return []

    def graph_xlabel(self, cmdopts: dict) -> str:
        labels = {
            'sensors': 'Sensor Noise',
            'actuators': 'Actuator Noise',
            'all': 'Sensor And Actuator Noise'
        }
        return labels[self.noise_type]

    def gen_exp_dirnames(self, cmdopts: dict) -> tp.List[str]:
        return ['exp' + str(x) for x in range(0, len(self.gen_attr_changelist()))]

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'robustness']

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        return False

    def __uniform_sources(self):
        """
        Return TRUE if all noise sources are uniform.
        """
        for v in self.variances:
            for _, attr, value in v:
                if attr == 'model' and value != 'uniform':
                    return False
        return True

    def __gaussian_sources(self):
        """
        Return TRUE if all noise sources are gaussian.
        """
        for v in self.variances:
            for _, attr, value in v:
                if attr == 'model' and value != 'gaussian':
                    return False
        return True


class SAANoiseParser():
    """
    Enforces the cmdline definition of the :class:`SAANoise` batch criteria.
    """

    def __call__(self, criteria_str: str) -> dict:
        """
        Returns:
            Dictionary with the following keys:
                - noise_type: Sensors|Actuators|All
                - cardinality: Cardinality of the set of noise ranges
                - population: Swarm size to use (optional)

        """
        ret = {
            'noise_type': str(),
            'cardinality': int(),
            'population': None
        }

        # Parse noise type
        res = re.search("sensors|actuators|all", criteria_str)
        assert res is not None, "FATAL: Bad noise type in criteria '{0}'".format(criteria_str)
        ret['noise_type'] = res.group(0)

        # Parse cardinality
        res = re.search(r"\.C[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad cardinality for set of noise ranges in criteria '{0}'".format(criteria_str)
        ret['cardinality'] = int(res.group(0)[2:])

        # Parse swarm size (optional)
        res = re.search(r"\.Z[0-9]+", criteria_str)
        if res is not None:
            ret['population'] = int(res.group(0)[2:])

        return ret


def factory(cli_arg: str, main_config: dict, batch_generation_root: str, **kwargs):
    """
    Factory to create :class:`SAANoise` derived classes from the command line definition of
    batch criteria.

    """
    attr = SAANoiseParser()(cli_arg)

    def gen_variances(attr: dict):

        xml_parents = {
            'sensors': {
                'light': ('.//sensors/footbot_light', ['noise']),
                'proximity': ('.//sensors/footbot_proximity', ['noise']),
                'ground': ('.//sensors/footbot_motor_ground', ['noise']),
                'steering': ('.//sensors/differential_steering', ['vel_noise', 'dist_noise']),
                'position': ('.//sensors/positioning', ['noise']),
                'colored_blob_omnidirectional_camera': ('.//sensors/colored_blob_omnidirectional_camera', ['noise'])
            },

            'actuators': {
                'steering': ('.//actuators/differential_steering', ['noise_factor'])
            }

        }

        if any(v == attr['noise_type'] for v in ['sensors', 'actuators']):
            configured_sources = {attr['noise_type']: main_config['perf']['robustness'][attr['noise_type']]}
        else:
            configured_sources = {
                'actuators': main_config['perf']['robustness'].get('actuators', {}),
                'sensors': main_config['perf']['robustness'].get('sensors', {})
            }

        # We iterate through by noise source (sensor or actuator) creating lists of noise levels for
        # each source, which are joined to create a list-of-lists: by_src. We have to do it this
        # way, because we need the values in the xml_attr dict in order to create the list of noise
        # ranges for each source.
        #
        # Only after creating this list-of-lists can we then invert it and group the lists of ranges
        # by experiment, rather than src. That is, we take the 0-th index from each source and use
        # them to define the first set of XML changes, then the 1-th index to define the second,
        # etc.
        #
        # I couldn't find a more elegant way of doing this.
        by_src = []  # type: tp.List[tp.Set]

        for dev_type in xml_parents.keys():
            # Either the sensors or actuators list is empty because it wasn't included in the YAML
            # config file.
            if dev_type not in configured_sources.keys():
                continue
            for dev_name in xml_parents[dev_type].keys():
                # Sensor or actuator missing from YAML list
                if dev_name not in configured_sources[dev_type].keys():
                    continue

                dev_noise_config = configured_sources[dev_type][dev_name]
                configure_device(xml_parents[dev_type][dev_name], dev_noise_config, by_src)

        # Invert!
        by_exp = []
        for i in range(0, attr['cardinality']):
            # This is the magic line. It takes every "level"-th element, since that is the # of
            # experiments that this criteria defines, starting with i=0...n_levels. So if there are
            # 10 levels, then the first set added to the return list would be i={0,10,20,...}, the
            # second would be i={1,11,21,...}, etc.
            by_exp.append({chg for s in by_src[i:: attr['cardinality']] for chg in s})

        return by_exp

    def configure_device(xml_config: tuple, dev_noise_config: dict, by_src: list):
        xml_parent = xml_config[0]
        xml_child_tags = xml_config[1]

        if dev_noise_config['model'] == 'uniform':
            levels = [x for x in np.linspace(dev_noise_config['range'][0],
                                             dev_noise_config['range'][1],
                                             num=attr['cardinality'])]
            for level in levels:
                v = set()
                for tag in xml_child_tags:
                    v |= set([(xml_parent + "/" + tag, 'model', dev_noise_config['model']),
                              (xml_parent + "/" + tag, 'level', str(level))])
                by_src.extend([v])
        elif dev_noise_config['model'] == 'gaussian':
            stddev_levels = [x for x in np.linspace(dev_noise_config['stddev_range'][0],
                                                    dev_noise_config['stddev_range'][1],
                                                    num=attr['cardinality'])]
            mean_levels = [x for x in np.linspace(dev_noise_config['mean_range'][0],
                                                  dev_noise_config['mean_range'][1],
                                                  num=attr['cardinality'])]
            for l1, l2 in zip(mean_levels, stddev_levels):
                v = set()
                for tag in xml_child_tags:
                    v |= set([(xml_parent + "/" + tag, 'model', dev_noise_config['model']),
                              (xml_parent + "/" + tag, 'mean', str(l1)),
                              (xml_parent + "/" + tag, 'stddev', str(l2))])

                by_src.extend([v])
        else:
            assert False, "FATAL: bad noise model '{0}'".format(dev_noise_config['model'])

    def __init__(self) -> None:
        SAANoise.__init__(self,
                          cli_arg,
                          main_config,
                          batch_generation_root,
                          gen_variances(attr),
                          attr.get("population", None),
                          attr['noise_type'])

    return type(cli_arg,
                (SAANoise,),
                {"__init__": __init__})


__api__ = [
    'SAANoise'


]
