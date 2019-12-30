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

import os
import pickle
import logging
import copy
import typing as tp

import core.utils
import core.xml_luigi
from core.variables import base_variable, constant_density


class BatchCriteria(base_variable.BaseVariable):
    """
    Defines the list of sets of changes to make to a template input file in order to run a related
    set of of experiments.

    Attributes:
        cli_arg: Unparsed batch criteria string from command line.
        main_config: Parsed dictionary of main YAML configuration.
        batch_generation_root: Absolute path to the directory where batch experiment directories
                               should be created.

    """

    kPMNames = ['blocks-collected', 'scalability', 'self-org', 'reactivity', 'adaptability']

    def __init__(self, cli_arg: str, main_config: tp.Dict[str, str], batch_generation_root: str):
        self.cli_arg = cli_arg
        self.main_config = main_config
        self.batch_generation_root = batch_generation_root

        self.cat_str = cli_arg.split('.')[0]
        self.def_str = '.'.join(cli_arg.split('.')[1:])

    def gen_attr_changelist(self) -> list:
        return []

    def gen_tag_rmlist(self) -> list:
        return []

    def gen_tag_addlist(self) -> list:
        return []

    def arena_dims(self) -> list:
        """
        Returns:
            Arena dimensions used for each experiment in the batch. Not applicable to all
            criteria.
        """
        dims = []
        for exp in self.gen_attr_changelist():
            for c in exp:
                if c[0] == ".//arena" and c[1] == "size":
                    x, y, z = c[2].split(',')
                    dims.append((int(x), int(y), int(z)))
        assert len(dims) > 0, "Scenario dimensions not contained in batch criteria"
        return dims

    def exp_dir2num(self, cmdopts: tp.Dict[str, str], exp_dir: str) -> int:
        return self.gen_exp_dirnames(cmdopts).index(exp_dir)

    def n_exp(self) -> int:
        exps = [i for i in os.listdir(self.batch_generation_root) if
                os.path.isdir(os.path.join(self.batch_generation_root, i)) and i not in
                self.main_config['sierra']['collate_csv_leaf']]
        return len(exps)

    def cleanup_pkl_files(self, batch_root: str):
        defs = list(self.gen_attr_changelist())
        for i in range(0, len(defs)):
            pkl_path = os.path.join(batch_root, 'batch_pkl{0}'.format(i))
            if os.path.exists(pkl_path):
                os.remove(pkl_path)

    def pickle_exp_defs(self, cmdopts: tp.Dict[str, str]):
        defs = list(self.gen_attr_changelist())
        for i, exp_def in enumerate(defs):
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            pkl_path = os.path.join(self.batch_generation_root, exp_dirname, 'exp_def.pkl')
            with open(pkl_path, 'ab') as f:
                pickle.dump(exp_def, f)

    def scaffold_exps(self,
                      xml_luigi: core.xml_luigi.XMLLuigi,
                      batch_config_leaf: str,
                      cmdopts: tp.Dict[str, str]):

        defs1 = list(self.gen_attr_changelist())
        defs2 = list(self.gen_tag_addlist())
        assert len(defs1) == 0 or len(defs2) == 0, \
            "FATAL: Batch criteria defines both attribute changes and tag additions"

        for i, defi in enumerate(defs1):
            print(defi)
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            exp_generation_root = os.path.join(self.batch_generation_root,
                                               str(exp_dirname))
            logging.info("Applying %s changes from batch criteria generator '%s' for exp%s in %s",
                         len(defi),
                         self.cli_arg,
                         i,
                         exp_dirname)

            os.makedirs(exp_generation_root, exist_ok=True)
            for path, attr, value in defi:
                xml_luigi.attr_change(path, attr, value)

            xml_luigi.write(os.path.join(exp_generation_root,
                                         batch_config_leaf))

        for i, defi in enumerate(defs2):
            # Because we are INSERTING and not MODIFYING tags, we have to copy the experimental
            # definition to avoid accumulating the added tags across experiments within the batch...
            xml_luigii = copy.deepcopy(xml_luigi)
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            exp_generation_root = os.path.join(self.batch_generation_root,
                                               str(exp_dirname))

            logging.info("Adding %s new tags from batch criteria '%s' for exp%s in %s",
                         len(defi),
                         self.cli_arg,
                         i,
                         exp_dirname)

            os.makedirs(exp_generation_root, exist_ok=True)

            for path, attr, value in defi:
                xml_luigii.tag_add(path, attr, value)
            xml_luigii.write(os.path.join(exp_generation_root,
                                          batch_config_leaf))

        n_exps = len(defs1) + len(defs2)
        n_exp_dirs = len(os.listdir(self.batch_generation_root))
        assert n_exps == n_exp_dirs,\
            "FATAL: Size of batched experiment ({0}) != # exp dirs ({1}): possibly caused by:\n"\
            "(1) Changing batch criteria without changing the generation root ({2})\n"\
            "(2) Sharing {2} between different batch criteria\n".format(n_exps,
                                                                        n_exp_dirs,
                                                                        self.batch_generation_root)

    def is_bivar(self) -> bool:
        """

        Returns:
            `True` if this class is a bivariate batch criteria instance, and `False` otherwise.
        """
        raise NotImplementedError

    def is_univar(self) -> bool:
        """

        Returns:
            `True` if this class is a univar batch criteria instance, and `False` otherwise.
        """
        raise NotImplementedError

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str]) -> tp.List[str]:
        """
        Generate list of strings from the current changelist to use for directory names within a
        batched experiment.

        Returns:
            List of directory names for current experiment

        """
        raise NotImplementedError

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then this list of directories directories will be used to
                      calculate the ticks, rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the X axis tick values for graph generation.

        """
        raise NotImplementedError

    def graph_yticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the ticks,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of criteria-specific values to use as the Y axis tick values for graph
            generation.

        """
        raise NotImplementedError

    def graph_yticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[str]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the labels,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the Y axis tick labels for graph generation.

        """
        raise NotImplementedError

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[str]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the labels,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the X axis tick labels for graph generation.

        """
        raise NotImplementedError

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        """
        Returns:
            The X-label that should be used for the graphs of various performance measures across
            batch criteria.
        """
        raise NotImplementedError

    def graph_ylabel(self, cmdopts: tp.Dict[str, str]) -> str:
        """
        Returns:
            The Y-label that should be used for the graphs of various performance measures across
            batch criteria. Only needed by bivar batch criteria.
        """
        raise NotImplementedError

    def pm_query(self, pm: str) -> bool:
        """
        Arguments:
            pm: A possible performance measure to generate from the results of the batched
                experiment defined by this object.

        Returns:
            `True` if the specified pm should be generated for the current object, and
            `False` otherwise.
        """
        raise NotImplementedError


