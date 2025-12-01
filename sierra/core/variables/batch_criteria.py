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
import itertools

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import base_variable
from sierra.core import utils
from sierra.core.experiment import definition
import sierra.core.plugin as pm
from sierra.core import types, config
from sierra.core.graphs import bcbridge


class IQueryableBatchCriteria(implements.Interface):
    """Mixin interface for criteria which can be queried during stage {1,2}.

    Used to extract additional information needed for configuring some
    :term:`Engines <Engine>` and execution environments.

    """

    def n_agents(self, exp_num: int) -> int:
        """
        Return the # of agents used for a given :term:`Experiment`.
        """
        raise NotImplementedError


@implements.implements(base_variable.IBaseVariable)
class BaseBatchCriteria:
    """Defines experiments via  lists of sets of changes to make to an expdef.

    Attributes:
        cli_arg: Unparsed batch criteria string from command line.

        main_config: Parsed dictionary of main YAML configuration.

        batch_input_root: Absolute path to the directory where batch experiment
                          directories should be created.

    """

    def __init__(
        self, cli_arg: str, main_config: types.YAMLDict, batch_input_root: pathlib.Path
    ) -> None:

        # 2025-09-21 [JRH]: The "name" of the batch criteria is just whatever is
        # passed on the cmdline.
        self.name = cli_arg
        self.main_config = main_config
        self.batch_input_root = batch_input_root

        self.cat_str = cli_arg.split(".")[0]
        self.def_str = ".".join(cli_arg.split(".")[1:])
        self.logger = logging.getLogger(__name__)

    # Stub out IBaseVariable because all concrete batch criteria only implement
    # a subset of them.
    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        return []

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        return []

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        return []

    def gen_files(self) -> None:
        pass

    def cardinality(self) -> int:
        return -1

    def gen_exp_names(self) -> list[str]:
        raise NotImplementedError

    def computable_exp_scenario_name(self) -> bool:
        return False

    def arena_dims(self, cmdopts: types.Cmdopts) -> list[utils.ArenaExtent]:
        """Get the arena dimensions used for each experiment in the batch.

        Not applicable to all criteria.

        Must be implemented on a per-engine basis, as different engines have
        different means of computing the size of the arena.

        """
        module = pm.pipeline.get_plugin_module(cmdopts["engine"])
        assert hasattr(
            module, "arena_dims_from_criteria"
        ), f"Engine plugin {module.__name__} does not implement arena_dims_from_criteria()"

        return module.arena_dims_from_criteria(self)

    def n_exp(self) -> int:
        from sierra.core.experiment import spec  # noqa: PLC0415

        scaffold_spec = spec.scaffold_spec_factory(self)
        return scaffold_spec.n_exps

    def pickle_exp_defs(self, cmdopts: types.Cmdopts) -> None:
        from sierra.core.experiment import spec  # noqa: PLC0415

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
            pkl_path = self.batch_input_root / exp_dirname / config.PICKLE_LEAF
            exp_defi = scaffold_spec.mods[exp]

            if not scaffold_spec.is_compound:
                exp_defi.pickle(pkl_path, delete=True)
            else:
                exp_defi[0].pickle(pkl_path, delete=True)
                exp_defi[1].pickle(pkl_path, delete=False)

    def scaffold_exps(
        self, batch_def: definition.BaseExpDef, cmdopts: types.Cmdopts
    ) -> None:
        """Scaffold a batch experiment.

        Takes the raw template input file and apply expdef modifications from the
        batch criteria for all experiments, and save the result in each
        experiment's input directory.

        """
        from sierra.core.experiment import spec  # noqa: PLC0415

        scaffold_spec = spec.scaffold_spec_factory(self, log=True)

        for i in range(0, scaffold_spec.n_exps):
            modsi = scaffold_spec.mods[i]
            expi_def = copy.deepcopy(batch_def)
            self._scaffold_expi(expi_def, modsi, scaffold_spec.is_compound, i, cmdopts)

        n_exp_dirs = len(list(self.batch_input_root.iterdir()))
        if scaffold_spec.n_exps != n_exp_dirs:
            msg1 = (
                f"Size of batch experiment ({scaffold_spec.n_exps}) != "
                f"# exp dirs ({n_exp_dirs}): possibly caused by:"
            )
            msg2 = (
                f"(1) Changing bc w/o changing the generation root "
                f"({self.batch_input_root})"
            )
            msg3 = (
                f"(2) Sharing {self.batch_input_root} between different "
                f"batch criteria"
            )

            self.logger.fatal(msg1)
            self.logger.fatal(msg2)
            self.logger.fatal(msg3)
            raise RuntimeError("Batch experiment size/# exp dir mismatch")

    def _scaffold_expi(
        self,
        expi_def: definition.BaseExpDef,
        modsi,
        is_compound: bool,
        i: int,
        cmdopts: types.Cmdopts,
    ) -> None:

        exp_dirname = self.gen_exp_names()[i]
        exp_input_root = self.batch_input_root / exp_dirname

        utils.dir_create_checked(exp_input_root, exist_ok=cmdopts["exp_overwrite"])

        if not is_compound:
            self.logger.debug(
                ("Applying %s expdef mods from '%s' for exp%s in %s"),
                len(modsi),
                self.name,
                i,
                exp_dirname,
            )

            for mod in modsi:
                if isinstance(mod, definition.AttrChange):
                    expi_def.attr_change(mod.path, mod.attr, mod.value)
                elif isinstance(mod, definition.ElementAdd):
                    assert (
                        mod.path is not None
                    ), "Cannot add root {mode.tag} during scaffolding"
                    expi_def.element_add(mod.path, mod.tag, mod.attr, mod.allow_dup)
                elif isinstance(mod, definition.ElementRm):
                    expi_def.element_remove(mod.path, mod.tag)
        else:
            self.logger.debug(
                ("Applying %s expdef modifications from '%s' for exp%s in %s"),
                len(modsi[0]) + len(modsi[1]),
                self.name,
                i,
                exp_dirname,
            )

            # Mods are a tuple for compound specs: adds, changes. We do adds
            # first, in case some insane person wants to use the second batch
            # criteria to modify something they just added.
            for add in modsi[0]:
                expi_def.element_add(add.path, add.tag, add.attr, add.allow_dup)
            for chg in modsi[1]:
                expi_def.attr_change(chg.path, chg.attr, chg.value)

        # This will be the "template" input file used to generate the input
        # files for each experimental run in the experiment
        fmt = pm.pipeline.get_plugin_module(cmdopts["expdef"])
        wr_config = definition.WriterConfig(
            [
                {
                    "src_parent": None,
                    "src_tag": fmt.root_querypath(),
                    "opath_leaf": None,
                    "new_children": None,
                    "new_children_parent": None,
                }
            ]
        )
        expi_def.write_config_set(wr_config)
        opath = utils.exp_template_path(cmdopts, self.batch_input_root, exp_dirname)
        expi_def.write(opath)


