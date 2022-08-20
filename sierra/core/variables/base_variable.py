# Copyright 2018 John Harwell, All rights reserved.
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
