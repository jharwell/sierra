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
        sizes: list[int],
    ) -> list[definition.AttrChangeSet]:
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
        size_list: list[int],
    ) -> None:
        population_size.PopulationSize.__init__(
            self, cli_arg, main_config, batch_input_root
        )
        self.size_list = size_list
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """
        Generate list of sets of changes for swarm sizes to define a batch experiment.
        """

        if not self.attr_changes:
            self.attr_changes = PopulationSize.gen_attr_changelist_from_list(
                self.size_list
            )
        return self.attr_changes

    def n_agents(self, exp_num: int) -> int:
        return self.size_list[exp_num]


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> PopulationSize:
    """Create a :class:`PopulationSize` derived class from the cmdline definition."""
    max_sizes = population_size.parse(cli_arg)

    return PopulationSize(cli_arg, main_config, batch_input_root, max_sizes)


__all__ = ["PopulationSize"]
