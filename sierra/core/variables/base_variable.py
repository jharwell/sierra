# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.experiment import xml


class IBaseVariable(implements.Interface):
    """Interface that all variables must implement.

    """

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """Generate XML attributes to change in a batch experiment definition.

        Modifications are sets, one per experiment in the batch, because the
        order you apply them doesn't matter.

        """
        raise NotImplementedError

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        """Generate XML tags to remove from the batch experiment definition.

        Modifications are lists, one per experiment in the batch, because the
        order you apply them matters.
        """

        raise NotImplementedError

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        """Generate XML tags to add to the batch experiment definition.

        Modifications are lists, one per experiment in the batch, because the
        order you apply them matters.
        """
        raise NotImplementedError

    def gen_files(self) -> None:
        """Generate one or more new files to add to the batch experiment definition.

        Presumably, the created files will be referenced in the template input
        file by path.

        """


__api__ = [
    'IBaseVariable'
]
