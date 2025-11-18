# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Functionality for reading, writing, etc., experiment definitions.

Format-specific bits handled at a lower level via plugin; this is generic
functionality for experiment definitions.
"""

# Core packages
import pathlib
import typing as tp
import logging
import pickle

# 3rd party packages
import implements

# Project packages
from sierra.core import types


class WriterConfig:
    """Config for writing :class:`~sierra.core.experiment.definition.BaseExpDef`.

    Different parts of the AST can be written to multiple files, as configured.

    The order of operations for the applying the config should be:

        - Extraction of subtree

        - Renaming subtree root

        - Adding new children

        - Adding grafts

    Attributes: values: Dict with the following possible key, value pairs:

        - ``src_parent`` - The parent of the root of the AST specifying a
          sub-tree to write out as a child of ``new_children_parent``, or
          ``None`` to write out entire AST.  This key is required.  If ``None``
          omitted then then tree rooted at ``src_tag`` is written out.
          Otherwise, the subtree rooted at ``<src_parent>/<src_tag>`` is written
          out instead.

        - ``src_tag`` - Unique query path expression for the child element
          within ``src_parent`` to write out; that is this tag is the root of
          the sub-tree within the experiment definition to write out.  This key
          is required.

        - ``rename_to`` - String to rename the root of the AST written out.
          This key is optional, and should be processed *after* ``{src_parent,
          src_tag}``.

        - ``new_children_parent`` - Unique query path expression for the parent
          element to create new child elements under via ``new_children``.  This
          key is optional; can be omitted or set to ``None``.

        - ``new_children`` - Ordered List of
          :class:`~sierra.core.experiment.definition.ElementAdd` objects to use
          to create new child elements under ``new_children_parent``.  Must form
          a tree with a single root when added in order.

        - ``opath_leaf`` - Additional bits added to whatever the opath file stem
          that is set for the
          :class:`~sierra.core.experiment.definition.BaseExpDef` instance.  This
          key is optional.  Can be used to add an extension; this is helpful
          because some engines require input files to have a certain
          extension, and SIERRA strips out the extension passed to
          ``--expdef-template`` used as the bases for creating experiments.

        - ``child_grafts_parent`` - Unique query path expression for the parent
          element to for grafting elements under via ``child_grafts``.  This
          path expression is *relative* to ``<src_tag>`` due to ordering.  This
          key is optional; can be omitted or set to ``None``.

        - ``child_grafts`` - Additional bits of the current AST to add under
          ``child_grafts_parent`` in the written out experiment definition,
          specified as a list of query path strings.  This key is optional.
    """

    def __init__(self, values: list[dict]) -> None:
        assert isinstance(values, list), "values must be a list of dicts"

        self.values = values

    def add(self, value: dict) -> None:
        self.values.append(value)


class BaseExpDef(implements.Interface):
    """Base class for experiment definitions."""

    def __init__(
        self, input_fpath: pathlib.Path, write_config: tp.Optional[WriterConfig] = None
    ) -> None:
        pass

    def write(self, base_opath: pathlib.Path) -> None:
        """Write the definition stored in the object to the filesystem."""
        raise NotImplementedError

    def n_mods(self) -> tuple[int, int]:
        """
        Get the # (adds, changes) as a tuple.
        """
        raise NotImplementedError

    def flatten(self, keys: list[str]) -> None:
        """
        Replace the specified filepath attributes with their contents.

        Filepaths are interpreted relative to the directory in which the
        original experiment definition template resides, and assumed to be
        defined as such.
        """
        raise NotImplementedError

    def attr_get(self, path: str, attr: str) -> tp.Union[str, int, float, None]:
        """Retrieve the specified attribute of the element at the specified path.

        If it does not exist, None is returned.

        """
        raise NotImplementedError

    def attr_change(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float],
        noprint: bool = False,
    ) -> bool:
        """Change the specified attribute of the element at the specified path.

        Only the attribute of the *FIRST* element matching the specified path is
        changed.

        Arguments:

          path: An expression uniquely identifying the element containing the
                attribute to change.  The element must exist or an error will be
                raised.

          attr: An expression uniquely identify the attribute to change within
                the enclosing element.

          value: The value to set the attribute to.
        """
        raise NotImplementedError

    def attr_add(
        self,
        path: str,
        attr: str,
        value: tp.Union[str, int, float],
        noprint: bool = False,
    ) -> bool:
        """Add the specified attribute to the element matching the specified path.

        Only the *FIRST* element matching the specified path searching from the
        tree root is modified.

        Arguments:

          path: An expression uniquely identifying the element containing the
                attribute to add. The element must exist or an error will be
                raised.

          attr: An expression uniquely identifying the attribute to change
                within the enclosing element.

          value: The value to set the attribute to.

        """
        raise NotImplementedError

    def has_element(self, path: str) -> bool:
        """Determine if the element uniquely identified by ``path`` exists."""
        raise NotImplementedError

    def has_attr(self, path: str, attr: str) -> bool:
        """Determine if the attribute uniquely identified by ``path`` exists."""
        raise NotImplementedError

    def element_change(self, path: str, tag: str, value: str) -> bool:
        """
        Change the specified tag of the element matching the specified path.

        Arguments:

          path: An expression uniquely identifying the element containing the
                tag to change. The element must exist or an error will be
                raised.

          tag: An expression uniquely identifying the tag to change within the
                enclosing element.

          value: The value to set the tag to.
        """
        raise NotImplementedError

    def element_remove(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove the specified child ``tag``  in the enclosing parent.

        If more than one tag matches, only one is removed. If the path does not
        exist, nothing is done.

        Arguments:

          path: An expression uniquely identifying the  element containing the
                tag to remove. The element must exist or an error will be
                raised.

          tag: An expression uniquely identifying the tag to remove within the
               enclosing element.

        """
        raise NotImplementedError

    def element_remove_all(self, path: str, tag: str, noprint: bool = False) -> bool:
        """Remove the specified child tag(s) in the enclosing parent.

        If more than one tag matches in the parent, all matching child tags are
        removed.

        Arguments:

          path: An expression uniquely identifying the element containing the
                tag(s) to remove. The element must exist or an error will be
                raised.

          tag: An expression uniquely identifying the tag to remove within the
               enclosing element.

        """
        raise NotImplementedError

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
        raise NotImplementedError