class UnivarBatchCriteria(BaseBatchCriteria):
    """
    Base class for a univariate batch criteria.
    """

    def cardinality(self) -> int:
        return 1

    def gen_exp_names(self) -> list[str]:
        return [f"c1-exp{i}" for i in range(0, self.n_exp())]

    def populations(
        self, cmdopts: types.Cmdopts, exp_names: tp.Optional[list[str]] = None
    ) -> list[int]:
        """
        Calculate system sizes used the batch experiment, sorted.

        Arguments:

            cmdopts: Dictionary of parsed command line options.

            exp_names: If is not `None`, then these directories will be used to
                       calculate the system sizes, rather than the results of
                       ``gen_exp_names()``.

        """
        sizes = []
        names = exp_names if exp_names is not None else self.gen_exp_names()

        module1 = pm.pipeline.get_plugin_module(cmdopts["engine"])
        module2 = pm.pipeline.get_plugin_module(cmdopts["expdef"])
        for d in names:
            path = self.batch_input_root / d / config.PICKLE_LEAF
            exp_def = module2.unpickle(path)

            sizes.append(
                module1.population_size_from_pickle(exp_def, self.main_config, cmdopts)
            )

        return sizes


@implements.implements(bcbridge.IGraphable)
@implements.implements(IQueryableBatchCriteria)
class XVarBatchCriteria(BaseBatchCriteria):
    """
    N-dimensional multiple :class:`sierra.core.variables.batch_criteria.UnivarBatchCriteria`.

    .. versionchanged:: 1.2.20

       Batch criteria can be compound: one criteria can create and the other
       modify expdef elements to create an experiment definition.
    """

    def __init__(self, criterias: list[BaseBatchCriteria]) -> None:
        BaseBatchCriteria.__init__(
            self,
            "+".join([c.name for c in criterias]),
            criterias[0].main_config,
            criterias[0].batch_input_root,
        )
        self.criterias = criterias

    def cardinality(self) -> int:
        return len(self.criterias)

    def computable_exp_scenario_name(self) -> bool:
        return any(c.computable_exp_scenario_name() for c in self.criterias)

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        changes = [c.gen_attr_changelist() for c in self.criterias]

        # Flatten each list of sets into a single list of items
        flattened_lists = []

        for list_of_sets in changes:
            flattened_list = list(list_of_sets)
            flattened_lists.append(flattened_list)

        # Use itertools.product to get all combinations
        result = []
        for combination in itertools.product(*flattened_lists):
            combined = definition.AttrChangeSet()
            # Add all changes from each AttrChangeSet in the combination
            for change_set in combination:
                for change in change_set:
                    combined.add(change)

            result.append(combined)

        return result

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        adds = [c.gen_element_addlist() for c in self.criterias]

        # Create combinations and combine ElementAddList objects
        result = []
        for combo in itertools.product(*adds):
            combined = definition.ElementAddList()

            # Add all ElementAdd objects from each ElementAddList in the combo
            for elem_add_list in combo:
                for elem_add in elem_add_list:
                    combined.append(elem_add)

            result.append(combined)

        return result

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        rms = [c.gen_tag_rmlist() for c in self.criterias]

        # Create combinations and combine ElementRmList objects
        result = []
        for combo in itertools.product(*rms):
            combined = definition.ElementRmList()

            # Add all ElementRm objects from each ElementRmList in the combo
            for elem_rm_list in combo:
                for elem_rm in elem_rm_list:
                    combined.append(elem_rm)
            result.append(combined)

        return result

    def gen_exp_names(self) -> list[str]:
        """
        Generate a SORTED list of strings for all experiment names.

        These will be used as directory LEAF names, and don't include the
        parents. Basically, this is a flattened list of permutations of all
        ``gen_exp_names()`` for each batch criteria.

        """

        # Collect all criteria lists with their prefixes
        criteria_lists = []
        for i, criteria in enumerate(self.criterias, 1):
            prefixed_names = [f"c{i}-exp{j}" for j in range(0, criteria.n_exp())]
            criteria_lists.append(prefixed_names)

        # Generate all combinations using itertools.product
        return [
            "+".join(combination) for combination in itertools.product(*criteria_lists)
        ]

    def populations(self, cmdopts: types.Cmdopts) -> list:
        """Generate a N-D array of system sizes used the batch experiment.

        Sizes are in the same order as the directories returned from
        ``gen_exp_names()`` for each criteria along each axis.

        """
        names = self.gen_exp_names()
        criteria_dims = []
        criteria_counts = []

        for criteria in self.criterias:
            exp_names = criteria.gen_exp_names()
            n_chgs = len(criteria.gen_attr_changelist())
            n_adds = len(criteria.gen_element_addlist())

            criteria_dims.append(len(exp_names))
            criteria_counts.append(n_chgs + n_adds)

        # Create multi-dimensional nested list initialized with zeros
        def create_nested_list(dimensions: list[int]) -> list:
            if len(dimensions) == 1:
                return [0] * dimensions[0]
            return [create_nested_list(dimensions[1:]) for _ in range(dimensions[0])]

        sizes = create_nested_list(criteria_dims)

        # Get plugin modules
        module1 = pm.pipeline.get_plugin_module(cmdopts["engine"])
        module2 = pm.pipeline.get_plugin_module(cmdopts["expdef"])

        # Calculate total combinations for index conversion
        total_combinations = 1
        for count in criteria_counts:
            total_combinations *= count

        for d in names:
            pkl_path = self.batch_input_root / d / config.PICKLE_LEAF
            exp_def = module2.unpickle(pkl_path)

            # Convert linear index to multi-dimensional indices
            index = names.index(d)
            indices = []
            remaining_index = index

            for i in range(len(criteria_counts)):
                # Calculate stride for this dimension
                stride = 1
                for j in range(i + 1, len(criteria_counts)):
                    stride *= criteria_counts[j]

                # Calculate index for this dimension
                dim_index = remaining_index // stride
                indices.append(dim_index)
                remaining_index = remaining_index % stride

            # Set the population size at the calculated indices
            current_level = sizes
            for _, idx in enumerate(indices[:-1]):
                current_level = current_level[idx]
            current_level[indices[-1]] = module1.population_size_from_pickle(
                exp_def, self.main_config, cmdopts
            )

        return sizes

    def exp_scenario_name(self, exp_num: int) -> str:
        """Given the experiment number, compute a parsable scenario name.

        It is necessary to query this function after generating the changelist
        in order to create generator classes for each experiment in the batch
        with the correct name and definition in some cases.

        Can only be called if constant density is one of the sub-criteria.

        """
        for criteria in self.criterias:
            if hasattr(criteria, "exp_scenario_name"):
                return criteria.exp_scenario_name(
                    int(exp_num / len(criteria.gen_attr_changelist()))
                )
        raise RuntimeError(
            "Batch criteria does not define 'exp_scenario_name()' required for constant density scenarios"
        )

    def graph_info(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[list[str]] = None,
    ) -> bcbridge.GraphInfo:
        info = bcbridge.GraphInfo(
            cmdopts,
            batch_output_root,
            self.gen_exp_names(),
        )

        # 2025-07-08 [JRH]: Eventually, this will be replaced with axes
        # selection, but for now, limiting to bivariate is the simpler way to
        # go.
        assert (
            len(self.criterias) <= 2
        ), "Only {univar,bivar} batch criteria graph generation currently supported"

        exp_names = self.gen_exp_names()
        if self.cardinality() == 1:
            info1 = self.criterias[0].graph_info(
                cmdopts, exp_names=exp_names, batch_output_root=batch_output_root
            )

            info.xticks = info1.xticks
            info.xlabel = info1.xlabel
            info.xticklabels = info1.xticklabels

        elif self.cardinality() == 2:
            c1_xnames = [f"c1-exp{i}" for i in range(0, self.criterias[0].n_exp())]
            xnames = [d for d in self.gen_exp_names() if any(x in d for x in c1_xnames)]
            c2_ynames = [f"c2-exp{i}" for i in range(0, self.criterias[1].n_exp())]
            ynames = [d for d in self.gen_exp_names() if any(y in d for y in c2_ynames)]

            info1 = self.criterias[0].graph_info(
                cmdopts, exp_names=xnames, batch_output_root=batch_output_root
            )
            info2 = self.criterias[1].graph_info(
                cmdopts, exp_names=ynames, batch_output_root=batch_output_root
            )
            info.xticks = info1.xticks
            info.xticklabels = info1.xticklabels
            info.yticks = info2.xticks
            info.xlabel = info1.xlabel
            info.ylabel = info2.xlabel
            info.yticklabels = info2.xticklabels

        return info

    def set_batch_input_root(self, root: pathlib.Path) -> None:
        self.batch_input_root = root
        for criteria in self.criterias:
            criteria.batch_input_root = root

    def n_agents(self, exp_num: int) -> int:
        # Calculate dimensions and counts for each criteria
        criteria_counts = []
        for criteria in self.criterias:
            n_chgs = len(criteria.gen_attr_changelist())
            n_adds = len(criteria.gen_element_addlist())
            criteria_counts.append(n_chgs + n_adds)

        # Convert linear experiment number to multi-dimensional indices
        indices = []
        remaining_exp_num = exp_num

        for i in range(len(criteria_counts)):
            # Calculate stride for this dimension
            stride = 1
            for j in range(i + 1, len(criteria_counts)):
                stride *= criteria_counts[j]

            # Calculate index for this dimension
            dim_index = remaining_exp_num // stride
            indices.append(dim_index)
            remaining_exp_num = remaining_exp_num % stride

        # Find the first criteria that has an n_agents method and use it
        for i, criteria in enumerate(self.criterias):
            if hasattr(criteria, "n_agents"):
                return criteria.n_agents(indices[i])

        # If no criteria has n_agents method, raise an error
        raise AttributeError("No criteria has an 'n_agents' method")