class UnivarBatchCriteria(BatchCriteria):
    """
    Base class for a univariate batch criteria.
    """

    def is_bivar(self) -> bool:
        return False

    def is_univar(self) -> bool:
        return True

    def populations(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[int]:
        """
        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If is not `None`, then these directories will be used to calculate the
                      swarm sizes, rather than the results of `gen_exp_dirnames()`.

        Returns:
            The list of swarm sizes used the batched experiment, sorted.

        """
        sizes = []
        if exp_dirs is not None:
            dirs = exp_dirs
        else:
            dirs = self.gen_exp_dirnames(cmdopts)

        for d in dirs:
            exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                               d,
                                                               "exp_def.pkl"))
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))
        return sizes


class BivarBatchCriteria(BatchCriteria):
    """
    Combination of the definition of two separate batch criteria.

    """

    def __init__(self, criteria1, criteria2):
        BatchCriteria.__init__(self,
                               '+'.join([criteria1.cli_arg, criteria2.cli_arg]),
                               criteria1.main_config,
                               criteria1.batch_generation_root)
        self.criteria1 = criteria1
        self.criteria2 = criteria2

    def gen_attr_changelist(self) -> list:
        list1 = self.criteria1.gen_attr_changelist()
        list2 = self.criteria2.gen_attr_changelist()
        ret = []
        for l1 in list1:
            for l2 in list2:
                ret.append(l1 | l2)

        return ret

    def gen_tag_rmlist(self) -> list:
        ret = self.criteria1.gen_tag_rmlist().extend(self.criteria2.gen_tag_rmlist())
        return ret

    def gen_tag_addlist(self) -> list:
        ret = self.criteria1.gen_tag_addlist().extend(self.criteria2.gen_tag_addlist())
        return ret

    def gen_exp_dirnames(self, cmdopts: tp.Dict[str, str], what: str = 'all') -> tp.List[str]:
        """
        Generates a SORTED list of strings for all X/Y axis directories for the bivariate
        experiments, or both X and Y.
        """
        list1 = self.criteria1.gen_exp_dirnames(cmdopts)
        list2 = self.criteria2.gen_exp_dirnames(cmdopts)
        ret = []

        if what == 'x':
            return ['c1-' + x for x in list1]
        elif what == 'y':
            return ['c2-' + y for y in list2]
        else:
            for l1 in list1:
                for l2 in list2:
                    ret.append('+'.join(['c1-' + l1, 'c2-' + l2]))

            return ret

    def populations(self, cmdopts: tp.Dict[str, str]) -> tp.List[int]:
        """Generate a 2D array of swarm swarm sizes used the batched experiment, in the same order as the
        directories returned from `gen_exp_dirnames()` for each criteria along each axis.

        """
        dirs = self.gen_exp_dirnames(cmdopts)

        sizes = [[0 for col in self.criteria2.gen_exp_dirnames(
            cmdopts)] for row in self.criteria1.gen_exp_dirnames(cmdopts)]

        for d in dirs:
            exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                               d,
                                                               "exp_def.pkl"))
            for e in exp_def:
                if not (e[0] == ".//arena/distribute/entity" and e[1] == "quantity"):
                    continue

                index = dirs.index(d)
                i = int(index / len(self.criteria2.gen_attr_changelist()))
                j = index % len(self.criteria2.gen_attr_changelist())
                sizes[i][j] = int(e[2])

        return sizes

    def exp_scenario_name(self, exp_num: int) -> str:
        """
        Given the exp number in the batch, compute a valid, parsable scenario name. It is necessary
        to query this criteria after generating the changnelist in order to create generator classes
        for each experiment in the batch with the correct name and definition.

        Can only be called if constant density is one of the sub-criteria.
        """
        if isinstance(self.criteria1, constant_density.ConstantDensity):
            return self.criteria1.exp_scenario_name(int(exp_num /
                                                        len(self.criteria2.gen_attr_changelist())))
        elif isinstance(self.criteria2, constant_density.ConstantDensity):
            return self.criteria2.exp_scenario_name(int(exp_num % len(self.criteria2.gen_attr_changelist())))
        else:
            assert False, "FATAL: bivariate batch criteria does not contain constant density"

    def is_bivar(self) -> bool:
        return True

    def is_univar(self) -> bool:
        return False

    def sc_graph_labels(self, scenarios):
        raise NotImplementedError

    def sc_sort_scenarios(self, scenarios):
        raise NotImplementedError

    def graph_xticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        dirs = []
        for c1 in self.criteria1.gen_exp_dirnames(cmdopts):
            for x in self.gen_exp_dirnames(cmdopts):
                if c1 in x.split('+')[0]:
                    dirs.append(x)
                    break

        assert len(dirs) == len(self.criteria1.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad xvals calculation"
        return self.criteria1.graph_xticks(cmdopts, dirs)

    def graph_yticks(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        dirs = []
        for c2 in self.criteria2.gen_exp_dirnames(cmdopts):
            for x in self.gen_exp_dirnames(cmdopts):
                if c2 in x.split('+')[1]:
                    dirs.append(x)
                    break

        assert len(dirs) == len(self.criteria2.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad yvals calculation"

        return self.criteria2.graph_xticks(cmdopts, dirs)

    def graph_xticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        dirs = []
        for c1 in self.criteria1.gen_exp_dirnames(cmdopts):
            for x in self.gen_exp_dirnames(cmdopts):
                if c1 in x.split('+')[0]:
                    dirs.append(x)
                    break

        assert len(dirs) == len(self.criteria1.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad xticks calculation"
        return self.criteria1.graph_xticklabels(cmdopts, dirs)

    def graph_yticklabels(self, cmdopts: tp.Dict[str, str], exp_dirs: list = None) -> tp.List[float]:
        dirs = []
        for c2 in self.criteria2.gen_exp_dirnames(cmdopts):
            for y in self.gen_exp_dirnames(cmdopts):
                if c2 in y.split('+')[1]:
                    dirs.append(y)
                    break

        assert len(dirs) == len(self.criteria2.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad yticks calculation"
        return self.criteria2.graph_xticklabels(cmdopts, dirs)

    def graph_xlabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return self.criteria1.graph_xlabel(cmdopts)

    def graph_ylabel(self, cmdopts: tp.Dict[str, str]) -> str:
        return self.criteria2.graph_xlabel(cmdopts)

    def pm_query(self, query: str) -> bool:
        return self.criteria1.pm_query(query) or self.criteria2.pm_query(query)

    def set_batch_generation_root(self, root: str):
        self.batch_generation_root = root
        self.criteria1.batch_generation_root = root
        self.criteria2.batch_generation_root = root


def factory(main_config: dict, cmdopts: tp.Dict[str, str], args, scenario: str = None):
    if scenario is None:
        scenario = args.scenario

    if len(args.batch_criteria) == 1:
        ret = __Univarfactory(main_config, cmdopts, args.batch_criteria[0], scenario)
    elif len(args.batch_criteria) == 2:
        assert args.batch_criteria[0] != args.batch_criteria[1],\
            "FATAL: Duplicate batch criteria passed"
        ret = __Bivarfactory(main_config, cmdopts, args.batch_criteria, scenario)
    else:
        assert False, "FATAL: 1 or 2 batch criterias must be specified on the cmdline"

    return ret


def __Univarfactory(main_config: dict, cmdopts: tp.Dict[str, str], cli_arg: str, scenario):
    """
    Construct a batch criteria object from a single cmdline argument.
    """
    category = cli_arg.split('.')[0]

    module = __import__("core.variables.{0}".format(category), fromlist=["*"])
    ret = getattr(module, "factory")(cli_arg,
                                     main_config,
                                     cmdopts['generation_root'],
                                     scenario=scenario)()
    logging.info("Create univariate batch criteria '%s'",
                 ret.__class__.__name__)
    return ret


def __Bivarfactory(main_config: dict, cmdopts: tp.Dict[str, str], cli_arg: tp.List[str], scenario):
    criteria1 = __Univarfactory(main_config, cmdopts, cli_arg[0], scenario)
    criteria2 = __Univarfactory(main_config, cmdopts, cli_arg[1], scenario)
    ret = BivarBatchCriteria(criteria1, criteria2)

    logging.info("Create BivariateBatchCriteria from %s,%s",
                 ret.criteria1.__class__.__name__,
                 ret.criteria2.__class__.__name__)
    return ret