class AttrChange:
    """
    Specification for a change to an existing expdef attribute.
    """

    def __init__(self, path: str, attr: str, value: tp.Union[str, int, float]) -> None:
        self.path = path
        self.attr = attr
        self.value = value

    def __iter__(self):
        yield from [self.path, self.attr, self.value]

    def __repr__(self) -> str:
        return self.path + "/" + self.attr + ": " + str(self.value)


class NullMod:
    """
    Specification for a null-change (no change) to an existing expdef.
    """

    def __init__(self) -> None:
        pass

    def __iter__(self):
        yield from []


class ElementRm:
    """
    Specification for removal of an existing expdef tag.
    """

    def __init__(self, path: str, tag: str):
        """
        Init the object.

        Arguments:

            path: The path to the **parent** of the tag you want to remove, in
                  relevant syntax.

            tag: The name of the tag to remove.
        """
        self.path = path
        self.tag = tag

    def __iter__(self):
        yield from [self.path, self.tag]

    def __repr__(self) -> str:
        return self.path + "/" + self.tag


class ElementAdd:
    """
    Specification for adding a new expdef tag.

    The tag may be added idempotently, or duplicates can be allowed.
    """

    @staticmethod
    def as_root(tag: str, attr: types.StrDict) -> "ElementAdd":
        return ElementAdd("", tag, attr, False, True)

    def __init__(
        self,
        path: str,
        tag: str,
        attr: types.StrDict,
        allow_dup: bool,
        as_root: bool = False,
    ):
        """
        Init the object.

        Arguments:

            path: The path to the **parent** tag you want to add a new tag
                  under, in appropriate syntax. If None, then the tag will be
                  added as the root tag.

            tag: The name of the tag to add.

            attr: A dictionary of (attribute, value) pairs to also create as
                  children of the new tag when creating the new tag.
        """

        self.path = path
        self.tag = tag
        self.attr = attr
        self.allow_dup = allow_dup
        self.as_root_elt = as_root

    def __iter__(self):
        yield from [self.path, self.tag, self.attr]

    def __repr__(self) -> str:
        return self.path + "/" + self.tag + ": " + str(self.attr)


