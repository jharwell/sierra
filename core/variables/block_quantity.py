# Copyright 2020 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
#
# SIERRA is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SIERRA.  If not, see <http://www.gnu.org/licenses/
"""
Classes for the block quantity batch criteria. See :ref:`ln-bc-block-quantity` for usage
documentation.
"""

import typing as tp
import re
import math
import os

import implements

from core.variables import batch_criteria as bc
import core.utils


@implements.implements(bc.IConcreteBatchCriteria)
class BlockQuantity(bc.UnivarBatchCriteria):
    """
    A univariate range of block counts used to define batched
    experiments. This class is a base class which should (almost) never be used on its own. Instead,
    the ``factory()`` function should be used to dynamically create derived classes expressing the
    user's desired size distribution.

    Attributes:
        quantities: List of integer block quantities defining the range of the variable for the
                    batched experiment.

    """

    def __init__(self,
                 cli_arg: str,
                 main_config: tp.Dict[str, str],
                 batch_input_root: str,
                 quantities: tp.List[int],
                 block_type: str) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)
        self.quantities = quantities
        self.block_type = block_type
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes for block quantities to define a batch experiment.
        """
        if not self.attr_changes:
            self.attr_changes = self.gen_attr_changelist_from_list(self.quantities, self.block_type)

        return self.attr_changes

    def gen_exp_dirnames(self, cmdopts: dict) -> list:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: dict,
                     exp_dirs: tp.List[str] = None) -> tp.List[float]:

        if exp_dirs is None:
            exp_dirs = self.gen_exp_dirnames(cmdopts)

        quantities = []

        for d in exp_dirs:
            pickle_fpath = os.path.join(self.batch_input_root,
                                        d,
                                        "exp_def.pkl")
            exp_def = core.utils.unpickle_exp_def(pickle_fpath)
            for path, attr, value in exp_def:
                if path == ".//arena_map/blocks/distribution/manifest" and attr == "n_" + self.block_type:
                    quantities.append(float(value))
        return quantities

    def graph_xticklabels(self,
                          cmdopts: dict,
                          exp_dirs: tp.List[str] = None) -> tp.List[str]:

        return list(map(str, self.graph_xticks(cmdopts, exp_dirs)))

    def graph_xlabel(self, cmdopts: dict) -> str:
        return "Block Quantity"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw', 'scalability', 'self-org']

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        return False

    @staticmethod
    def gen_attr_changelist_from_list(quantities: list, block_type: str) -> tp.List:
        return [set([(".//arena_map/blocks/distribution/manifest",
                      "n_" + block_type,
                      str(c))]) for c in quantities]


class BlockQuantityParser():
    """
    Enforces the cmdline definition of the :class:`BlockQuantity` batch criteria defined in
    :ref:`ln-bc-block-quantity`.
    """

    def __call__(self, criteria_str: str) -> dict:
        ret = {
            'block_type': str(),
            'max_quantity': int(),
            'increment_type': str(),
            'linear_increment': None
        }

        # Parse block type
        res = re.search("cube|ramp", criteria_str.split('.')[1])
        assert res is not None, \
            "FATAL: Bad block type specification in criteria '{0}'".format(criteria_str)
        ret['block_type'] = res.group(0)

        # Parse increment type
        res = re.search("Log|Linear", criteria_str.split('.')[2])
        assert res is not None, \
            "FATAL: Bad quantity increment specification in criteria '{0}'".format(criteria_str)
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", criteria_str.split('.')[2])
        assert res is not None, \
            "FATAL: Bad max quantity in criteria '{0}'".format(criteria_str)
        ret['max_quantity'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(ret['max_quantity'] / 10.0)  # type: ignore

        return ret


def factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            batch_input_root: str,
            **kwargs) -> BlockQuantity:
    """
    Factory to create :class:`BlockQuantity` derived classes from the command line definition.

    """
    attr = BlockQuantityParser()(cli_arg)

    def gen_quantities():
        if attr["increment_type"] == 'Linear':
            return [attr["linear_increment"] * x for x in range(1, 11)]
        elif attr["increment_type"] == 'Log':
            return [2 ** x for x in range(0, int(math.log2(attr["max_quantity"])) + 1)]
        else:
            return None

    def __init__(self) -> None:
        BlockQuantity.__init__(self,
                               cli_arg,
                               main_config,
                               batch_input_root,
                               gen_quantities(),
                               attr['block_type'])

    return type(cli_arg,  # type: ignore
                (BlockQuantity,),
                {"__init__": __init__})


__api__ = [
    'BlockQuantity'
]
