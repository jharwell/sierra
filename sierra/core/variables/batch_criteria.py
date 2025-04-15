# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Base classes used to define :term:`Batch Experiments <Batch Experiment>`.
"""
# Core packages
import typing as tp
import logging
import argparse
import copy
import pathlib

# 3rd party packages
import implements

from sierra.core.variables import base_variable
from sierra.core import utils
from sierra.core.experiment import definition


import sierra.core.plugin_manager as pm
from sierra.core import types, config


class IQueryableBatchCriteria(implements.Interface):
    """Mixin interface for criteria which can be queried during stage {1,2}.

    Used to extract additional information needed for configuring some
    :term:`Platforms <Platform>` and execution environments.

    """

    def n_agents(self, exp_num: int) -> int:
        """
        Return the # of agents used for a given :term:`Experiment`.
        """
        raise NotImplementedError


class IConcreteBatchCriteria(implements.Interface):
    """
    'Final' interface for user-visible batch criteria.
    """

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
                     batch_output_root: pathlib.Path,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        """Calculate X axis ticks for graph generation.

        Arguments:

            cmdopts: Dictionary of parsed command line options. Most batch
                     criteria will not need this, BUT it is available.

            batch_output_root: Root directory for all experimental output in the
                               batch. Needed in calculating graphs for batch
                               criteria when ``--exp-range`` is used.

            exp_names: If not None, then this list of directories will be used
                       to calculate the ticks, rather than the results of
                       :py:func:`BatchCriteria.gen_exp_names`. This argument will be non-None
                       when calling this function from within a bivariate batch
                       criteria.

        """

        raise NotImplementedError

    def graph_xticklabels(self,
                          cmdopts: types.Cmdopts,
                          batch_output_root: pathlib.Path,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        """Calculate X axis tick labels for graph generation.

        Arguments:

            cmdopts: Dictionary of parsed command line options. Most batch
                     criteria will not need this, BUT it is available.

            batch_output_root: Root directory for all experimental output in the
                               batch. Needed in calculating graphs for batch
                               criteria when ``--exp-range`` is used.
                               batch.

            exp_names: If not None, then these directories will be used to
                       calculate the labels, rather than the results of
                       ``gen_exp_names()``. This argument will be non-None
                       when calling this function from within a bivariate batch
                       criteria.

        """
        raise NotImplementedError

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        """Get the X-label for a graph.

        Returns:

            The X-label that should be used for the graphs of various
            performance measures across batch criteria.

        """
        raise NotImplementedError


class IBivarBatchCriteria(implements.Interface):
    """
    Interface for bivariate batch criteria(those with two univariate axes).
    """

    def graph_yticks(self,
                     cmdopts: types.Cmdopts,
                     batch_output_root: pathlib.Path,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        """
        Calculate Y axis ticks for graph generation.

        Arguments:

            cmdopts: Dictionary of parsed command line options. Most batch
                     criteria will not need this, BUT it is available.

            batch_output_root: Root directory for all experimental output in the
                               batch. Needed in calculating graphs for batch
                               criteria when ``--exp-range`` is used.

            exp_names: If not None, then these directories will be used to
                       calculate the labels, rather than the results of
                       ``gen_exp_names()``.
        """
        raise NotImplementedError

    def graph_yticklabels(self,
                          cmdopts: types.Cmdopts,
                          batch_output_root: pathlib.Path,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        """
        Calculate X axis ticks for graph generation.

        Arguments:

            cmdopts: Dictionary of parsed command line options. Most batch
                     criteria will not need this, BUT it is available.

            batch_output_root: Root directory for all experimental output in the
                               batch. Needed in calculating graphs for batch
                               criteria when ``--exp-range`` is used.

            exp_names: If not None, then these directories will be used to
                       calculate the labels, rather than the results of
                       ``gen_exp_names()``.
        """
        raise NotImplementedError

    def graph_ylabel(self, cmdopts: types.Cmdopts) -> str:
        """
        Get the Y-label for a graph.

        Returns:p

            The Y-label that should be used for the graphs of various
            performance measures across batch criteria. Only needed by bivar
            batch criteria.
        """
        raise NotImplementedError


class IBatchCriteriaType(implements.Interface):
    """Mixin interface for criteria for querying univariate/bivariate.

    """

    def is_bivar(self) -> bool:
        """
        Determine if the batch criteria is bivariate.

        Returns:

            `True` if this class is a bivariate batch criteria instance, and
            `False` otherwise.
        """
        raise NotImplementedError

    def is_univar(self) -> bool:
        """
        Determine if the batch criteria is univariate.

        Returns:

            `True` if this class is a univar batch criteria instance, and
            `False` otherwise.
        """
        raise NotImplementedError


@implements.implements(base_variable.IBaseVariable)
class BatchCriteria():
    """Defines experiments via  lists of sets of changes to make to an expdef.

    Attributes:
        cli_arg: Unparsed batch criteria string from command line.

        main_config: Parsed dictionary of main YAML configuration.

        batch_input_root: Absolute path to the directory where batch experiment
                          directories should be created.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path) -> None:
        self.cli_arg = cli_arg
        self.main_config = main_config
        self.batch_input_root = batch_input_root

        self.cat_str = cli_arg.split('.')[0]
        self.def_str = '.'.join(cli_arg.split('.')[1:])
        self.logger = logging.getLogger(__name__)

    # Stub out IBaseVariable because all concrete batch criteria only implement
    # a subset of them.
    def gen_attr_changelist(self) -> tp.List[definition.AttrChangeSet]:
        return []

    def gen_tag_rmlist(self) -> tp.List[definition.ElementRmList]:
        return []

    def gen_element_addlist(self) -> tp.List[definition.ElementAddList]:
        return []

    def gen_files(self) -> None:
        pass

    def gen_exp_names(self) -> tp.List[str]:
        """
        Generate list of experiment names from the criteria.

        Used for creating unique directory names for each experiment in the
        batch.

        Returns:

            List of experiments names for current experiment.

        """
        return []

    def arena_dims(self, cmdopts: types.Cmdopts) -> tp.List[utils.ArenaExtent]:
        """Get the arena dimensions used for each experiment in the batch.

        Not applicable to all criteria.

        Must be implemented on a per-platform basis, as different platforms have
        different means of computing the size of the arena.

        """
        module = pm.pipeline.get_plugin_module(cmdopts['platform'])
        assert hasattr(module, 'arena_dims_from_criteria'), \
            f"Platform plugin {module.__name__} does not implement arena_dims_from_criteria()"

        return module.arena_dims_from_criteria(self)

    def n_exp(self) -> int:
        from sierra.core.experiment import spec
        scaffold_spec = spec.scaffold_spec_factory(self)
        return scaffold_spec.n_exps

    def pickle_exp_defs(self, cmdopts: types.Cmdopts) -> None:
        from sierra.core.experiment import spec
        scaffold_spec = spec.scaffold_spec_factory(self)

        for exp in range(0, scaffold_spec.n_exps):
            exp_dirname = self.gen_exp_names()[exp]
            # Pickling of batch criteria experiment definitions is the FIRST set
            # of changes to be pickled--all other changes come after. We append
            # to the pickle file by default, which allows any number of
            # additional sets of changes to be written, BUT that can also lead
            # to errors if stage 1 is run multiple times before stage 4. So, we
            # DELETE the pickle file for each experiment here to make stage 1
            # idempotent.
            pkl_path = self.batch_input_root / exp_dirname / config.kPickleLeaf
            exp_defi = scaffold_spec.mods[exp]

            if not scaffold_spec.is_compound:
                exp_defi.pickle(pkl_path, delete=True)
            else:
                exp_defi[0].pickle(pkl_path, delete=True)
                exp_defi[1].pickle(pkl_path, delete=False)

    def scaffold_exps(self,
                      batch_def: definition.BaseExpDef,
                      cmdopts: types.Cmdopts) -> None:
        """Scaffold a batch experiment.

        Takes the raw template input file and apply expdef modifications from the
        batch criteria for all experiments, and save the result in each
        experiment's input directory.

        """

        from sierra.core.experiment import spec
        scaffold_spec = spec.scaffold_spec_factory(self, log=True)

        for i in range(0, scaffold_spec.n_exps):
            modsi = scaffold_spec.mods[i]
            expi_def = copy.deepcopy(batch_def)
            self._scaffold_expi(expi_def,
                                modsi,
                                scaffold_spec.is_compound,
                                i,
                                cmdopts)

        n_exp_dirs = len(list(self.batch_input_root.iterdir()))
        if scaffold_spec.n_exps != n_exp_dirs:
            msg1 = (f"Size of batch experiment ({scaffold_spec.n_exps}) != "
                    f"# exp dirs ({n_exp_dirs}): possibly caused by:")
            msg2 = (f"(1) Changing bc w/o changing the generation root "
                    f"({self.batch_input_root})")
            msg3 = (f"(2) Sharing {self.batch_input_root} between different "
                    f"batch criteria")

            self.logger.fatal(msg1)
            self.logger.fatal(msg2)
            self.logger.fatal(msg3)
            raise RuntimeError("Batch experiment size/# exp dir mismatch")

    def _scaffold_expi(self,
                       expi_def: definition.BaseExpDef,
                       modsi,
                       is_compound: bool,
                       i: int,
                       cmdopts: types.Cmdopts) -> None:
        exp_dirname = self.gen_exp_names()[i]
        exp_input_root = self.batch_input_root / exp_dirname

        utils.dir_create_checked(exp_input_root,
                                 exist_ok=cmdopts['exp_overwrite'])

        if not is_compound:
            self.logger.debug(("Applying %s expdef modifications from '%s' for "
                               "exp%s in %s"),
                              len(modsi),
                              self.cli_arg,
                              i,
                              exp_dirname)

            for mod in modsi:
                if isinstance(mod, definition.AttrChange):
                    expi_def.attr_change(mod.path, mod.attr, mod.value)
                elif isinstance(mod, definition.ElementAdd):
                    assert mod.path is not None, \
                        "Cannot add root {mode.tag} during scaffolding"
                    expi_def.element_add(mod.path,
                                         mod.tag,
                                         mod.attr,
                                         mod.allow_dup)
        else:
            self.logger.debug(("Applying %s expdef modifications from '%s' for "
                               "exp%s in %s"),
                              len(modsi[0]) + len(modsi[1]),
                              self.cli_arg,
                              i,
                              exp_dirname)

            # Mods are a tuple for compound specs: adds, changes. We do adds
            # first, in case some insane person wants to use the second batch
            # criteria to modify something they just added.
            for add in modsi[0]:
                expi_def.element_add(add.path,
                                     add.tag,
                                     add.attr,
                                     add.allow_dup)
            for chg in modsi[1]:
                expi_def.attr_change(chg.path,
                                     chg.attr,
                                     chg.value)

        # This will be the "template" input file used to generate the input
        # files for each experimental run in the experiment
        fmt = pm.pipeline.get_plugin_module(cmdopts['expdef'])
        wr_config = definition.WriterConfig([{'src_parent': None,
                                              'src_tag': fmt.root_querypath(),
                                              'opath_leaf': None,
                                              'new_children': None,
                                              'new_children_parent': None
                                              }])
        expi_def.write_config_set(wr_config)
        opath = utils.exp_template_path(cmdopts,
                                        self.batch_input_root,
                                        exp_dirname)
        expi_def.write(opath)


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

    def populations(self,
                    cmdopts: types.Cmdopts,
                    exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[int]:
        """
        Calculate system sizes used the batch experiment, sorted.

        Arguments:

            cmdopts: Dictionary of parsed command line options.

            exp_names: If is not `None`, then these directories will be used to
                       calculate the system sizes, rather than the results of
                       ``gen_exp_names()``.

        """
        sizes = []
        if exp_names is not None:
            names = exp_names
        else:
            names = self.gen_exp_names()

        module1 = pm.pipeline.get_plugin_module(cmdopts['platform'])
        module2 = pm.pipeline.get_plugin_module(cmdopts['expdef'])
        for d in names:
            path = self.batch_input_root / d / config.kPickleLeaf
            exp_def = module2.unpickle(path)

            sizes.append(module1.population_size_from_pickle(exp_def,
                                                             self.main_config,
                                                             cmdopts))
        return sizes


@implements.implements(IBivarBatchCriteria)
@implements.implements(IBatchCriteriaType)
@implements.implements(IQueryableBatchCriteria)
class BivarBatchCriteria(BatchCriteria):
    """
    Combination of the definition of two separate batch criteria.

    .. versionchanged:: 1.2.20

       Bivariate batch criteria can be compound: one criteria can create and
       the other modify expdef elements to create an experiment definition.

    """

    def __init__(self,
                 criteria1: IConcreteBatchCriteria,
                 criteria2: IConcreteBatchCriteria) -> None:
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

    def gen_attr_changelist(self) -> tp.List[definition.AttrChangeSet]:
        list1 = self.criteria1.gen_attr_changelist()
        list2 = self.criteria2.gen_attr_changelist()
        ret = []

        if list1 and list2:
            for l1 in list1:
                for l2 in list2:
                    ret.append(l1 | l2)

        elif list1:
            ret = list1

        elif list2:
            ret = list2

        return ret

    def gen_element_addlist(self) -> tp.List[definition.ElementAddList]:
        list1 = self.criteria1.gen_element_addlist()
        list2 = self.criteria2.gen_element_addlist()
        ret = []

        if list1 and list2:
            for l1 in list1:
                for l2 in list2:
                    l1.extend(l2)
                    ret.append(l1)
        elif list1:
            ret = list1

        elif list2:
            ret = list2

        return ret

    def gen_tag_rmlist(self) -> tp.List[definition.ElementRmList]:
        ret = self.criteria1.gen_tag_rmlist()
        ret.extend(self.criteria2.gen_tag_rmlist())
        return ret

    def gen_exp_names(self) -> tp.List[str]:
        """
        Generate a SORTED list of strings for all experiment names.

        These will be used as directory LEAF names--and don't include the
        parents.

        """
        list1 = self.criteria1.gen_exp_names()
        list2 = self.criteria2.gen_exp_names()
        ret = []

        for l1 in list1:
            for l2 in list2:
                ret.append('+'.join(['c1-' + l1, 'c2-' + l2]))

        return ret

    def populations(self, cmdopts: types.Cmdopts) -> tp.List[tp.List[int]]:
        """Generate a 2D array of system sizes used the batch experiment.

        Sizes are in the same order as the directories returned from
        `gen_exp_names()` for each criteria along each axis.

        """
        names = self.gen_exp_names()

        sizes = [[0 for col in self.criteria2.gen_exp_names()]
                 for row in self.criteria1.gen_exp_names()]

        n_chgs2 = len(self.criteria2.gen_attr_changelist())
        n_adds2 = len(self.criteria2.gen_element_addlist())

        module1 = pm.pipeline.get_plugin_module(cmdopts['platform'])
        module2 = pm.pipeline.get_plugin_module(cmdopts['expdef'])

        for d in names:
            pkl_path = self.batch_input_root / d / config.kPickleLeaf
            exp_def = module2.unpickle(pkl_path)

            index = names.index(d)
            i = int(index / (n_chgs2 + n_adds2))
            j = index % (n_chgs2 + n_adds2)
            sizes[i][j] = module1.population_size_from_pickle(exp_def,
                                                              self.main_config,
                                                              cmdopts)

        return sizes

    def exp_scenario_name(self, exp_num: int) -> str:
        """Given the expeperiment number, compute a parsable scenario name.

        It is necessary to query this function after generating the changelist
        in order to create generator classes for each experiment in the batch
        with the correct name and definition in some cases.

        Can only be called if constant density is one of the sub-criteria.

        """
        if hasattr(self.criteria1, 'exp_scenario_name'):
            return self.criteria1.exp_scenario_name(int(exp_num /
                                                        len(self.criteria2.gen_attr_changelist())))
        if hasattr(self.criteria2, 'exp_scenario_name'):
            return self.criteria2.exp_scenario_name(int(exp_num % len(self.criteria2.gen_attr_changelist())))
        else:
            raise RuntimeError(
                "Bivariate batch criteria does not contain constant density")

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
                     batch_output_root: pathlib.Path,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        names = []
        all_dirs = utils.exp_range_calc(cmdopts["exp_range"],
                                        batch_output_root,
                                        self)

        ynames = exp_names if exp_names else self.criteria1.gen_exp_names()

        for c1 in ynames:
            for x in all_dirs:
                leaf = x.name
                if c1 in leaf.split('+')[0]:
                    names.append(leaf)
                    break

        return self.criteria1.graph_xticks(cmdopts, batch_output_root, names)

    def graph_yticks(self,
                     cmdopts: types.Cmdopts,
                     batch_output_root: pathlib.Path,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        names = []
        all_dirs = utils.exp_range_calc(cmdopts["exp_range"],
                                        batch_output_root,
                                        self)
        xnames = exp_names if exp_names else self.criteria2.gen_exp_names()

        for c2 in xnames:
            for y in all_dirs:
                leaf = y.name
                if c2 in leaf.split('+')[1]:
                    names.append(leaf)
                    break

        return self.criteria2.graph_xticks(cmdopts, batch_output_root, names)

    def graph_xticklabels(self,
                          cmdopts: types.Cmdopts,
                          batch_output_root: pathlib.Path,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        """Generate x-axis labels.

        This bivariate function is one of the reasons the ``exp_names`` argument
        is needed as an optional: when calculating xticks using say criteria1,
        if the criteria uses :py:func:`populations()` in the process, the
        criteria's OWN ``gen_exp_names()`` will be used, which will result in
        bad directory name calculations.  This can be overcome by passing the
        list of exp names to use at THIS level.
        """
        names = []
        all_dirs = utils.exp_range_calc(cmdopts['exp_range'],
                                        batch_output_root,
                                        self)

        for c1 in self.criteria1.gen_exp_names():
            for x in all_dirs:
                leaf = x.name
                if c1 in leaf.split('+')[0]:
                    names.append(leaf)
                    break

        return self.criteria1.graph_xticklabels(cmdopts,
                                                batch_output_root,
                                                names)

    def graph_yticklabels(self,
                          cmdopts: types.Cmdopts,
                          batch_output_root: pathlib.Path,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        """Generate y-axis labels.

        This bivariate function is one of the reasons the ``exp_names`` argument
        is needed as an optional: when calculating yticks using criteria2, if
        the criteria uses :py:func:`populations()` in the process, the
        criteria's OWN ``gen_exp_names()`` will be used, which will result in
        bad directory name calculations.  This can be overcome by passing the
        list of exp names to use at THIS level.
        """
        names = []
        all_dirs = utils.exp_range_calc(cmdopts['exp_range'],
                                        batch_output_root,
                                        self)

        for c2 in self.criteria2.gen_exp_names():
            for x in all_dirs:
                leaf = x.name
                if c2 in leaf.split('+')[0]:
                    names.append(leaf)
                    break

        return self.criteria2.graph_xticklabels(cmdopts,
                                                batch_output_root,
                                                names)

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        return self.criteria1.graph_xlabel(cmdopts)

    def graph_ylabel(self, cmdopts: types.Cmdopts) -> str:
        return self.criteria2.graph_xlabel(cmdopts)

    def set_batch_input_root(self, root: pathlib.Path) -> None:
        self.batch_input_root = root
        self.criteria1.batch_input_root = root
        self.criteria2.batch_input_root = root

    def n_agents(self, exp_num: int) -> int:
        n_chgs2 = len(self.criteria2.gen_attr_changelist())
        n_adds2 = len(self.criteria2.gen_element_addlist())
        i = int(exp_num / (n_chgs2 + n_adds2))
        j = exp_num % (n_chgs2 + n_adds2)

        if hasattr(self.criteria1, 'n_agents'):
            return self.criteria1.n_agents(i)
        elif hasattr(self.criteria2, 'n_agents'):
            return self.criteria2.n_agents(j)

        raise NotImplementedError


def factory(main_config: types.YAMLDict,
            cmdopts: types.Cmdopts,
            batch_input_root: pathlib.Path,
            args: argparse.Namespace,
            scenario: tp.Optional[str] = None) -> IConcreteBatchCriteria:
    if scenario is None:
        scenario = args.scenario

    if len(args.batch_criteria) == 1:
        return __univar_factory(main_config,
                                cmdopts,
                                batch_input_root,
                                args.batch_criteria[0],
                                scenario)
    elif len(args.batch_criteria) == 2:
        assert args.batch_criteria[0] != args.batch_criteria[1], \
            "Duplicate batch criteria passed"
        return __bivar_factory(main_config,
                               cmdopts,
                               batch_input_root,
                               args.batch_criteria,
                               scenario)
    else:
        raise RuntimeError(
            "1 or 2 batch criterias must be specified on the cmdline")


def __univar_factory(main_config: types.YAMLDict,
                     cmdopts: types.Cmdopts,
                     batch_input_root: pathlib.Path,
                     cli_arg: str,
                     scenario) -> IConcreteBatchCriteria:
    """
    Construct a batch criteria object from a single cmdline argument.
    """
    category = cli_arg.split('.')[0]
    path = f'variables.{category}'

    module = pm.bc_load(cmdopts, category)
    bcfactory = getattr(module, "factory")

    if 5 in cmdopts['pipeline']:
        ret = bcfactory(cli_arg,
                        main_config,
                        cmdopts,
                        batch_input_root,
                        scenario=scenario)()
    else:
        ret = bcfactory(cli_arg, main_config, cmdopts, batch_input_root)()

    logging.info("Create univariate batch criteria '%s' from '%s'",
                 ret.__class__.__name__,
                 path)
    return ret  # type: ignore


def __bivar_factory(main_config: types.YAMLDict,
                    cmdopts: types.Cmdopts,
                    batch_input_root: pathlib.Path,
                    cli_arg: tp.List[str],
                    scenario: str) -> IConcreteBatchCriteria:
    criteria1 = __univar_factory(main_config,
                                 cmdopts,
                                 batch_input_root,
                                 cli_arg[0],
                                 scenario)

    criteria2 = __univar_factory(main_config,
                                 cmdopts,
                                 batch_input_root,
                                 cli_arg[1],
                                 scenario)

    # Project hook
    bc = pm.module_load_tiered(project=cmdopts['project'],
                               path='variables.batch_criteria')
    ret = bc.BivarBatchCriteria(criteria1, criteria2)

    logging.info("Created bivariate batch criteria from %s,%s",
                 ret.criteria1.__class__.__name__,
                 ret.criteria2.__class__.__name__)

    return ret  # type: ignore


__all__ = [
    'BatchCriteria',
    'IConcreteBatchCriteria',
    'UnivarBatchCriteria',
    'BivarBatchCriteria',
]