class AttrChangeSet:
    """
    Data structure for :class:`AttrChange` objects.

    The order in which attributes are changed doesn't matter from the standpoint
    of correctness (i.e., different orders won't cause crashes).

    """

    @staticmethod
    def unpickle(fpath: pathlib.Path) -> "AttrChangeSet":
        """Unpickle changes.

        You don't know how many there are, so go until you get an exception.

        """
        exp_def = AttrChangeSet()

        try:
            with fpath.open("rb") as f:
                while True:
                    exp_def |= AttrChangeSet(*pickle.load(f))
        except EOFError:
            pass
        return exp_def

    def __init__(self, *args: tp.Union[AttrChange, NullMod]) -> None:
        self.changes = set(args)
        self.logger = logging.getLogger(__name__)

    def __len__(self) -> int:
        return len(self.changes)

    def __iter__(self) -> tp.Iterator[tp.Union[AttrChange, NullMod]]:
        return iter(self.changes)

    def __ior__(self, other: "AttrChangeSet") -> "AttrChangeSet":
        self.changes |= other.changes
        return self

    def __or__(self, other: "AttrChangeSet") -> "AttrChangeSet":
        new = AttrChangeSet(*self.changes)
        new |= other
        return new

    def __repr__(self) -> str:
        return str(self.changes)

    def add(self, chg: AttrChange) -> None:
        self.changes.add(chg)

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils  # noqa: PLC0415

        if delete and utils.path_exists(fpath):
            fpath.unlink()

        with fpath.open("ab") as f:
            utils.pickle_dump(self.changes, f)


class ElementRmList:
    """
    Data structure for :class:`ElementRm` objects.

    The order in which tags are removed matters (i.e., if you remove dependent
    tags in the wrong order you will get an exception), hence the list
    representation.

    """

    def __init__(self, *args: ElementRm) -> None:
        self.rms = list(args)

    def __len__(self) -> int:
        return len(self.rms)

    def __iter__(self) -> tp.Iterator[ElementRm]:
        return iter(self.rms)

    def __repr__(self) -> str:
        return str(self.rms)

    def extend(self, other: "ElementRmList") -> None:
        self.rms.extend(other.rms)

    def append(self, other: ElementRm) -> None:
        self.rms.append(other)

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils  # noqa: PLC0415

        if delete and utils.path_exists(fpath):
            fpath.unlink()

        with fpath.open("ab") as f:
            utils.pickle_dump(self.rms, f)


class ElementAddList:
    """
    Data structure for :class:`ElementAdd` objects.

    The order in which tags are added matters (i.e., if you add dependent tags
    in the wrong order you will get an exception), hence the list
    representation.
    """

    @staticmethod
    def unpickle(fpath: pathlib.Path) -> tp.Optional["ElementAddList"]:
        """Unpickle modifications.

        You don't know how many there are, so go until you get an exception.

        """
        exp_def = ElementAddList()

        try:
            with fpath.open("rb") as f:
                while True:
                    exp_def.append(*pickle.load(f))
        except EOFError:
            pass
        return exp_def

    def __init__(self, *args: ElementAdd) -> None:
        self.adds = list(args)

    def __len__(self) -> int:
        return len(self.adds)

    def __iter__(self) -> tp.Iterator[ElementAdd]:
        return iter(self.adds)

    def __repr__(self) -> str:
        return str(self.adds)

    def extend(self, other: "ElementAddList") -> None:
        self.adds.extend(other.adds)

    def append(self, other: ElementAdd) -> None:
        self.adds.append(other)

    def prepend(self, other: ElementAdd) -> None:
        self.adds.insert(0, other)

    def pickle(self, fpath: pathlib.Path, delete: bool = False) -> None:
        from sierra.core import utils  # noqa: PLC0415

        if delete and utils.path_exists(fpath):
            fpath.unlink()

        with fpath.open("ab") as f:
            utils.pickle_dump(self.adds, f)


__all__ = [
    "AttrChange",
    "AttrChangeSet",
    "BaseExpDef",
    "ElementAdd",
    "ElementAddList",
    "ElementRm",
    "ElementRmList",
    "NullMod",
    "WriterConfig",
]
