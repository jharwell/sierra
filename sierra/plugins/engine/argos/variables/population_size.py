# Copyright 2020 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""Classes for the population size batch criteria.

See :ref:`plugins/engine/argos/bc/population-size` for usage documentation.

"""

# Core packages
import typing as tp
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.experiment import definition
from sierra.core import types
from sierra.core.variables import population_size
from sierra.core.graphs import bcbridge


@implements.implements(bcbridge.IGraphable)
@implements.implements(bc.IQueryableBatchCriteria)
class PopulationSize(population_size.PopulationSize):
    """A univariate range of swarm sizes used to define batch experiments.

    This class is a base class which should (almost) never be used on its
    own. Instead, the ``factory()`` function should be used to dynamically
    create derived classes expressing the user's desired size distribution.

    Note: Usage of this class assumes homogeneous swarms.

    Attributes:
        size_list: List of integer swarm sizes defining the range of the
                   variable for the batch experiment.

    """

    @staticmethod
    def gen_attr_changelist_from_list(
        sizes: tp.List[int],
    ) -> tp.List[definition.AttrChangeSet]:
        return [
            definition.AttrChangeSet(
                definition.AttrChange(".//arena/distribute/entity", "quantity", str(s))
            )
            for s in sizes
        ]

    def __init__(
        self,
        cli_arg: str,
        main_config: types.YAMLDict,
        batch_input_root: pathlib.Path,
        size_list: tp.List[int],
    ) -> None:
        population_size.PopulationSize.__init__(
            self, cli_arg, main_config, batch_input_root
        )
        self.size_list = size_list
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[definition.AttrChangeSet]:
        """
        Generate list of sets of changes for swarm sizes to define a batch experiment.
        """

        if not self.attr_changes:
            self.attr_changes = PopulationSize.gen_attr_changelist_from_list(
                self.size_list
            )
        return self.attr_changes

    def gen_exp_names(self) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ["exp" + str(x) for x in range(0, len(changes))]

    def n_agents(self, exp_num: int) -> int:
        return self.size_list[exp_num]

    def graph_info(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[tp.List[str]] = None,
    ) -> bcbridge.GraphInfo:
        info = bcbridge.GraphInfo(
            cmdopts,
            batch_output_root,
            exp_names if exp_names else self.gen_exp_names(),
        )
        info.xlabel = super().graph_xlabel(info.cmdopts)
        info.xticklabels = super().graph_xticklabels(
            info.cmdopts, info.batch_output_root, info.exp_names
        )
        info.xticks = super().graph_xticks(
            info.cmdopts, info.batch_output_root, info.exp_names
        )
        return info


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition."""
    max_sizes = population_size.parse(cli_arg)

    def __init__(self) -> None:
        PopulationSize.__init__(self, cli_arg, main_config, batch_input_root, max_sizes)

    return type(cli_arg, (PopulationSize,), {"__init__": __init__})  # type: ignore


__all__ = ["PopulationSize"]
