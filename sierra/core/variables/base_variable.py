# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.experiment import definition


class IBaseVariable(implements.Interface):
    """Interface that all variables must implement."""

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """Generate expdef attributes to change in a batch experiment definition.

        Modifications are sets, one per experiment in the batch, because the
        order you apply them doesn't matter.

        """
        raise NotImplementedError

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        """Generate expdef tags to remove from the batch experiment definition.

        Modifications are lists, one per experiment in the batch, because the
        order you apply them matters.
        """

        raise NotImplementedError

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        """Generate expdef elelemnts to add to the batch experiment definition.

        Modifications are lists, one per experiment in the batch, because the
        order you apply them matters.
        """
        raise NotImplementedError

    def gen_files(self) -> None:
        """Generate files to add to the batch experiment definition.

        Presumably, the created files will be referenced in the
        ``--expdef-template`` file by path.
        """


__all__ = ["IBaseVariable"]
