# Copyright 2024 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Plugin for parsing and manipulating template input files in XML format."""

# Core packages
import pathlib
import logging
import xml.etree.ElementTree as ET
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.experiment import definition
from sierra.core import types


class Writer:
    """Write the XML experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, tree: ET.ElementTree) -> None:
        self.tree = tree
        self.root = tree.getroot()
        self.logger = logging.getLogger(__name__)

    def __call__(
        self, write_config: definition.WriterConfig, base_opath: pathlib.Path
    ) -> None:
        for config in write_config.values:
            self._write_with_config(base_opath, config)

    def _write_with_config(
        self, base_opath: tp.Union[pathlib.Path, str], config: dict
    ) -> None:
        tree, src_root, opath = self._prepare_tree(pathlib.Path(base_opath), config)

        if tree is None:
            self.logger.warning(
                "Cannot write non-existent tree@'%s' to '%s'", src_root, opath
            )
            return

        self.logger.trace("Write tree@%s to %s", src_root, opath)

        # Renaming tree root is not required
        if "rename_to" in config and config["rename_to"] is not None:
            tree.tag = config["rename_to"]
            self.logger.trace("Rename tree root -> %s", config["rename_to"])

        # Adding new children not required
        if all(
            k in config and config[k] is not None
            for k in ["new_children_parent", "new_children"]
        ):
            self._add_new_children(config, tree)

        # Grafts are not required
        if all(
            k in config and config[k] is not None
            for k in ["child_grafts_parent", "child_grafts"]
        ):
            self._add_grafts(config, tree)

        to_write = ET.ElementTree(tree)

        ET.indent(to_write.getroot(), space="\t", level=0)
        ET.indent(to_write, space="\t", level=0)
        to_write.write(opath, encoding="utf-8")

    def _add_grafts(self, config: dict, tree: ET.Element) -> None:

        graft_parent = tree.find(config["child_grafts_parent"])
        assert graft_parent is not None, f"Bad parent '{graft_parent}' for grafting"

        for g in config["child_grafts"]:
            self.logger.trace("Graft tree@'%s' as child under '%s'", g, graft_parent)
            elt = self.root.find(g)
            graft_parent.append(elt)

    def _add_new_children(self, config: dict, tree: ET.ElementTree) -> None:
        """Given the experiment definition, add new children as configured.

        We operate on the whole definition in-situ, rather than creating a new
        subtree with all the children because that is less error prone in terms
        of grafting the new subtree back into the experiment definition.
        """

        parent = tree.find(config["new_children_parent"])

        assert (
            parent is not None
        ), f"Could not find parent '{0}' of new children".format(
            config["new_children_parent"]
        )
        for spec in config["new_children"]:
            if spec.as_root_elt:
                # Special case: Adding children to an empty tree
                tree = ET.Element(spec.path, spec.attr)
                continue

            elt = parent.find(spec.path)

            assert elt is not None, (
                f"Could not find parent '{spec.path}' of new child element '{spec.tag}' "
                "to add"
            )

            ET.SubElement(elt, spec.tag, spec.attr)

            self.logger.trace(
                "Create child element '%s' under '%s'",
                spec.tag,
                spec.path,
            )

    def _prepare_tree(
        self, base_opath: pathlib.Path, config: dict
    ) -> tuple[tp.Optional[ET.Element], str, pathlib.Path]:
        assert "src_parent" in config, "'src_parent' key is required"
        assert (
            "src_tag" in config and config["src_tag"] is not None
        ), "'src_tag' key is required"

        if config["src_parent"] is None:
            src_root = config["src_tag"]
        else:
            src_root = "{}/{}".format(config["src_parent"], config["src_tag"])

        tree_out = self.tree.getroot().find(src_root)

        # Customizing the output write path is not required
        opath = base_opath
        if "opath_leaf" in config and config["opath_leaf"] is not None:
            opath = base_opath.with_name(base_opath.name + str(config["opath_leaf"]))

        self.logger.trace(
            "Preparing subtree write of '%s' to '%s', root='%s'",
            tree_out,
            opath,
            tree_out,
        )

        return (tree_out, src_root, opath)


def root_querypath() -> str:
    return "."


@implements.implements(definition.BaseExpDef)
class ExpDef:
    """Read, write, and modify parsed XML files into experiment definitions."""

    def __init__(
        self,
        input_fpath: pathlib.Path,
        write_config: tp.Optional[definition.WriterConfig] = None,
    ) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        self.tree = ET.parse(self.input_fpath)
        self.root = self.tree.getroot()
        self.element_adds = definition.ElementAddList()
        self.attr_chgs = definition.AttrChangeSet()

        self.logger = logging.getLogger(__name__)

    def n_mods(self) -> tuple[int, int]:
        return len(self.element_adds), len(self.attr_chgs)

    def write_config_set(self, config: definition.WriterConfig) -> None:
        """Set the write config for the object.

        Provided for cases in which the configuration is dependent on whether or
        not certain tags/element are present in the input file.

        """
        self.write_config = config

    def write(self, base_opath: pathlib.Path) -> None:
        assert self.write_config is not None, "Can't write without write config"

        writer = Writer(self.tree)
        writer(self.write_config, base_opath)

    def flatten(self, keys: list[str]) -> None:
        raise NotImplementedError("The XML expdef plugin does not support flattening")

    def attr_get(self, path: str, attr: str) -> tp.Optional[tp.Union[str, int, float]]:
        el = self.root.find(path)
        if el is not None and attr in el.attrib:
            return el.attrib[attr]
        return None

    def attr_change(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float],
        noprint: bool = False,
    ) -> bool:
        el = self.root.find(path)
        if el is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        if attr not in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' not found in path '%s'", attr, path)
            return False

        el.attrib[attr] = value
        self.logger.trace("Modify attr: '%s/%s' = '%s'", path, attr, value)

        self.attr_chgs.add(definition.AttrChange(path, attr, str(value)))
        return True

    def attr_add(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float],
        noprint: bool = False,
    ) -> bool:
        el = self.root.find(path)
        if el is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        if attr in el.attrib:
            if not noprint:
                self.logger.warning("Attribute '%s' already in path '%s'", attr, path)
            return False

        el.set(attr, value)
        self.logger.trace("Add new attribute: '%s/%s' = '%s'", path, attr, value)
        self.attr_chgs.add(definition.AttrChange(path, attr, str(value)))
        return True

    def has_element(self, path: str) -> bool:
        return self.root.find(path) is not None

    def has_attr(self, path: str, attr: str) -> bool:
        el = self.root.find(path)
        if el is None:
            return False
        return attr in el.attrib

    def element_change(self, path: str, tag: str, value: str) -> bool:
        el = self.root.find(path)
        if el is None:
            self.logger.warning("Parent element '%s' not found", path)
            return False

        for child in el:
            if child.tag == tag:
                child.tag = value
                self.logger.trace("Modify element: '%s/%s' = '%s'", path, tag, value)
                return True

        self.logger.warning("No such element '%s' found in '%s'", tag, path)
        return False

    def element_remove(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove the first matching element in ``path`` matching ``tag``."""
        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent node '%s' not found", path)
            return False

        victim = parent.find(tag)
        if victim is None:
            if not noprint:
                self.logger.warning("No victim '%s' found in parent '%s'", tag, path)
            return False

        parent.remove(victim)
        return True

    def element_remove_all(self, path: str, tag: str, noprint: bool = False) -> bool:

        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        victims = parent.findall(tag)
        if not victims:
            if not noprint:
                self.logger.warning(
                    "No victims matching '%s' found in parent '%s'", tag, path
                )
            return False

        for victim in victims:
            parent.remove(victim)
            self.logger.trace("Remove matching element: '%s/%s'", path, tag)

        return True

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
        parent = self.root.find(path)

        if parent is None:
            if not noprint:
                self.logger.warning("Parent element '%s' not found", path)
            return False

        if not allow_dup:
            if parent.find(tag) is not None:
                if not noprint:
                    self.logger.warning(
                        "Child element '%s' already in parent '%s'", tag, path
                    )
                return False

            ET.SubElement(parent, tag, attrib=attr if attr else {})
            self.logger.trace(
                "Add new unique element: '%s/%s' = '%s'",
                path,
                tag,
                str(attr),
            )
        else:
            # Use ET.Element instead of ET.SubElement so that child nodes with
            # the same 'tag' don't overwrite each other.
            child = ET.Element(tag, attrib=attr if attr else {})
            parent.append(child)
            self.logger.trace("Add new element: '%s/%s' = '%s'", path, tag, str(attr))

        self.element_adds.append(definition.ElementAdd(path, tag, attr, allow_dup))
        return True


def unpickle(
    fpath: pathlib.Path,
) -> tp.Optional[tp.Union[definition.AttrChangeSet, definition.ElementAddList]]:
    """Unickle all XML modifications from the pickle file at the path.

    You don't know how many there are, so go until you get an exception.

    """
    try:
        return definition.AttrChangeSet.unpickle(fpath)
    except (EOFError, TypeError):
        pass

    try:
        return definition.ElementAddList.unpickle(fpath)
    except EOFError:
        pass

    raise NotImplementedError


__all__ = ["ExpDef", "unpickle"]
