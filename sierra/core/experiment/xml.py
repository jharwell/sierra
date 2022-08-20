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

"""Helper classes for XML experiment definitions.

Adding/removing tags, modifying attributes, configuration for how to write XML
files.

"""

# Core packages
import typing as tp
import logging
import pickle
import xml.etree.ElementTree as ET
import sys
import pathlib

# 3rd party packages

# Project packages
from sierra.core import types


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
        Init the object.

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
    @staticmethod
    def as_root(tag: str,
                attr: types.StrDict) -> 'TagAdd':
        return TagAdd('', tag, attr, False)

    def __init__(self,
                 path: str,
                 tag: str,
                 attr: types.StrDict,
                 allow_dup: bool):
        """
        Init the object.

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
        return self.path + '/' + self.tag + ': ' + str(self.attr)


class AttrChangeSet():
    """
    Data structure for :class:`AttrChange` objects.

    The order in which attributes are changed doesn't matter from the standpoint
    of correctness (i.e., different orders won't cause crashes).

    """
    @staticmethod
    def unpickle(fpath: pathlib.Path) -> 'AttrChangeSet':
        """Unpickle XML changes.

        You don't know how many there are, so go until you get an exception.

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

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            fpath.unlink()

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

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            fpath.unlink()

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
    def unpickle(fpath: pathlib.Path) -> tp.Optional['TagAddList']:
        """Unpickle XML modifications.

        You don't know how many there are, so go until you get an exception.

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

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils

        if delete and utils.path_exists(fpath):
            fpath.unlink()

        with open(fpath, 'ab') as f:
            utils.pickle_dump(self.adds, f)


class WriterConfig():
    """Config for writing :class:`~sierra.core.experiment.definition.XMLExpDef`.

    Different parts of the XML tree can be written to multiple XML files.

    Attributes:

        values: Dict with the following possible key, value pairs:

                ``src_parent`` - The parent of the root of the XML tree
                                 specifying a sub-tree to write out as a child
                                 of ``dest_root``. This key is required.

                ``src_tag`` - The name of the tag within ``src_parent`` to write
                              out. This key is required.

                ``dest_parent`` - The new name of ``src_root`` when writing out
                                  the partial XML tree to a new file. This key
                                  is optional.

                ``create_tags`` - Additional tags to create under
                                  ``dest_parent``. Must form a tree with a
                                  single root.

                ``opath_leaf`` - Additional bits added to whatever the opath
                                 file stem that is set for the
                                 :class:`~sierra.core.experiment.definition.XMLExpDef`
                                 instance. This key is optional. Can be used to
                                 add an extension.

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


class Writer():
    """Write the XML experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, tree: ET.ElementTree) -> None:
        self.tree = tree
        self.root = tree.getroot()
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 write_config: WriterConfig,
                 base_opath: pathlib.Path) -> None:
        for config in write_config.values:
            self._write_with_config(base_opath, config)

    def _write_with_config(self,
                           base_opath: pathlib.Path,
                           config: dict) -> None:
        tree, src_root, opath = self._write_prepare_tree(base_opath, config)

        if tree is None:
            self.logger.warning("Cannot write non-existent tree@%s to %s",
                                src_root,
                                opath)
            return

        self.logger.trace("Write tree@%s to %s",  # type: ignore
                          src_root,
                          opath)

        # Renaming tree root is not required
        if 'rename_to' in config and config['rename_to'] is not None:
            tree.tag = config['rename_to']
            self.logger.trace("Rename tree root -> %s",  # type: ignore
                              config['rename_to'])

        # Adding tags not required
        if 'dest_parent' in config and config['dest_parent'] is not None:
            # Create a new tree to add the specified tags in. After adding the
            # tags, append the tree of newly created tags back into the parent.

            to_write = ET.ElementTree()
            if 'create_tags' in config and config['create_tags'] is not None:
                self._write_add_tags(config, to_write)

            parent = to_write.getroot().find(config['dest_parent'])
            assert parent is not None,\
                "Could not find parent '{0}' of tags for appending".format(
                    config['dest_parent'])
            parent.append(tree)
        else:
            to_write = ET.ElementTree(tree)
            parent = to_write.getroot()

        # Grafts are not required
        if 'child_grafts' in config and config['child_grafts'] is not None:
            self._write_add_grafts(config, to_write)

        # Write out pretty XML to make it easier to read to see if things
        # have been generated correctly.
        if sys.version_info < (3, 9):
            from xml.dom import minidom
            with open(opath, "w", encoding='utf-8') as f:
                raw = ET.tostring(to_write.getroot())
                pretty = minidom.parseString(raw).toprettyxml(indent="  ")
                f.write(pretty)
        else:
            ET.indent(to_write, space="\t", level=0)
            to_write.write(opath, encoding='utf-8')

    def _write_add_grafts(self,
                          config: dict,
                          to_write: ET.ElementTree) -> None:
        dest_root = "{0}/{1}".format(config['dest_parent'],
                                     config['src_tag'])
        graft_parent = to_write.getroot().find(dest_root)
        assert graft_parent is not None, \
            "Bad parent {dest_root} for grafting"

        for g in config['child_grafts']:
            self.logger.trace("Graft tree@%s as child under %s",  # type: ignore
                              g,
                              dest_root)
            elt = self.root.find(g)
            graft_parent.append(elt)

    def _write_add_tags(self,
                        config: dict,
                        to_write: ET.ElementTree) -> None:
        for spec in config['create_tags']:
            # Tree has no root set--set root to specified tag
            if to_write.getroot() is None:
                to_write._setroot(ET.Element(spec.tag, spec.attr))
            else:
                elt = to_write.find(spec.path)
                assert elt is not None,\
                    (f"Could not find parent '{spec.path}' of tag '{spec.tag}' "
                     "to add")

                ET.SubElement(elt, spec.tag, spec.attr)

            self.logger.trace("Create tag@%s as child under %s",  # type: ignore
                              spec.tag,
                              spec.path)

    def _write_prepare_tree(self,
                            base_opath: pathlib.Path,
                            config: dict) -> tp.Tuple[tp.Optional[ET.Element],
                                                      str,
                                                      pathlib.Path]:
        if config['src_parent'] is None:
            src_root = config['src_tag']
        else:
            src_root = "{0}/{1}".format(config['src_parent'],
                                        config['src_tag'])

        tree_out = self.tree.getroot().find(src_root)

        # Customizing the output write path is not required
        if 'opath_leaf' in config and config['opath_leaf'] is not None:
            opath = base_opath.with_name(base_opath.name + config['opath_leaf'])
        else:
            opath = base_opath

        return (tree_out, src_root, opath)


__api__ = [
    'AttrChange',
    'AttrChangeSet',
    'TagAdd',
    'TagAddList',
    'TagRm',
    'TagRmList',
    'WriterConfig'
]
