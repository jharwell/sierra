# Copyright 2022 John Harwell, All rights reserved.
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

"""
Classes for XML experiment definitions: adding/removing tags, modifying
attributes, configuration for how to write XML files.
"""

# Core packages
import typing as tp
import os
import logging
import pickle

# 3rd party packages

# Project packages


class AttrChange():
    """
    Specification for a change to an existing XML attribute.
    """

    def __init__(self,
                 path: str,
                 attr: str,
                 value: tp.Union[str, int, float]) -> None:
        self.path = path
        self.attr = attr
        self.value = str(value)

    def __iter__(self):
        yield from [self.path, self.attr, self.value]

    def __repr__(self) -> str:
        return self.path + '/' + self.attr + ': ' + str(self.value)


class TagRm():
    """
    Specification for removal of an existing XML tag.
    """

    def __init__(self, path: str, tag: str):
        """
        Arguments:
            path: The path to the **parent** of the tag you want to remove, in
                  XPath syntax.

            tag: The name of the tag to remove.
        """
        self.path = path
        self.tag = tag

    def __iter__(self):
        yield from [self.path, self.tag]

    def __repr__(self) -> str:
        return self.path + '/' + self.tag


class TagAdd():
    """
    Specification for adding a new XML tag.

    The tag may be added idempotently, or duplicates can be allowed.
    """

    def __init__(self,
                 path: tp.Optional[str],
                 tag: str,
                 attr: dict,
                 allow_dup: bool):
        """
        Arguments:
            path: The path to the **parent** tag you want to add a new tag
                  under, in XPath syntax. If None, then the tag will be added as
                  the root XML tag.

            tag: The name of the tag to add.

            attr: A dictionary of (attribute, value) pairs to also create as
                  children of the new tag when creating the new tag.
        """

        self.path = path
        self.tag = tag
        self.attr = attr
        self.allow_dup = allow_dup

    def __iter__(self):
        yield from [self.path, self.tag, self.attr]

    def __repr__(self) -> str:
        if self.path is not None:
            return self.path + '/' + self.tag + ': ' + str(self.attr)
        else:
            return '/' + self.tag + ': ' + str(self.attr)


class AttrChangeSet():
    """
    Data structure for :class:`AttrChange` objects.

    The order in which attributes are changed doesn't matter from the standpoint
    of correctness (i.e., different orders won't cause crashes).

    """
    @staticmethod
    def unpickle(fpath: str) -> 'AttrChangeSet':
        """
        Read in all the different sets of parameter changes that were pickled to
        make crucial parts of the experiment definition easily accessible. You
        don't know how many there are, so go until you get an exception.

        """
        exp_def = AttrChangeSet()

        try:
            with open(fpath, 'rb') as f:
                while True:
                    exp_def |= AttrChangeSet(*pickle.load(f))
        except EOFError:
            pass
        return exp_def

    def __init__(self, *args: AttrChange) -> None:
        self.changes = set(args)
        self.logger = logging.getLogger(__name__)

    def __len__(self) -> int:
        return len(self.changes)

    def __iter__(self) -> tp.Iterator[AttrChange]:
        return iter(self.changes)

    def __ior__(self, other: 'AttrChangeSet') -> 'AttrChangeSet':
        self.changes |= other.changes
        return self

    def __or__(self, other: 'AttrChangeSet') -> 'AttrChangeSet':
        new = AttrChangeSet(*self.changes)
        new |= other
        return new

    def __repr__(self) -> str:
        return str(self.changes)

    def add(self, chg: AttrChange) -> None:
        self.changes.add(chg)

    def pickle(self, fpath: str, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            os.remove(fpath)

        with open(fpath, 'ab') as f:
            utils.pickle_dump(self.changes, f)


class TagRmList():
    """
    Data structure for :class:`TagRm` objects.

    The order in which tags are removed matters (i.e., if you remove dependent
    tags in the wrong order you will get an exception), hence the list
    representation.

    """

    def __init__(self, *args: TagRm) -> None:
        self.rms = list(args)

    def __len__(self) -> int:
        return len(self.rms)

    def __iter__(self) -> tp.Iterator[TagRm]:
        return iter(self.rms)

    def __repr__(self) -> str:
        return str(self.rms)

    def extend(self, other: 'TagRmList') -> None:
        self.rms.extend(other.rms)

    def append(self, other: TagRm) -> None:
        self.rms.append(other)

    def pickle(self, fpath: str, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            os.remove(fpath)

        with open(fpath, 'ab') as f:
            utils.pickle_dump(self.rms, f)


class TagAddList():
    """
    Data structure for :class:`TagAdd` objects.

    The order in which tags are added matters (i.e., if you add dependent tags
    in the wrong order you will get an exception), hence the list
    representation.
    """

    @staticmethod
    def unpickle(fpath: str) -> tp.Optional['TagAddList']:
        """
        Read in all the different sets of parameter changes that were pickled to
        make crucial parts of the experiment definition easily accessible. You
        don't know how many there are, so go until you get an exception.

        """
        exp_def = TagAddList()

        try:
            with open(fpath, 'rb') as f:
                while True:
                    exp_def.append(*pickle.load(f))
        except EOFError:
            pass
        return exp_def

    def __init__(self, *args: TagAdd) -> None:
        self.adds = list(args)

    def __len__(self) -> int:
        return len(self.adds)

    def __iter__(self) -> tp.Iterator[TagAdd]:
        return iter(self.adds)

    def __repr__(self) -> str:
        return str(self.adds)

    def extend(self, other: 'TagAddList') -> None:
        self.adds.extend(other.adds)

    def append(self, other: TagAdd) -> None:
        self.adds.append(other)

    def prepend(self, other: TagAdd) -> None:
        self.adds.insert(0, other)

    def pickle(self, fpath: str, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            os.remove(fpath)

        with open(fpath, 'ab') as f:
            utils.pickle_dump(self.adds, f)


class WriterConfig():
    """Config for writing the XML content managed by
    :class:`~sierra.core.experiment.definition.XMLExpDef`.

    Different parts of the XML tree can be written to multiple XML files.

    Attributes:

        values: Dict with the following possible key, value pairs:

                ``src_parent`` - The parent of the root of the XML tree
                                 specifying a sub-tree to write out as a child
                                 of ``dest_root``. This key is required.

                ``src_tag`` - The name of the tag within ``src_parent`` to write
                              out.This key is required.

                ``dest_root`` - The new name of ``src_root`` when writing out
                                the partial XML tree to a new file. This key is
                                optional.

                ``opath_leaf`` - Additional bits added to whatever the opath
                                 file stem that is set for the
                                 :class:`~sierra.core.experiment.definition.XMLExpDef`
                                 instance. This key is optional.

                ``child_grafts`` - Additional bits of the XML tree to add under
                                   the new ``dest_root/src_tag``, specified as a
                                   list of XPath strings. You can't just have
                                   multiple src_roots because that makes
                                   unambiguous renaming of ``src_root`` ->
                                   ``dest_root`` impossible. This key is
                                   optional.

    """

    def __init__(self, values: tp.List[dict]) -> None:
        self.values = values

    def add(self, value: dict) -> None:
        self.values.append(value)


__api__ = [
    'AttrChange',
    'AttrChangeSet',
    'TagAdd',
    'TagAddList',
    'TagRm',
    'TagRmList',
    'WriterConfig'
]
