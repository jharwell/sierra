#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Functionality for generating root directory paths for a batch experiment.

See :ref:`ln-sierra-usage-runtime-exp-tree` for details about the defined root
directories in SIERRA.
"""

# Core packages
import typing as tp
import logging
import pathlib
import argparse

# 3rd party packages

# Project packages


class ExpRootLeaf():
    @staticmethod
    def from_name(leaf: str) -> 'ExpRootLeaf':
        template_stem = ''.join(leaf.split('-')[0])
        scenario_and_bc = leaf.split('-')[1].split('+')
        scenario = scenario_and_bc[0]
        bc = scenario_and_bc[1:]  # type: tp.Union[tp.List[str],str]

        if not isinstance(bc, list):  # Univariate batch criteria
            bc = [bc]

        return ExpRootLeaf(bc, template_stem, scenario)

    @staticmethod
    def from_components(bc: tp.List[str],
                        template_stem: str,
                        scenario: str) -> 'ExpRootLeaf':
        return ExpRootLeaf(bc, template_stem, scenario)

    def __init__(self, bc: tp.List[str],
                 template_stem: str,
                 scenario: str) -> None:
        self.bc = bc
        self.template_stem = template_stem
        self.scenario = scenario

    def to_path(self) -> pathlib.Path:
        root = pathlib.Path(f"{0}-{1}+{2}" % (self.template_stem,
                                              self.scenario,
                                              '+'.join(self.bc)))
        logging.debug("Generated batch leaf %s", root)
        return root


class ExpRoot():
    def __init__(self,
                 sierra_root: str,
                 project: str,
                 controller: str,
                 leaf: ExpRootLeaf) -> None:
        """Generate the directory path for the rootbatch root directory.

        The directory path depends on all of the input arguments to this function,
        and if ANY of the arguments change, so will the generated path.

         root is:
        <sierra_root>/<project>/<template_basename>-<scenario>+<criteria0>+<criteria1>

        Arguments:

            root: The path to the root directory where SIERRA should store
                  everything.

            project: The name of the project plugin used.

            controller: The name of the controller used.

        """
        self.leaf = leaf

        self.project = project
        self.controller = controller

        # Don't reslove() the path--that makes symlinked dirs under $HOME
        # through errors which are fatal from pathlib's POV, but actually
        # harmless.
        self.sierra_root = pathlib.Path(sierra_root)

    def to_path(self) -> pathlib.Path:
        return self.sierra_root / self.project / self.controller / self.leaf.to_path()


class PathSet():
    def __init__(self, root: ExpRoot) -> None:
        self.root = root
        self.input_root = self.root.to_path() / "exp-inputs"
        self.output_root = self.root.to_path() / "exp-outputs"
        self.graph_root = self.root.to_path() / "graphs"
        self.model_root = self.root.to_path() / "models"
        self.stat_root = self.root.to_path() / "statistics"
        self.stat_exec_root = self.stat_root.to_path() / "exec"
        self.imagize_root = self.root.to_path() / "imagize"
        self.video_root = self.root.to_path() / "videos"
        self.stat_collate = self.stat_root.to_path() / "collated"
        self.graph_collate = self.graph_root.to_path() / "collated"
        self.scratch_root = self.root.to_path() / "scratch"


def from_cmdline(args: argparse.Namespace) -> PathSet:
    """Generate directory paths directly from cmdline arguments.

    """
    template = pathlib.Path(args.template_input_file)

    # Remove all '-' from the template input file stem so we know the only '-'
    # that are in it are ones that we put there.
    template_stem = template.stem.replace('-', '')

    batch_leaf = ExpRootLeaf(args.batch_criteria,
                             str(template_stem),
                             args.scenario)

    return from_exp(args.sierra_root,
                    args.project,
                    batch_leaf,
                    args.controller)


def from_exp(sierra_rpath: str,
             project: str,
             batch_leaf: ExpRootLeaf,
             controller: str) -> PathSet:
    """Regenerate directory pathroots from a previously created batch experiment.

    Arguments:

        sierra_rpath: The path to the root directory where SIERRA should store
                      everything.

        project: The name of the project plugin used.

        criteria: List of strings from the cmdline specification of the batch
                  criteria.

        batch_root: The name of the directory that will be the root of the batch
                    experiment (not including its parent).

        controller: The name of the controller used.

    """
    root = ExpRoot(sierra_rpath,
                   project,
                   controller,
                   batch_leaf)
    logging.info('Generated batch root %s', root)
    return PathSet(root)
