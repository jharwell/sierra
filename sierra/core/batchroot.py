#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Functionality for generating root directory paths for a batch experiment.

See :ref:`usage/run-time-tree` for details about the defined root
directories in SIERRA.
"""

# Core packages
import typing as tp
import logging
import pathlib
import argparse
from dataclasses import dataclass

# 3rd party packages

# Project packages


class ExpRootLeaf:
    """
    Representation of the "name" in pathlib parlance in :class:`ExpRoot`.
    """

    @staticmethod
    def from_name(leaf: str) -> "ExpRootLeaf":
        """Parse the the directory name to extract leaf components.

        "Name" here is pathlib parlance. Expected to be of the form::

          <template stem>-[<criteria0>+<criteria1>]...

        This function is the inverse of :func:`to_path()`.
        """

        template_stem, bc_str = leaf.split("-")
        bc = bc_str.split("+")

        if not isinstance(bc, list):  # Univariate batch criteria
            bc = [bc]

        return ExpRootLeaf(bc, template_stem)

    @staticmethod
    def from_components(bc: list[str], template_stem: str) -> "ExpRootLeaf":
        """Create the leaf representation directory from the components."""
        return ExpRootLeaf(bc, template_stem)

    def __init__(self, bc: list[str], template_stem: str) -> None:
        self.bc = bc
        self.template_stem = template_stem

    def to_path(self) -> pathlib.Path:
        """Get the leaf as a ``pathlib.Path`` object."""
        return pathlib.Path("{}-{}".format(self.template_stem, "+".join(self.bc)))

    def to_str(self) -> str:
        return str(self.to_path())


class ExpRoot:
    """
    Representation of the filesystem path containing all per-experiment data.
    """

    def __init__(
        self,
        sierra_root: str,
        project: str,
        controller: str,
        scenario: str,
        leaf: ExpRootLeaf,
    ) -> None:
        """Generate the directory path for the rootbatch root directory.

        The directory path depends on all of the input arguments to this
        class, and if ANY of the arguments change, so will the generated
        path. Root is::

          <sierra_root>/<project>/<controller>/<scenario>/<criterias>/<template_basename>+<criterias>

        Args:
           root: The path to the root directory where SIERRA should store
                 everything.

           project: The name of the project plugin used.

           controller: The name of the controller used.

           scenario: The name of the scenario used.

           leaf: The batch criteria + ``--expdef-template`` stem.
        """
        self.leaf = leaf

        self.project = project
        self.controller = controller
        self.scenario = scenario

        if self.controller is None:
            raise RuntimeError("--controller must be specified")
        if self.scenario is None:
            raise RuntimeError("--scenario must be specified")

        # Don't reslove() the path--that makes symlinked dirs under $HOME throw
        # errors which are fatal from pathlib's POV, but actually harmless.
        self.sierra_root = pathlib.Path(sierra_root)

    def to_path(self) -> pathlib.Path:
        return (
            self.sierra_root
            / self.project
            / self.controller
            / self.scenario
            / self.leaf.to_path()
        )

    def to_str(self) -> str:
        return str(self.to_path())


@dataclass
class PathSet:
    """
    The set of filesystem paths under ``--sierra-root`` that SIERRA uses.

    Collected here in the interest of DRY.
    """

    input_root: pathlib.Path
    output_root: pathlib.Path
    graph_root: pathlib.Path
    model_root: pathlib.Path
    model_interexp_root: pathlib.Path
    stat_root: pathlib.Path
    stat_exec_root: pathlib.Path
    imagize_root: pathlib.Path
    video_root: pathlib.Path
    stat_interexp_root: pathlib.Path
    graph_interexp_root: pathlib.Path
    scratch_root: pathlib.Path
    root: pathlib.Path

    @classmethod
    def from_root(cls, root: ExpRoot) -> "PathSet":
        """Create PathSet from an ExpRoot."""
        root_path = root.to_path()
        model_root = root_path / "models"
        stat_root = root_path / "statistics"
        graph_root = root_path / "graphs"

        return cls(
            input_root=root_path / "exp-inputs",
            output_root=root_path / "exp-outputs",
            graph_root=graph_root,
            model_root=model_root,
            model_interexp_root=model_root / "inter-exp",
            stat_root=stat_root,
            stat_exec_root=stat_root / "exec",
            imagize_root=root_path / "imagize",
            video_root=root_path / "videos",
            stat_interexp_root=stat_root / "inter-exp",
            graph_interexp_root=graph_root / "inter-exp",
            scratch_root=root_path / "scratch",
            root=root_path,
        )

    def __str__(self) -> str:
        """
        Convert the batch eperiment pathset to a GNU ``tree``-like format string.

        No recursion. Everything is shown in a one-level breakdown relative to
        the batch root. Could be improved by using recursion, but this is
        sufficient for now.
        """
        # pointers:
        tee = "├── "
        last = "└── "

        contents = [
            self.input_root,
            self.output_root,
            self.graph_root,
            self.model_root,
            self.stat_root,
            self.stat_exec_root,
            self.imagize_root,
            self.video_root,
            self.stat_interexp_root,
            self.graph_interexp_root,
            self.scratch_root,
        ]
        contents.sort()
        pointers = [tee] * (len(contents) - 1) + [last]
        dirs = ""
        for pointer, path in zip(pointers, contents):
            dirs += f"\n{pointer}{path.relative_to(self.root)}"

        return str(self.root.resolve()) + dirs


def from_cmdline(args: argparse.Namespace) -> PathSet:
    """Generate directory paths directly from cmdline arguments."""
    template = pathlib.Path(args.expdef_template)

    # Remove all '-' from the template input file stem so we know the only '-'
    # that are in it are ones that we put there.
    template_stem = template.stem.replace("-", "")
    batch_leaf = ExpRootLeaf(args.batch_criteria, str(template_stem))

    return from_exp(
        args.sierra_root, args.project, batch_leaf, args.controller, args.scenario
    )


def from_exp(
    sierra_root: str,
    project: str,
    batch_leaf: ExpRootLeaf,
    controller: str,
    scenario: str,
) -> PathSet:
    """Regenerate directory pathroots from a batch experiment.

    Args:

    sierra_root: The value of ``--sierra-root``.

    project: The value of ``--project``.

    batch_leaf: The name of the directory that will be the root of the batch
    experiment (not including its parent).

    controller: The value of ``--controller``.

    scenario: The value of ``--scenario``.
    """
    root = ExpRoot(sierra_root, project, controller, scenario, batch_leaf)
    logging.info("Generated batchroot %s", root.to_path())
    return PathSet.from_root(root)


__all__ = [
    "ExpRoot",
    "ExpRootLeaf",
    "PathSet",
    "from_cmdline",
    "from_exp",
]
