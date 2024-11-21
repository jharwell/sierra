# Copyright 2024 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Plugin for parsing and manipulating template input files in XML format.

"""

# Core packages
import pathlib
import logging
import typing as tp
import json

# 3rd party packages
import implements
from jsonpath_ng.ext import parse as jpparse

# Project packages
from sierra.core.experiment import definition
from sierra.core import types


class Writer():
    """Write the XML experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, tree: types.JSON) -> None:
        self.tree = tree
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 write_config: definition.WriterConfig,
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

        to_write = tree

        json.dump(to_write, open(opath, 'w', encoding='utf-8'))

    def _write_prepare_tree(self,
                            base_opath: pathlib.Path,
                            config: dict) -> tp.Tuple[tp.Optional[types.JSON],
                                                      str,
                                                      pathlib.Path]:
        if config['src_parent'] is None:
            src_root = config['src_tag']
        else:
            src_root = "{0}/{1}".format(config['src_parent'],
                                        config['src_tag'])

        expr = jpparse(src_root)
        matches = expr.find(self.tree)
        assert len(matches) == 1, "src_root was not unique!"
        tree_out = matches[0].value

        # Customizing the output write path is not required
        if 'opath_leaf' in config and config['opath_leaf'] is not None:
            opath = base_opath.with_name(base_opath.name + config['opath_leaf'])
        else:
            opath = base_opath

        return (tree_out, src_root, opath)


