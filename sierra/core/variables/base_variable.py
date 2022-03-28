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
from sierra.core.xml import XMLAttrChangeSet, XMLTagRmList, XMLTagAddList


class IBaseVariable(implements.Interface):
    """Interface that all variables must implement.

    """

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """Generate a list of sets of XML attributes to change in the template input XML
file."""
        raise NotImplementedError

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        """Generate a list of lists of XML tags to remove from the template input XML
file."""
        raise NotImplementedError

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        """Generate a list of lists of XML tags (and possibly child attributes) to add
        to the template input XML file.

        """
        raise NotImplementedError

    def gen_files(self) -> None:
        """Generate one or more new files which will (presumably) be referenced in the
        template input file by path.

        """


__api__ = [
    'IBaseVariable'
]
