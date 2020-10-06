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
import typing as tp
import implements

import core.utils
import core.xml_luigi
from core.variables import constant_density, base_variable


class IConcreteBatchCriteria(implements.Interface):
    """
    'Final' interface that user-visible batch criteria variables need to implement to indicate that
    they can be used as such, as they contain no virtual methods.
    """

    def graph_xticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then this list of directories directories will be used to
                      calculate the ticks, rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the X axis tick values for graph generation.

        """

    def graph_xticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the labels,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the X axis tick labels for graph generation.

        """

    def graph_xlabel(self, cmdopts: dict) -> str:
        """
        Returns:
            The X-label that should be used for the graphs of various performance measures across
            batch criteria.
        """

    def pm_query(self, pm: str) -> bool:
        """
        Arguments:
            pm: A possible performance measure to generate from the results of the batched
                experiment defined by this object.

        Returns:
            `True` if the specified pm should be generated for the current object, and
            `False` otherwise.
        """

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        """
        Do the inter-experiment graphs for this batch criteria exclude exp0 ?

        Needed for correct stage5 comparison graph generation for univariate criteria. 
        """


class IBivarBatchCriteria(implements.Interface):
    def graph_yticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the ticks,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of criteria-specific values to use as the Y axis tick values for graph
            generation.

        """

    def graph_yticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:
        """

        Arguments:
            cmdopts: Dictionary of parsed command line options.
            exp_dirs: If not None, then these directories will be used to calculate the labels,
                      rather than the results of gen_exp_dirnames().

        Returns:
            A list of values to use as the Y axis tick labels for graph generation.

        """

    def graph_ylabel(self, cmdopts: dict) -> str:
        """
        Returns:
            The Y-label that should be used for the graphs of various performance measures across
            batch criteria. Only needed by bivar batch criteria.
        """


class IBatchCriteriaType(implements.Interface):
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


@implements.implements(base_variable.IBaseVariable)
class BatchCriteria():
    """
    Defines the list of sets of changes to make to a template input file in order to run a related
    set of of experiments.

    Attributes:
        cli_arg: Unparsed batch criteria string from command line.
        main_config: Parsed dictionary of main YAML configuration.
        batch_input_root: Absolute path to the directory where batch experiment directories
                               should be created.

    """

    kPMNames = ['raw', 'scalability', 'self-org', 'flexibility', 'robustness']

    def __init__(self,
                 cli_arg: str,
                 main_config: dict,
                 batch_input_root: str) -> None:
        self.cli_arg = cli_arg
        self.main_config = main_config
        self.batch_input_root = batch_input_root

        self.cat_str = cli_arg.split('.')[0]
        self.def_str = '.'.join(cli_arg.split('.')[1:])

    # Stub out IBaseVariable because all concrete batch criteria only implement a subset of them.

    def gen_attr_changelist(self) -> list:
        return []

    def gen_tag_rmlist(self) -> list:
        return []

    def gen_tag_addlist(self) -> list:
        return []

    def gen_exp_dirnames(self, cmdopts: dict) -> tp.List[str]:
        """
        Generate list of strings from the current changelist to use for directory names within a
        batched experiment.

        Returns:
            List of directory names for current experiment

        """
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
                    dims.append(core.utils.ArenaExtent((int(x), int(y), int(z))))
        assert len(dims) > 0, "Scenario dimensions not contained in batch criteria"
        return dims

    def n_exp(self) -> int:
        exps = [i for i in os.listdir(self.batch_input_root) if
                os.path.isdir(os.path.join(self.batch_input_root, i)) and i not in
                self.main_config['sierra']['collate_csv_leaf']]
        return len(exps)

    def pickle_exp_defs(self, cmdopts: dict):
        defs = list(self.gen_attr_changelist())
        for i, exp_def in enumerate(defs):
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            pkl_path = os.path.join(self.batch_input_root, exp_dirname, 'exp_def.pkl')
            with open(pkl_path, 'ab') as f:
                pickle.dump(exp_def, f)

    def scaffold_exps(self,
                      xml_luigi: core.xml_luigi.XMLLuigi,
                      batch_config_leaf: str,
                      cmdopts: dict):
        """
        Scaffold a batched experiment by taking the raw template input file and applying the XML
        attribute changes to it, and saving the result in the experiment input directory in each
        experiment in the batch.

        Note that batch criteria which use XML tag additions are NOT valid, because those
        necessarily have a dictionary of attr,value pairs for the new tag to add, and these cannot
        be pickled for successful retrieval later.

        """
        assert len(self.gen_tag_addlist()) == 0, "FATAL: Batch criteria cannot add XML tags"
        chg_defs = list(self.gen_attr_changelist())
        n_exps = len(chg_defs)

        logging.info("Scaffolding experiments from batch criteria '%s' by modifying %s XML tags",
                     self.cli_arg,
                     len(chg_defs[0]))

        for i, defi in enumerate(chg_defs):
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            exp_input_root = os.path.join(self.batch_input_root,
                                          str(exp_dirname))
            logging.debug("Applying %s XML attribute changes from batch criteria generator '%s' for exp%s in %s",
                          len(defi),
                          self.cli_arg,
                          i,
                          exp_dirname)

            core.utils.dir_create_checked(exp_input_root, exist_ok=cmdopts['exp_overwrite'])
            for changes_i in defi:
                try:
                    path, attr, value = changes_i
                except ValueError:
                    logging.fatal("%s XML changes not a 3-tuple (path,attr,value)", changes_i)
                    raise

                xml_luigi.attr_change(path, attr, value)

            xml_luigi.write(os.path.join(exp_input_root,
                                         batch_config_leaf))

        n_exp_dirs = len(os.listdir(self.batch_input_root))
        if n_exps != n_exp_dirs:
            msg1 = "Size of batched experiment ({0}) != # exp dirs ({1}): possibly caused by:".format(n_exps,
                                                                                                      n_exp_dirs)
            msg2 = "(1) Changing batch criteria without changing the generation root ({0})".format(
                self.batch_input_root)
            msg3 = "(2) Sharing {0} between different batch criteria".format(
                self.batch_input_root)
            logging.fatal(msg1)
            logging.fatal(msg2)
            logging.fatal(msg3)
            raise ValueError("Batch experiment size/# exp dir mismatch")


@implements.implements(IBatchCriteriaType)
class UnivarBatchCriteria(BatchCriteria):
    """
    Base class for a univariate batch criteria.
    """
    #
    # IBatchCriteriaType overrides
    #

    def is_bivar(self) -> bool:
        return False

    def is_univar(self) -> bool:
        return True

    def populations(self, cmdopts: dict, exp_dirs: list=None) -> tp.List[int]:
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
            exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_input_root,
                                                               d,
                                                               "exp_def.pkl"))
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))
        return sizes


@implements.implements(IBivarBatchCriteria)
@implements.implements(IBatchCriteriaType)
class BivarBatchCriteria(BatchCriteria):
    """
    Combination of the definition of two separate batch criteria.

    """

    def __init__(self, criteria1, criteria2) -> None:
        BatchCriteria.__init__(self,
                               '+'.join([criteria1.cli_arg, criteria2.cli_arg]),
                               criteria1.main_config,
                               criteria1.batch_input_root)
        self.criteria1 = criteria1
        self.criteria2 = criteria2
    #
    # IBatchCriteriaType overrides
    #

    def is_bivar(self) -> bool:
        return True

    def is_univar(self) -> bool:
        return False

    def gen_attr_changelist(self) -> list:
        list1 = self.criteria1.gen_attr_changelist()
        list2 = self.criteria2.gen_attr_changelist()
        ret = []

        for l1 in list1:
            for l2 in list2:
                ret.append(l1 | l2)

        return ret

    def gen_tag_rmlist(self) -> list:
        ret = self.criteria1.gen_tag_rmlist()
        ret.extend(self.criteria2.gen_tag_rmlist())
        return ret

    def gen_exp_dirnames(self, cmdopts: dict) -> tp.List[str]:
        """
        Generates a SORTED list of strings for all X/Y axis directories for the bivariate
        experiments, or both X and Y.
        """
        list1 = self.criteria1.gen_exp_dirnames(cmdopts)
        list2 = self.criteria2.gen_exp_dirnames(cmdopts)
        ret = []

        for l1 in list1:
            for l2 in list2:
                ret.append('+'.join(['c1-' + l1, 'c2-' + l2]))

        return ret

    def populations(self, cmdopts: dict) -> tp.List[tp.List[int]]:
        """
        Generate a 2D array of swarm swarm sizes used the batched experiment, in the same order as
        the directories returned from `gen_exp_dirnames()` for each criteria along each axis.

        """
        dirs = self.gen_exp_dirnames(cmdopts)

        sizes = [[0 for col in self.criteria2.gen_exp_dirnames(
            cmdopts)] for row in self.criteria1.gen_exp_dirnames(cmdopts)]

        n_chgs = len(self.criteria2.gen_attr_changelist())
        n_adds = len(self.criteria2.gen_tag_addlist())

        assert n_chgs == 0 or n_adds == 0,\
            "FATAL: Criteria defines both XML attribute changes and XML tag additions"

        for d in dirs:
            exp_def = core.utils.unpickle_exp_def(os.path.join(self.batch_input_root,
                                                               d,
                                                               "exp_def.pkl"))
            for path, attr, value in exp_def:
                if not (path == ".//arena/distribute/entity" and attr == "quantity"):
                    continue
                index = dirs.index(d)
                i = int(index / (n_chgs + n_adds))
                j = index % (n_chgs + n_adds)
                sizes[i][j] = int(value)

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

    def graph_xticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:
        dirs = []
        all_dirs = core.utils.exp_range_calc(cmdopts,
                                             cmdopts['batch_output_root'],
                                             self)

        for c1 in self.criteria1.gen_exp_dirnames(cmdopts):
            for x in all_dirs:
                leaf = os.path.split(x)[1]
                if c1 in leaf.split('+')[0]:
                    dirs.append(leaf)
                    break

        return self.criteria1.graph_xticks(cmdopts, dirs)

    def graph_yticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:
        dirs = []
        all_dirs = core.utils.exp_range_calc(cmdopts,
                                             cmdopts['batch_output_root'],
                                             self)

        for c2 in self.criteria2.gen_exp_dirnames(cmdopts):
            for y in all_dirs:
                leaf = os.path.split(y)[1]
                if c2 in leaf.split('+')[1]:
                    dirs.append(leaf)
                    break

        return self.criteria2.graph_xticks(cmdopts, dirs)

    def graph_xticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:
        dirs = []
        all_dirs = core.utils.exp_range_calc(cmdopts,
                                             cmdopts['batch_output_root'],
                                             self)

        for c1 in self.criteria1.gen_exp_dirnames(cmdopts):
            for x in all_dirs:
                leaf = os.path.split(x)[1]
                if c1 in leaf.split('+')[0]:
                    dirs.append(leaf)
                    break

        return self.criteria1.graph_xticklabels(cmdopts, dirs)

    def graph_yticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:
        dirs = []
        all_dirs = core.utils.exp_range_calc(cmdopts,
                                             cmdopts['batch_output_root'],
                                             self)

        for c2 in self.criteria2.gen_exp_dirnames(cmdopts):
            for y in all_dirs:
                leaf = os.path.split(y)[1]
                if c2 in leaf.split('+')[1]:
                    dirs.append(leaf)
                    break

        return self.criteria2.graph_xticklabels(cmdopts, dirs)

    def graph_xlabel(self, cmdopts: dict) -> str:
        return self.criteria1.graph_xlabel(cmdopts)

    def graph_ylabel(self, cmdopts: dict) -> str:
        return self.criteria2.graph_xlabel(cmdopts)

    def pm_query(self, pm: str) -> bool:
        return self.criteria1.pm_query(pm) or self.criteria2.pm_query(pm)

    def set_batch_input_root(self, root: str):
        self.batch_input_root = root
        self.criteria1.batch_input_root = root
        self.criteria2.batch_input_root = root


def factory(main_config: dict, cmdopts: dict, args, scenario: str = None):
    if scenario is None:
        scenario = args.scenario

    if len(args.batch_criteria) == 1:
        ret = __univar_factory(main_config, cmdopts, args.batch_criteria[0], scenario)
    elif len(args.batch_criteria) == 2:
        assert args.batch_criteria[0] != args.batch_criteria[1],\
            "FATAL: Duplicate batch criteria passed"
        ret = __bivar_factory(main_config, cmdopts, args.batch_criteria, scenario)
    else:
        assert False, "FATAL: 1 or 2 batch criterias must be specified on the cmdline"

    return ret


def __univar_factory(main_config: dict, cmdopts: dict, cli_arg: str, scenario):
    """
    Construct a batch criteria object from a single cmdline argument.
    """
    category = cli_arg.split('.')[0]
    module = __import__("core.variables.{0}".format(category), fromlist=["*"])
    ret = getattr(module, "factory")(cli_arg,
                                     main_config,
                                     cmdopts['batch_input_root'],
                                     scenario=scenario)()
    logging.info("Create univariate batch criteria '%s'",
                 ret.__class__.__name__)
    return ret


def __bivar_factory(main_config: dict, cmdopts: dict, cli_arg: tp.List[str], scenario):
    criteria1 = __univar_factory(main_config, cmdopts, cli_arg[0], scenario)
    criteria2 = __univar_factory(main_config, cmdopts, cli_arg[1], scenario)
    ret = BivarBatchCriteria(criteria1, criteria2)

    logging.info("Create BivariateBatchCriteria from %s,%s",
                 ret.criteria1.__class__.__name__,
                 ret.criteria2.__class__.__name__)
    return ret


__api__ = [
    'BatchCriteria',
    'UnivarBatchCriteria',
    'BivarBatchCriteria',
]
