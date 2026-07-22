# Copyright 2024 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Plugin for parsing and manipulating template input files in JSON format."""

# Core packages
import pathlib
import logging
import typing as tp
import json

# 3rd party packages
from jsonpath_ng.ext import parse as jpparse

# Project packages
from sierra.core.experiment import definition
from sierra.core import types, utils


class Writer:
    """Write the JSON experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, tree: types.JSON) -> None:
        self.tree = tree
        self.logger = logging.getLogger(__name__)

    def __call__(
        self, write_config: definition.WriterConfig, base_opath: pathlib.Path
    ) -> None:
        for config in write_config.values:
            self._write_with_config(base_opath, config)

    def _write_with_config(self, base_opath: pathlib.Path, config: dict) -> None:
        tree, src_root, opath = self._write_prepare_tree(base_opath, config)

        self.logger.trace("Write tree@%s to %s", src_root, opath)

        to_write = tree

        with utils.utf8open(opath, "w") as f:
            json.dump(to_write, f, indent=2)

    def _write_prepare_tree(
        self, base_opath: pathlib.Path, config: dict
    ) -> tuple[tp.Optional[types.JSON], str, pathlib.Path]:
        if config["src_parent"] is None:
            src_root = config["src_tag"]
        else:
            src_root = "{}.{}".format(config["src_parent"], config["src_tag"])

        expr = jpparse(src_root)
        matches = expr.find(self.tree)
        assert len(matches) == 1, "src_root was not unique!"
        tree_out = matches[0].value

        # Customizing the output write path is not required
        if "opath_leaf" in config and config["opath_leaf"] is not None:
            opath = base_opath.with_name(base_opath.name + config["opath_leaf"])
        else:
            opath = base_opath

        return (tree_out, src_root, opath)


def root_querypath() -> str:
    return "$"


class ExpDef(definition.BaseExpDef):
    """Read, write, and modify parsed JSON files into experiment definitions."""

    def __init__(
        self,
        input_fpath: pathlib.Path,
        write_config: tp.Optional[definition.WriterConfig] = None,
    ) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        with utils.utf8open(self.input_fpath, "r") as f:
            self.tree = json.load(f)
        self.element_adds = definition.ElementAddList()
        self.attr_chgs = definition.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

    def n_mods(self) -> tuple[int, int]:
        return len(self.element_adds), len(self.attr_chgs)

    def write_config_set(self, config: definition.WriterConfig) -> None:
        """Set the write config for the object.

        Provided for cases in which the configuration is dependent on whether or
        not certain tags are present in the input file.

        """
        self.write_config = config

    def write(self, base_opath: pathlib.Path) -> None:
        assert self.write_config is not None, "Can't write without write config"

        writer = Writer(self.tree)
        writer(self.write_config, base_opath)

    def flatten(self, keys: list[str]) -> None:
        """
        Flatten a nested JSON structure.

        Recursively searches for each of the supplies keys, and replaces the
        values of all matching keys with the corresponding config files. The
        paths to the nested config files are assumed to be specified relative to
        the root/main config file, and to reside in subdirs/adjacent dirs to it.
        """
        for k in keys:
            self.logger.debug("Flattening with key=%s", k)
            self._flatten_recurse(self.tree, self.input_fpath, k)

    def _flatten_recurse(
        self, blob: types.JSON, prefix: pathlib.Path, path_key: str
    ) -> None:
        """
        Recursive flattening implementation.

        The use of recursion enables searching for simple key matches instead of
        having to deal with complicated jsonpath expressions, which is a huge
        win. Plus, it's generally faster than an iterating implementation when
        it comes to large files.

        Arguments:
            blob: The tree of JSON containing filepath references to flatten.

            prefix: The prefix which should be prepended to all values which
                    match ``prefix``. This allows nested JSON structures where
                    filepaths are specified relative to the root-level
                    configuration (really it's parent directory), which is very
                    convenient. Note that all paths must be relative to
                    root-level configuration--relativity to a sub-path will NOT
                    work.

            path_key: The key to recursively search for. Not a substring--will
                      be checked for exact match.
        """

        def _flatten_update_path(parent, key: str, value) -> None:
            # Base case
            if path_key != key:
                return

            # Make relative to input prefix. This SHOULD work recursively for
            # nested dirs, though I'm not 100% sure.
            path = pathlib.Path(value)

            if not path.is_absolute():
                path = prefix.parent / path
                value = str(path.resolve())

            # If the file doesn't exist, that's an error, so don't catch the
            # exception if that happens.
            with utils.utf8open(path, "r") as f:
                subblob = json.load(f)

                self._flatten_recurse(subblob, path, path_key)

                if isinstance(parent, dict):
                    parent.update(subblob)

                    # This ensures that the original <key,value> pair is removed
                    # from the parent.
                    parent.pop(path_key)

        def _flatten_erase_key(_, __, value):
            if isinstance(value, dict):
                keys_to_erase = [key for key in value if path_key == key]
                for key in reversed(keys_to_erase):
                    value.pop(key, None)

        self._flatten_apply1(blob, _flatten_update_path)
        self._flatten_apply2(blob, _flatten_erase_key)

    def _flatten_apply1(self, blob: types.JSON, f: tp.Callable) -> None:
        """Apply the given callable to every unstructured key-value pair.

        "Unstructured" here means pairs where the value is a literal instead of
        a list or dict.
        """
        if isinstance(blob, dict):
            c = blob.copy()
            for key, val in c.items():
                if isinstance(val, (dict, list)):
                    # recurse on each value in dict. Key is ignored.
                    self._flatten_apply1(val, f)
                else:
                    # Base case: literal
                    f(blob, key, val)

        elif isinstance(blob, list):
            for item in blob:
                # Recurse on each item in list
                self._flatten_apply1(item, f)

    def _flatten_apply2(self, blob: types.JSON, f: tp.Callable) -> None:
        """Apply the given callable to every structured key-value pair.

        "Structured" here means pairs where the value is a list or dict instead
        of a literal.

        This function does not have a base case per-se, because we iterate
        through each item in the dict/list passed in and call this function on
        each one; recursion will terminate after we have exhaustively applied
        the callback to all sub-blobs.
        """
        if isinstance(blob, dict):
            for key, val in blob.items():
                if isinstance(val, (dict, list)):
                    self._flatten_apply2(val, f)

                    f(blob, key, val)
        elif isinstance(blob, list):
            for item in blob:
                self._flatten_apply2(item, f)

    @staticmethod
    def _is_attr_value(value: tp.Any) -> bool:
        """Determine if a value qualifies as an attribute value.

        A value is an *attribute* if it is a scalar (str, int, float, bool,
        None), or a *non-empty flat* list whose members are all scalars (e.g.
        ``[80, 443]``).  A dict, or a list containing any dict/list member
        (e.g. a list of sub-elements), is *not* an attribute -- it is an
        element.

        An empty list or dict is treated as an *element* (an unpopulated
        container), not an attribute, matching the behavior of
        :meth:`has_element` for empty sections.

        The list rule is deliberately non-recursive: a nested list such as
        ``[[1, 2], [3, 4]]`` is treated as an element, not an attribute.

        This mirrors the identically-named helper in the YAML plugin so the two
        formats classify attribute/element values consistently.
        """
        if isinstance(value, dict):
            return False
        if isinstance(value, list):
            if len(value) == 0:
                return False
            return all(not isinstance(m, (list, dict)) for m in value)
        return True

    @classmethod
    def _is_element_value(cls, value: tp.Any) -> bool:
        """Inverse of :meth:`_is_attr_value`; a value is an element or not."""
        return not cls._is_attr_value(value)

    def attr_get(
        self, path: str, attr: str
    ) -> tp.Optional[tp.Union[str, int, float, list]]:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, f"Path '{path}' to element was not unique!"

        if len(matches) == 0:
            return None

        match = matches[0].value

        if not isinstance(match, list):
            match = [match]

        for m in match:
            if attr in m and self._is_attr_value(m[attr]):
                return m[attr]

        return None

    def attr_change(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float, list],
        noprint: bool = False,
    ) -> bool:

        expr = jpparse(path)
        matches = expr.find(self.tree)

        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        # Validate every match BEFORE mutating any, so a failure partway through
        # cannot leave the tree modified while the change goes unrecorded (which
        # would desync the tree from self.attr_chgs). This preserves the
        # all-or-nothing contract of this method.
        for m in matches:
            match = m.value
            if attr not in match:
                if not noprint:
                    self.logger.warning(
                        "Attribute '%s' not found in path '%s'", attr, m.full_path
                    )
                return False

            # The existing value must itself be an attribute. Refuse to clobber
            # an element (dict, or list-of-elements) with an attribute value;
            # SIERRA keeps the attribute/element distinction even though JSON
            # does not.
            if not self._is_attr_value(match[attr]):
                if not noprint:
                    self.logger.warning(
                        "'%s' in '%s' maps to an element, not an attribute",
                        attr,
                        m.full_path,
                    )
                return False

        for m in matches:
            m.value[attr] = value
            self.logger.trace("Modify attr: '%s/%s' = '%s'", m.full_path, attr, value)

        self.attr_chgs.add(definition.AttrChange(path, attr, tp.cast("tp.Union[str, int, float]", value)))
        return True

    def attr_add(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float, list],
        noprint: bool = False,
    ) -> bool:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, f"Path '{path}' to element was not unique!"

        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return False

        for m in matches:
            match = m.value
            if attr in match:
                if not noprint:
                    self.logger.warning(
                        "Attribute '%s' already in path '%s'", attr, m.full_path
                    )
                return False

            match[attr] = value
            self.logger.trace(
                "Add new attribute: '%s/%s' = '%s'", m.full_path, attr, value
            )
        self.attr_chgs.add(definition.AttrChange(path, attr, tp.cast("tp.Union[str, int, float]", value)))
        return True

    def has_element(self, path: str) -> bool:
        expr = jpparse(path)
        el = expr.find(self.tree)

        assert len(el) <= 1, (
            f"Path '{path}' to element was not unique! Perhaps "
            "you have malform JSON?"
        )

        if el:
            # If path maps to an attribute value (a scalar, or a flat list of
            # scalars), then we are pointing to an attribute, not an element.
            # Elements are dicts, lists-of-elements, and empty containers.
            return self._is_element_value(el[0].value)

        return False

    def has_attr(self, path: str, attr: str) -> bool:
        expr = jpparse(path)
        matches = expr.find(self.tree)

        assert len(matches) <= 1, f"Path '{path}' to parent element was not unique!"

        if len(matches) == 0:
            return False

        found = False

        match = matches[0].value
        if not isinstance(match, list):
            match = [match]

        for m in match:
            if not isinstance(m, dict):
                continue

            for k in m:
                # While python/JSON doesn't distinguish between a key which maps
                # to a literal {bool, int, ...}, and one which maps to a
                # sub-element, SIERRA does, because it treats one key as
                # referring to an attribute mapping, and one referring to a
                # sub-element.
                if k == attr and self._is_attr_value(m[k]):
                    assert (
                        not found
                    ), f"Specified attr '{attr}' is not unique in '{path}'"
                    found = True

        return found

    def element_change(self, path: str, tag: str, value: str) -> bool:
        raise NotImplementedError

    def element_remove(self, path: str, tag: str, noprint: bool = False) -> bool:
        expr = jpparse(path)
        parents = expr.find(self.tree)

        assert len(parents) <= 1, (
            f"Path '{path}' to parent was not unique! If you want to remove "
            "multiple matching elements, use elements_remove_all()"
        )

        if len(parents) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = parents[0].value
        victims = jpparse(tag).find(parent)

        # A scalar-valued key is an attribute, not an element, and is not
        # removable via element_remove (use attr-oriented methods instead).
        if len(victims) == 0 or not self._is_element_value(victims[0].value):
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'", tag, path)
            return False

        del parent[tag]
        return True

    def element_remove_all(self, path: str, tag: str, noprint: bool = False) -> bool:
        # JSON objects have unique keys, so a tag can match at most one child of
        # a given parent -- "remove all matching" collapses to a single removal.
        # (The multi-match case only exists in XML, where a parent may have
        # several children with the same tag.) Delegate to element_remove.
        return self.element_remove(path, tag, noprint=noprint)

    def element_add(
        self,
        path: str,
        tag: str,
        attr: tp.Optional[types.StrDict] = None,
        allow_dup: bool = True,
        noprint: bool = False,
    ) -> bool:
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
                    self.logger.warning(
                        "Child element '%s' already in parent '%s'", tag, path
                    )
                return False

            # Child doesn't exist--just assign to single sub-element.
            parent[tag] = attr
            self.logger.trace(
                "Add new unique element: '%s.%s' = '%s'",
                path,
                tag,
                str(attr),
            )
        else:
            child = jpparse(tag).find(parent)

            # Child element exists, so update it to be a list of sub-elements
            # rather than a single sub-element. If it is already a list, append
            # to it (do not nest); otherwise wrap the existing value and the new
            # one into a fresh list.
            if len(child):
                existing = parent[tag]
                if isinstance(existing, list):
                    existing.append(attr)
                else:
                    parent[tag] = [existing, attr]
            else:
                # Child doesn't exist--just assign to single sub-element.
                parent[tag] = attr

        self.element_adds.append(definition.ElementAdd(path, tag, attr if attr else {}, allow_dup))
        return True


def unpickle(fpath: pathlib.Path) -> definition.ExpDefPickle:
    """Unpickle all JSON modifications from the pickle file at the path.

    Returns every modification kind (attribute changes, element additions,
    and element removals) present in the pickle, so engines that set up
    experiments with any combination of them round-trip completely.
    """
    return definition.unpickle(fpath)


__all__ = ["ExpDef", "unpickle"]
