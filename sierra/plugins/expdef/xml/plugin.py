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

# Project packages
from sierra.core.experiment import definition
from sierra.core import types


class Writer:
    """Write the XML experiment to the filesystem according to configuration.

    More than one file may be written, as specified.
    """

    def __init__(self, root: ET.Element) -> None:
        self.root = root
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
            # May return a new root element (as_root_elt spec), which replaces
            # `tree` for the graft step and the final write below.
            tree = self._add_new_children(config, tree)

        # Grafts are not required
        if all(
            k in config and config[k] is not None
            for k in ["child_grafts_parent", "child_grafts"]
        ):
            self._add_grafts(config, tree)

        to_write = ET.ElementTree(tree)

        ET.indent(to_write, space="\t", level=0)
        to_write.write(opath, encoding="utf-8")

    def _add_grafts(self, config: dict, tree: ET.Element) -> None:

        graft_parent = tree.find(config["child_grafts_parent"])
        assert (
            graft_parent is not None
        ), f"Bad parent '{config['child_grafts_parent']}' for grafting"

        for g in config["child_grafts"]:
            self.logger.trace("Graft tree@'%s' as child under '%s'", g, graft_parent)
            elt = self.root.find(g)
            assert elt is not None, f"Could not find graft source '{g}'"
            graft_parent.append(elt)

    def _add_new_children(
        self, config: dict, tree: ET.Element
    ) -> ET.Element:
        """Given the experiment definition, add new children as configured.

        We operate on the whole definition in-situ, rather than creating a new
        subtree with all the children because that is less error prone in terms
        of grafting the new subtree back into the experiment definition.

        Returns the root element to operate on going forward. This is normally
        the ``tree`` passed in, but if a spec is flagged ``as_root_elt`` it is a
        freshly-created root element which *replaces* ``tree`` (used to build an
        output file from scratch and then graft real content underneath it).
        """
        # Handle an as-root spec first: it establishes a brand-new root element
        # that replaces the incoming tree. Subsequent normal children (and later
        # grafts) are resolved against this new root.
        for spec in config["new_children"]:
            if spec.as_root_elt:
                # 'tag' is the new root's name; 'path' is empty for as_root
                # specs (see ElementAdd.as_root), so it must NOT be used here.
                tree = ET.Element(spec.tag, spec.attr if spec.attr else {})
                self.logger.trace("Create new root element '%s'", spec.tag)

        parent = tree.find(config["new_children_parent"])

        assert parent is not None, (
            f"Could not find parent '{config['new_children_parent']}' of new "
            "children"
        )
        for spec in config["new_children"]:
            if spec.as_root_elt:
                # Already handled above.
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

        return tree

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

        tree_out = self.root.find(src_root)

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


class ExpDef(definition.BaseExpDef):
    """Read, write, and modify parsed XML files into experiment definitions."""

    def __init__(
        self,
        input_fpath: pathlib.Path,
        write_config: tp.Optional[definition.WriterConfig] = None,
    ) -> None:

        self.write_config = write_config
        self.input_fpath = input_fpath
        self.tree = ET.parse(self.input_fpath)
        root = self.tree.getroot()
        assert root is not None, f"Parsed XML {self.input_fpath} has no root"
        self.root: ET.Element = root
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

        writer = Writer(self.root)
        writer(self.write_config, base_opath)

    def flatten(self, keys: list[str]) -> None:
        raise NotImplementedError("The XML expdef plugin does not support flattening")

    @staticmethod
    def _is_attr_value(value: tp.Any) -> bool:
        """Determine if a value qualifies as an attribute value.

        Unlike the YAML and JSON plugins, XML has no array/object types: an
        attribute value is always serialized as a string. A list or dict
        therefore cannot be represented as an XML attribute -- assigning one
        would be silently stringified by ElementTree into a Python-repr string
        (e.g. ``ports="[80, 443]"``), corrupting the output.

        This helper exists so the XML plugin shares the same vocabulary as the
        other formats, but here it only ever returns True for genuine scalars.
        SIERRA's notion of an "array attribute" (a flat list of scalars) is not
        expressible in XML and is rejected by :meth:`attr_change` /
        :meth:`attr_add` rather than classified here.
        """
        return not isinstance(value, (list, dict))

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

        # XML attribute values are strings; a list/dict cannot be represented
        # and would be silently corrupted on write. Reject it explicitly.
        if not self._is_attr_value(value):
            if not noprint:
                self.logger.warning(
                    "Cannot assign non-scalar value to XML attribute '%s' in '%s'; "
                    "XML attributes cannot hold arrays or objects",
                    attr,
                    path,
                )
            return False

        el.attrib[attr] = str(value)
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

        # XML attribute values are strings; a list/dict cannot be represented
        # and would be silently corrupted on write. Reject it explicitly.
        if not self._is_attr_value(value):
            if not noprint:
                self.logger.warning(
                    "Cannot assign non-scalar value to XML attribute '%s' in '%s'; "
                    "XML attributes cannot hold arrays or objects",
                    attr,
                    path,
                )
            return False

        el.set(attr, str(value))
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

        self.element_adds.append(
            definition.ElementAdd(path, tag, attr if attr else {}, allow_dup)
        )
        return True


def unpickle(fpath: pathlib.Path) -> definition.ExpDefPickle:
    """Unpickle all XML modifications from the pickle file at the path.

    Returns every modification kind (attribute changes, element additions, and
    element removals) present in the pickle, so engines that set up experiments
    with any combination of them round-trip completely.
    """
    return definition.unpickle(fpath)


__all__ = ["ExpDef", "unpickle"]
