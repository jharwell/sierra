# Copyright 2024 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Plugin for parsing and manipulating template input files in YAML format."""

# Core packages
import pathlib
import logging
import typing as tp
import argparse

# 3rd party packages
import yamlpath
import ruamel.yaml


# Project packages
from sierra.core.experiment import definition
from sierra.core import types, utils


class Writer:
    """Write the YAML experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, tree: types.YAMLDict) -> None:
        self.tree = tree
        self.logger = logging.getLogger(__name__)

        # Create YAML spec for formatting
        self.yaml_spec = ruamel.yaml.YAML()
        self.yaml_spec.version = (1, 2)
        self.yaml_spec.width = 80
        self.yaml_spec.preserve_quotes = True
        self.yaml_spec.default_flow_style = False
        self.yaml_spec.indent(mapping=2, sequence=4, offset=2)

        # Create processor with proper logger
        args = argparse.Namespace(verbose=False, quiet=True, debug=False)
        log = yamlpath.wrappers.ConsolePrinter(args)
        self.processor = yamlpath.Processor(log, self.tree)

    def __call__(
        self, write_config: definition.WriterConfig, base_opath: pathlib.Path
    ) -> None:
        for config in write_config.values:
            self._write_with_config(base_opath, config)

    def _write_with_config(self, base_opath: pathlib.Path, config: dict) -> None:
        tree, src_root, opath = self._write_prepare_tree(base_opath, config)

        self.logger.trace("Write tree@%s to %s", src_root, opath)

        to_write = tree
        # Use ruamel.yaml for writing to preserve formatting
        with utils.utf8open(opath, "w") as f:
            self.yaml_spec.dump(to_write, f)

    def _write_prepare_tree(
        self, base_opath: pathlib.Path, config: dict
    ) -> tuple[tp.Optional[types.YAMLDict], str, pathlib.Path]:
        if config["src_parent"] is None:
            src_root = config["src_tag"]
        else:
            src_root = "{}/{}".format(config["src_parent"], config["src_tag"])

        spec = yamlpath.YAMLPath(src_root)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) != 1:
            raise ValueError(
                f"src_root '{src_root}' was not unique/does not exist! Found {len(matches)} matches"
            )

        tree_out = matches[0].node

        # Customizing the output write path is not required
        if "opath_leaf" in config and config["opath_leaf"] is not None:
            opath = base_opath.with_name(base_opath.name + config["opath_leaf"])
        else:
            opath = base_opath

        return (tree_out, src_root, opath)


def root_querypath() -> str:
    """Return the root query path."""
    return "/"


class ExpDef(definition.BaseExpDef):
    """Read, write, and modify parsed YAML files into experiment definitions."""

    def __init__(
        self,
        input_fpath: pathlib.Path,
        write_config: tp.Optional[definition.WriterConfig] = None,
    ) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath

        # Load YAML file
        with utils.utf8open(self.input_fpath, "r") as f:
            self.tree = yamlpath.common.Parsers.get_yaml_editor().load(f)

        # Create YAML spec for formatting
        self.yaml_spec = ruamel.yaml.YAML()
        self.yaml_spec.version = (1, 2)
        self.yaml_spec.width = 80
        self.yaml_spec.preserve_quotes = True
        self.yaml_spec.default_flow_style = False

        args = argparse.Namespace(verbose=False, quiet=True, debug=False)
        self.log = yamlpath.wrappers.ConsolePrinter(args)
        self.processor = yamlpath.Processor(self.log, self.tree)

        self.element_adds = definition.ElementAddList()
        self.attr_chgs = definition.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

    def n_mods(self) -> tuple[int, int]:
        """Return the number of modifications (element adds, attribute changes)."""
        return len(self.element_adds), len(self.attr_chgs)

    def write_config_set(self, config: definition.WriterConfig) -> None:
        """Set the write config for the object.

        Provided for cases in which the configuration is dependent on whether or
        not certain tags are present in the input file.
        """
        self.write_config = config

    def write(self, base_opath: pathlib.Path) -> None:
        """Write the modified YAML tree to disk."""
        if self.write_config is None:
            raise ValueError("Can't write without write config")

        writer = Writer(self.tree)
        writer(self.write_config, base_opath)

    def flatten(self, keys: list[str]) -> None:
        """Flatten the YAML structure."""
        raise NotImplementedError

    @staticmethod
    def _is_attr_value(value: tp.Any) -> bool:
        """Determine if a value qualifies as an attribute value.

        A value is an *attribute* if it is a scalar (str, int, float, bool,
        None), or a *non-empty flat* list whose members are all scalars (e.g.
        ``[80, 443]``).  A dict, or a list containing any dict/list member
        (e.g. a list of sub-elements), is *not* an attribute -- it is an
        element.

        An empty list or dict is treated as an *element* (an unpopulated
        container), not an attribute, matching the historical behavior of
        :meth:`has_element` for empty sections.

        The list rule is deliberately non-recursive: a nested list such as
        ``[[1, 2], [3, 4]]`` is treated as an element, not an attribute.
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
        """Get an attribute value at the specified path."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) > 1:
            raise ValueError(f"Path '{path}' to element was not unique!")

        if len(matches) == 0:
            return None

        the_match = matches[0].node

        # Handle list or single dict
        if not isinstance(the_match, list):
            the_match = [the_match]

        for m in the_match:
            if isinstance(m, dict) and attr in m and self._is_attr_value(m[attr]):
                return m[attr]

        return None

    def attr_change(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float, list],
        noprint: bool = False,
    ) -> bool:
        """Change an attribute value at the specified path.

        All matching paths are modified.
        """
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))
        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        mod = False

        for node_coord in matches:
            the_match = node_coord.node  # type: tp.Any
            # A parent that maps to a list (or a scalar) isn't an attribute
            # container; only a dict can hold named attributes.
            if not isinstance(the_match, dict):
                continue

            # If the child doesn't exist in the parent, or if child maps to
            # anything other than a scalar, that isn't an attribute.
            if attr not in the_match:
                self.logger.warning(
                    "'%s' not in '%s' attributes or does not map to a scalar",
                    attr,
                    path,
                )
                continue

            # The existing value must itself be an attribute. Refuse to clobber
            # an element (dict, or list-of-elements) with an attribute value;
            # SIERRA keeps the attribute/element distinction even though YAML
            # does not.
            if not self._is_attr_value(the_match[attr]):
                if not noprint:
                    self.logger.warning(
                        "'%s' in '%s' maps to an element, not an attribute",
                        attr,
                        path,
                    )
                continue

            the_match[attr] = value
            full_path = f"{path}/{attr}" if path else attr
            mod = True
            self.logger.trace("Modify attr: '%s' = '%s'", full_path, value)

        if mod:
            self.attr_chgs.add(
                definition.AttrChange(
                    path, attr, tp.cast("tp.Union[str, int, float]", value)
                )
            )
        else:
            self.logger.warning("Attribute '%s' not found in parent '%s'", attr, path)

        return mod

    def attr_add(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float, list],
        noprint: bool = False,
    ) -> bool:
        """Add a new attribute at the specified path. At most 1 attribute is added."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        # Path to parent must be unique.
        if len(matches) > 1:
            raise ValueError(f"Path '{path}' to element was not unique!")

        if len(matches) == 0:
            if not noprint:
                self.logger.warning("Node '%s' not found", path)
            return False

        for node_coord in matches:
            the_match = node_coord.node

            if not isinstance(the_match, dict):
                if not noprint:
                    self.logger.warning("Path '%s' does not point to a dict", path)
                return False

            if attr in the_match:
                if not noprint:
                    full_path = f"{path}.{attr}" if path else attr
                    self.logger.warning(
                        "Attribute '%s' already in path '%s'", attr, full_path
                    )
                return False

            the_match[attr] = value
            full_path = f"{path}.{attr}" if path else attr
            self.logger.trace("Add new attribute: '%s' = '%s'", full_path, value)

        self.attr_chgs.add(
            definition.AttrChange(
                path, attr, tp.cast("tp.Union[str, int, float]", value)
            )
        )
        return True

    def has_element(self, path: str) -> bool:
        """Check if an element exists at the specified path."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) > 1:
            raise ValueError(
                f"Path '{path}' to element was not unique! Perhaps "
                "you have malformed YAML?"
            )

        if not matches:
            return False

        # Get the value from NodeCoords
        value = matches[0].node

        # If path maps to an attribute value (a scalar, or a flat list of
        # scalars), then we are pointing to an attribute, not an element.
        # Elements are dicts, lists-of-elements, and empty containers.
        return self._is_element_value(value)

    def has_attr(self, path: str, attr: str) -> bool:
        """Check if an attribute exists at the specified path."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        # 2025-11-18 [JRH]: We don't check if the parent match was unique,
        # because if we are searching into a list of elements, some of which
        # have different fields, elements which don't have the attr we are
        # searching for will still show up, because lack of key=empty key in
        # yamlpath.

        if len(matches) == 0:
            return False

        found = False

        the_match = matches[0].node

        if not isinstance(the_match, list):
            the_match = [the_match]

        for m in the_match:
            if not isinstance(m, dict):
                continue

            for k in m:
                # While python/YAML doesn't distinguish between a key which maps
                # to a literal {bool, int, ...}, and one which maps to a
                # sub-element, SIERRA does, because it treats one key as
                # referring to an attribute mapping, and one referring to a
                # sub-element.
                if k == attr and self._is_attr_value(m[k]):
                    if found:
                        raise ValueError(
                            f"Specified attr '{attr}' is not unique in '{path}'"
                        )
                    found = True

        return found

    def element_change(self, path: str, tag: str, value: str) -> bool:
        """Change an element tag at the specified path.

        This isn't well-defined in YAML.  What effectively happens is that the
        subtree pointed to by ``path`` is re-added to the parent under the tag
        ``value``, and the original subtree deleted.
        """
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) == 0:
            self.logger.warning("Parent element '%s' not found", path)
            return False

        if len(matches) > 1:
            raise ValueError(f"Path '{path}' to parent was not unique!")

        parent = matches[0].node
        # Parent must be a dict to have keys
        if not isinstance(parent, dict):
            self.logger.warning("Path '%s' does not point to a dict", path)
            return False

        # Check if the key exists
        if tag not in parent:
            self.logger.warning("No such tag '%s' found in '%s'", tag, path)
            return False

        # Change the value by copying the subtree, re-adding, and deleting
        # original. Not the most elegant.
        children = parent[tag]
        del parent[tag]
        parent[value] = children

        self.logger.trace("Modified tag: '%s/%s' = '%s'", path, tag, value)
        return True

    def _element_remove_dict(
        self, path: str, tag: str, parent, noprint: bool = False
    ) -> bool:
        if tag not in parent:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'", tag, path)
            return False

        # A scalar-valued key is an attribute, not an element, and is not
        # removable via element_remove (use attr-oriented methods instead).
        if not self._is_element_value(parent[tag]):
            if not noprint:
                self.logger.warning(
                    "'%s' in '%s' is an attribute, not an element", tag, path
                )
            return False

        del parent[tag]
        return True

    def _element_remove_list(
        self, path: str, tag: str, parent, noprint: bool = False
    ) -> bool:
        subprocessor = yamlpath.Processor(self.log, parent)
        subpath = yamlpath.YAMLPath(tag)

        victims = list(subprocessor.get_nodes(subpath))
        if not victims:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'", tag, path)
            return False

        victim = victims[0].node
        if victim not in parent:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'", tag, path)
            return False

        parent.remove(victim)
        return True

    def element_remove(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove an element at the specified path."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) > 1:
            raise ValueError(
                f"Path '{path}' to parent was not unique! If you want to remove "
                "multiple matching elements, use element_remove_all()"
            )

        if len(matches) == 0 or matches[0].node is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = matches[0].node
        ret = False
        if isinstance(parent, dict):
            ret = self._element_remove_dict(path, tag, parent, noprint)
        elif isinstance(parent, list):
            ret = self._element_remove_list(path, tag, parent, noprint)

        if ret:
            self.logger.trace("Removed element '%s' from '%s'", tag, path)

        return ret

    def element_remove_all(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove the matching element at the specified path.

        YAML mappings have unique keys, so a tag matches at most one child of a
        given parent -- "remove all matching" collapses to a single removal.
        (The genuine multi-match case only exists in XML, where a parent may
        have several children with the same tag.) Delegates to element_remove.

        Note: this does NOT iterate over multiple parents matching ``path``; a
        non-unique parent path raises via element_remove, matching the other
        plugins' contract.
        """
        return self.element_remove(path, tag, noprint=noprint)

    def element_add(  # noqa: C901
        self,
        path: str,
        tag: str,
        attr: tp.Optional[types.StrDict] = None,
        allow_dup: bool = True,
        noprint: bool = False,
    ) -> bool:
        """Add tag name as a child element of enclosing parent."""
        spec = yamlpath.YAMLPath(path)
        matches = list(self.processor.get_nodes(spec))

        if len(matches) > 1:
            raise ValueError(f"Path '{path}' to parent was not unique!")

        if len(matches) == 0 or matches[0].node is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        parent = matches[0].node

        if not isinstance(parent, dict):
            if not noprint:
                self.logger.warning("Parent '%s' is not a dict", path)
            return False

        if not allow_dup and tag in parent:
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
        # Child element exists. Two cases: it exists, but has no
        # children, and it exists and has children. If it has no children, we
        # user the contents of attr to figure out if the user wants a list of
        # children, or a dict of children.
        elif tag in parent:
            if parent[tag] is None:
                parent[tag] = attr
                self.logger.trace(
                    "Create sub-element: '%s/%s' = '%s'",
                    path,
                    tag,
                    str(attr),
                )

            elif isinstance(parent[tag], list):
                parent[tag].append(attr)
                self.logger.trace(
                    "Append to element list: '%s/%s' += '%s'",
                    path,
                    tag,
                    str(attr),
                )
            elif isinstance(parent[tag], dict):
                parent[tag].update(attr)
                self.logger.trace(
                    "Merge sub-element map: '%s/%s' U '%s'",
                    path,
                    tag,
                    str(attr),
                )
        else:
            # Child doesn't exist--just assign to single sub-element.
            parent[tag] = attr
            self.logger.trace(
                "Add new element: '%s/%s' = '%s'",
                path,
                tag,
                str(attr),
            )

        self.element_adds.append(
            definition.ElementAdd(path, tag, attr if attr else {}, allow_dup)
        )
        return True


def unpickle(fpath: pathlib.Path) -> definition.ExpDefPickle:
    """Unpickle all YAML modifications from the pickle file at the path.

    Returns every modification kind (attribute changes, element additions,
    and element removals) present in the pickle, so engines that set up
    experiments with any combination of them round-trip completely.
    """
    return definition.unpickle(fpath)


__all__ = ["ExpDef", "unpickle"]