@implements.implements(definition.BaseExpDef)
class ExpDef:
    """Read, write, and modify parsed XML files into experiment definitions.
    """

    def __init__(self,
                 input_fpath: pathlib.Path,
                 write_config: tp.Optional[definition.WriterConfig] = None) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        self.tree = json.load(open(self.input_fpath, 'r', encoding='utf-8'))
        self.element_adds = definition.ElementAddList()
        self.attr_chgs = definition.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

    def write_config_set(self, config: definition.WriterConfig) -> None:
        """Set the write config for the object.

        Provided for cases in which the configuration is dependent on whether or
        not certain tags are present in the input file.

        """
        self.write_config = config

    def write(self, base_opath: pathlib.Path) -> None:
        assert self.write_config is not None, \
            "Can't write without write config"

        writer = Writer(self.tree)
        writer(self.write_config, base_opath)

    def attr_get(self, path: str, attr: str) -> tp.Union[str, None]:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, f"Path '{path}' to element was not unique!"

        if len(matches) == 0:
            return None

        match = matches[0].value

        if not isinstance(match, list):
            match = [match]

        for m in match:
            if attr in m.keys() and not isinstance(m[attr], (list, dict)):
                return m[attr]

        return None

    def attr_change(self,
                    path: str,
                    attr: str,
                    value: str,
                    noprint: bool = False) -> bool:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        match = matches[0].value
        if attr not in match.keys() or isinstance(match[attr], (list, dict)):
            if not noprint:
                self.logger.warning("Attribute '%s' not found in path '%s'",
                                    attr,
                                    path)
            return False

        match[attr] = value
        self.logger.trace("Modify attr: '%s/%s' = '%s'",  # type: ignore
                          path,
                          attr,
                          value)

        self.attr_chgs.add(definition.AttrChange(path, attr, value))
        return True

    def attr_add(self,
                 path: str,
                 attr: str,
                 value: str,
                 noprint: bool = False) -> bool:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, f"Path '{path}' to element was not unique!"

        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return False

        match = matches[0].value
        if attr in match:
            if not noprint:
                self.logger.warning("Attribute '%s' already in path '%s'",
                                    attr,
                                    path)
            return False

        match[attr] = value
        self.logger.trace("Add new attribute: '%s/%s' = '%s'",  # type: ignore
                          path,
                          attr,
                          value)
        self.attr_chgs.add(definition.AttrChange(path, attr, value))
        return True

    def has_element(self, path: str) -> bool:
        expr = jpparse(path)
        el = expr.find(self.tree)

        assert len(el) <= 1, \
            (f"Path '{path}' to element was not unique! Perhaps "
             "you have malform JSON?")

        print(json.dumps(self.tree))

        if el:
            # If path maps to a literal, then we are pointing to an attribute,
            # which is obviously not an element.
            return isinstance(el[0].value, (list, dict))

        return False

    def has_attr(self, path: str, attr: str) -> bool:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, \
            f"Path '{path}' to parent element was not unique!"

        if len(matches) == 0:
            return False

        found = False

        match = matches[0].value
        if not isinstance(match, list):
            match = [match]

        for m in match:
            for k in m:
                # While python/JSON doesn't distinguish between a key which maps
                # to a literal {bool, int, ...}, and one which maps to a
                # sub-element, SIERRA does, because it treats one key as
                # referring to an attribute mapping, and one referring to a
                # sub-element.
                if k == attr and not isinstance(m[k], (list, dict)):
                    assert not found, f"Specified attr '{attr}' is not unique in '{path}'"
                    found = True

        return found

    def element_change(self, path: str, tag: str, value: str) -> bool:
        expr = jpparse(path)
        el = expr.find(self.tree).value

        if el is None:
            self.logger.warning("Parent element '%s' not found", path)
            return False

        for child in el:
            if child.tag == tag:
                child.tag = value
                self.logger.trace("Modify tag: '%s/%s' = '%s'",  # type: ignore
                                  path,
                                  tag,
                                  value)
                return True

        self.logger.warning("No such element '%s' found in '%s'", tag, path)
        return False

    def element_remove(self,
                       path: str,
                       tag: str,
                       noprint: bool = False) -> bool:
        expr = jpparse(path)
        parents = expr.find(self.tree)

        assert len(parents) <= 1, \
            (f"Path '{path}' to parent was not unique! If you want to remove "
             "multiple matching elements, use elements_remove_all()")

        if len(parents) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = parents[0].value
        victims = jpparse(tag).find(parent)

        if len(victims) == 0 or not isinstance(victims[0].value, (list, dict)):
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'",
                                    tag,
                                    path)
            return False

        del parent[tag]
        return True

    def element_remove_all(self,
                           path: str,
                           tag: str,
                           noprint: bool = False) -> bool:

        expr = jpparse(path)
        parents = expr.find(self.tree)

        if len(parents) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = parents[0].value

        victims = jpparse(tag).find(parent)

        if len(victims) == 0:
            if not noprint:
                self.logger.warning("No victims matching '%s' found in parent '%s'",
                                    tag,
                                    path)
            return False

        del parent[tag]
        return True

    def element_add(self,
                    path: str,
                    tag: str,
                    attr: types.StrDict = {},
                    allow_dup: bool = True,
                    noprint: bool = False) -> bool:
        """
        Add tag name as a child element of enclosing parent.
        """
        expr = jpparse(path)
        parents = expr.find(self.tree)

        assert len(parents) <= 1, f"Path '{path}' to parent was not unique!"

        if len(parents) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = parents[0].value

        if not allow_dup:
            child = jpparse(tag).find(parent)
            if len(child):
                if not noprint:
                    self.logger.warning("Child element '%s' already in parent '%s'",
                                        tag,
                                        path)
                return False

            # Child doesn't exist--just assign to single sub-element.
            parent[tag] = attr
            self.logger.trace("Add new unique element: '%s/%s' = '%s'",  # type: ignore
                              path,
                              tag,
                              str(attr))
        else:
            child = jpparse(tag).find(parent)

            # Child element exists, so update it to be a list of sub-elements
            # rather than a single sub-elements.
            if len(child):
                d = [parent[tag], attr]
                jpparse(tag).update(parent, d)
            else:
                # Child doesn't exist--just assign to single sub-element.
                parent[tag] = attr

        self.element_adds.append(definition.ElementAdd(path, tag, attr, allow_dup))
        return True


def unpickle(fpath: pathlib.Path) -> tp.Optional[tp.Union[definition.AttrChangeSet,
                                                          definition.ElementAddList]]:
    """Unickle all XML modifications from the pickle file at the path.

    You don't know how many there are, so go until you get an exception.

    """
    try:
        return definition.AttrChangeSet.unpickle(fpath)
    except EOFError:
        pass

    try:
        return definition.ElementAddList.unpickle(fpath)
    except EOFError:
        pass

    raise NotImplementedError


__api__ = [
    'ExpDef',
    'unpickle'


]