def univar_factory(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    cli_arg: str,
    scenario,
) -> BaseBatchCriteria:
    """
    Construct a univariate batch criteria object from a single cmdline argument.
    """
    category = cli_arg.split(".")[0]
    path = f"variables.{category}"

    module = pm.bc_load(cmdopts, category)
    bcfactory = module.factory

    if 5 in cmdopts["pipeline"]:
        ret = bcfactory(
            cli_arg, main_config, cmdopts, batch_input_root, scenario=scenario
        )
    else:
        ret = bcfactory(cli_arg, main_config, cmdopts, batch_input_root)

    logging.info("Create univariate batch criteria %s from %s", ret.name, path)
    return ret


def factory(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    args: argparse.Namespace,
    scenario: tp.Optional[str] = None,
) -> BaseBatchCriteria:
    """
    Construct a multivariate batch criteria object from cmdline input.
    """
    criterias = [
        univar_factory(main_config, cmdopts, batch_input_root, arg, scenario)
        for arg in args.batch_criteria
    ]

    # Project hook
    bc = pm.module_load_tiered(
        project=cmdopts["project"], path="variables.batch_criteria"
    )
    ret = bc.XVarBatchCriteria(criterias)

    logging.info(
        "Created %s-D batch criteria from %s",
        len(criterias),
        ",".join([c.name for c in criterias]),
    )

    return ret


__all__ = [
    "BaseBatchCriteria",
    "UnivarBatchCriteria",
    "XVarBatchCriteria",
]
