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
import os

import typing as tp
import numpy as np

from core.variables.batch_criteria import UnivarBatchCriteria
from core.variables.population_size import PopulationSize
import core.utils


class SAANoise(UnivarBatchCriteria):
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
        UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_generation_root)

        self.variances = variances
        self.population = population
        self.noise_type = noise_type

    def gen_attr_changelist(self) -> list:
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified noise ranges.
        """
        # Swarm size is optional. It can be (1) controlled via this variable, (2) controlled by
        # another variable in a bivariate batch criteria, (3) not controlled at all. For (2), (3),
        # the swarm size can be None.
        if self.population is not None:
            size_attr = next(iter(PopulationSize(self.cli_arg,
                                                 self.main_config,
                                                 self.batch_generation_root,
                                                 [self.population]).gen_attr_changelist()[0]))
            changes = [{(v2[0], v2[1], v2[2]) for v2 in v1} for v1 in self.variances]
            for c in changes:
                c.add(size_attr)
            return changes
        else:
            return [{v2 for v2 in v1} for v1 in self.variances]

    def graph_xticks(self,
                     cmdopts: tp.Dict[str, str],
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:

        # If exp_dirs is passed, then we have been handed a subset of the total # of directories in
        # the batch exp root, and so n_exp() will return more experiments than we actually
        # have. This behavior is needed to correctly extract x/y values for bivariate experiments.
        if exp_dirs is not None:
            if self.__uniform_sources():
                return [self.__avg_uniform_level_from_dir(d) for d in exp_dirs]
            elif self.__gaussian_sources():
                # order by mean
                return [self.__avg_gaussian_level_from_dir(d)[0] for d in exp_dirs]
            else:
                return [x for x in range(0, len(exp_dirs))]
        else:
            if self.__uniform_sources():
                return [self.__avg_uniform_level_from_chglist(v) for v in self.variances]
            elif self.__gaussian_sources():
                # order by mean
                return [self.__avg_gaussian_level_from_chglist(v)[0] for v in self.variances]
            else:
                return [x for x in range(0, self.n_exp())]

    def graph_xticklabels(self,
                          cmdopts: tp.Dict[str, str],
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:
        if exp_dirs is not None:
            if self.__uniform_sources():
                return ["U(-{0},{0})".format(round(l, 2)) for l in self.graph_xticks(cmdopts, exp_dirs)]
            elif self.__gaussian_sources():
                levels = [self.__avg_gaussian_level_from_dir(d) for d in exp_dirs]
                return ["G({0},{1})".format(round(mean, 2), round(stddev)) for mean, stddev in levels]
            else:
                return list(map(str, range(0, len(exp_dirs))))
        else:
            if self.__uniform_sources():
                levels = [self.__avg_uniform_level_from_chglist(v) for v in self.variances]
                return ["U(-{0},{0})".format(round(l, 2)) for l in levels]
            elif self.__gaussian_sources():
                levels = [self.__avg_gaussian_level_from_chglist(v) for v in self.variances]
                return ["G({0},{1})".format(round(mean), round(stddev)) for mean, stddev in levels]
            else:
                return list(map(str, range(0, self.n_exp())))

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        labels = {
            'sensors': 'Sensor Noise',
            'actuators': 'Actuator Noise',
            'all': 'Sensor And Actuator Noise'
        }
        return labels[self.noise_type]

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> tp.List[str]:
        return ['exp' + str(x) for x in range(0, len(self.gen_attr_changelist()))]

    def pm_query(self, pm: str) -> bool:
        return pm in ['blocks-transported', 'robustness-saa']

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

    def __avg_uniform_level_from_chglist(self, changelist) -> float:
        """
        Return the average level used for all uniform noise sources for the specified changelist
        corresponding to a particular experiment by reading the XML attribute changelist. Only valid
        if :method:`__uniform_sources` returns `True`.
        """
        accum = 0.0
        count = 0
        for source in changelist:
            _, attr, value = source
            if attr == 'level':
                accum += float(value)
                count += 1
        return accum / count

    def __avg_uniform_level_from_dir(self, expdir: str):
        """
        Return the average level used for all uniform noise sources within the specified experiment
        by reading the pickle file; this is only needed for bivariate batch criteria in order to get
        graph ticks/tick labels to come out right. Only valid if :method:`__uniform_sources` returns
        `True`.

        """
        accum = 0.0
        exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                           expdir,
                                                           'exp_def.pkl'))
        count = 0
        for parent, attr, value in exp_def:
            if 'noise' in parent and attr == 'level':
                accum += float(value)
                count += 1
        return accum / count

    def __avg_gaussian_level_from_chglist(self, changelist) -> tp.Tuple[float, float]:
        """
        Return the average (mean, stddev) used for all Gaussian noise sources for the specified
        changelist corresponding to a particular experiment by reading the XML attribute
        changelist. Only valid if :method:`__guassian_sources` returns `True`.

        """
        mean_accum = 0.0
        stddev_accum = 0.0
        count = 0
        for source in changelist:
            parent, attr, value = source
            if attr == 'mean':
                mean_accum += float(value)
                count += 1
            elif attr == 'stddev':
                stddev_accum += float(value)
                count += 1
        return (mean_accum / count, stddev_accum / count)

    def __avg_gaussian_level_from_dir(self, expdir: str):
        """
        Return the average (mean, stddev) used for all gaussian Noise sources within a specific
        experiment by reading the pickle file; this is only needed for bivariate batch criteria in
        order to get graph ticks/tick labels to come out right. Only valid if
        :method:`__gaussian_sources` returns `True`.

        """
        mean_accum = 0.0
        stddev_accum = 0.0
        count = 0
        exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                           expdir,
                                                           'exp_def.pkl'))
        for parent, attr, value in exp_def:
            if 'noise' in parent and attr == 'mean':
                mean_accum += float(value)
                count += 1
            if 'noise' in parent and attr == 'stddev':
                stddev_accum += float(value)
                count += 1
        return (mean_accum / count, stddev_accum / count)


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
            'population': int()
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
            },

            'actuators': {
                'steering': ('.//sensors/differential_steering', ['noise_factor'])
            }

        }

        if any(v == attr['noise_type'] for v in ['sensors', 'actuators']):
            sources = main_config['sierra']['robustness'][attr['noise_type']]
            noise_types = [attr['noise_type']]
        else:
            sources = main_config['sierra']['robustness']['actuators']
            sources.update(main_config['sierra']['robustness']['sensors'])
            noise_types = ['sensors', 'actuators']

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
        by_src = []
        n_levels = 0
        for src, config in sources.items():
            for nt in noise_types:
                # Cannot always add noise to the sensor AND actuator models for the same device (eg
                # light sensor does not have a light actuator complement).
                if src not in xml_parents[nt]:
                    continue

                xml_parent = xml_parents[nt][src][0]
                xml_child_tags = xml_parents[nt][src][1]
                if config['model'] == 'uniform':
                    levels = [x for x in np.linspace(config['range'][0],
                                                     config['range'][1],
                                                     num=attr['cardinality'] + 1)]
                    for l in levels:
                        by_src.extend([set([(xml_parent + tag, 'model', config['model']),
                                            (xml_parent + tag, 'level', str(l))]) for tag in xml_child_tags])
                    n_levels = len(levels)
                elif config['model'] == 'gaussian':
                    stddev_levels = [x for x in np.linspace(config['stddev_range'][0],
                                                            config['stddev_range'][1],
                                                            num=attr['cardinality'] + 1)]
                    mean_levels = [x for x in np.linspace(config['mean_range'][0],
                                                          config['mean_range'][1],
                                                          num=attr['cardinality'] + 1)]
                    for l1, l2 in zip(mean_levels, stddev_levels):
                        by_src.extend([set([(xml_parent + tag, 'model', config['model']),
                                            (xml_parent + tag, 'mean', str(l1)),
                                            (xml_parent + tag, 'stddev', str(l2))])
                                       for tag in xml_child_tags])
                    n_levels = len(mean_levels)
                else:
                    assert False, "FATAL: bad noise model '{0}'".format(config['model'])

        # Invert!
        by_exp = []
        for i in range(0, n_levels):
            # This is the magic line. It takes every "level"-th element, since that is the # of
            # experiments that this criteria defines, starting with i=0...n_levels. So if there are
            # 10 levels, then the first set added to the return list would be i={0,10,20,...}, the
            # second would be i={1,11,21,...}, etc.
            by_exp.append({chg for s in by_src[i::n_levels] for chg in s})

        return by_exp

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
