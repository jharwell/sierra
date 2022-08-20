# Copyright 2018 John Harwell, All rights reserved.
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

"""Functions for generating root directory paths for a batch experiment.

- The batch experiment root. ALL files (inputs and outputs) are written to this
  directory, which will be under ``--sierra-root``. Named using a combination of
  ``--scenario`` (block distribution + arena dimensions) and
  ``--batch-criteria`` in order to guarantee uniqueness among batch roots
  anytime the batch criteria or scenario change.

- The batch input root. All input files will be generated under this root
  directory. Named ``<batch experiment root>/exp-inputs``.

- The batch output root. All output files will accrue under this root
  directory. Each experiment will get their own directory in this root for its
  outputs to accrue into. Named ``<batch experiment root>/exp-outputs``.

- The batch graph root. All generated graphs will acrrue under this root
  directory. Each experiment will get their own directory in this root for their
  graphs to accrue into. Named ``<batch experiment root>/graphs``.

- The batch model root. All model outputs will accrue under this root
  directory. Each experiment will get their own directory in this root for their
  model outputs to accrue into. Named ``<batch experiment root>/models``.

- The batch statistics root. All statistics generated during stage 3 will accrue
  under this root directory. Each experiment will get their own directory in
  this root for their statistics. Named
  ``<batch experiment root>/statistics``.

- The batch imagizing root. All images generated during stage 3 will accrue
  under this root directory. Each experiment will get their own directory in
  this root for their images. Named
  ``<batch experiment root>/images``.

- The batch video root. All videos rendered during stage 4 will accrue
  under this root directory. Each experiment will get their own directory in
  this root for their videos. Named
  ``<batch experiment root>/videos``.

- The batch scratch root. All GNU parallel outputs, ``--exec-env`` artifacts
  will appear under here. Each experiment will get their own directory in this
  root for their own scratch. This root is separate from experiment inputs to
  make checking for segfaults, tar-ing experiments, etc. easier. Named ``<batch
  experiment root>/scratch``.

"""
# Core packages
import os
import typing as tp
import logging
import argparse
import pathlib

# 3rd party packages

# Project packages


def from_cmdline(args: argparse.Namespace) -> tp.Dict[str, pathlib.Path]:
    """Generate directory paths directly from cmdline arguments.

    """
    template = pathlib.Path(args.template_input_file)

    # Remove all '-' from the template input file stem so we know the only '-'
    # that are in it are ones that we put there.
    template_stem = template.stem.replace('-', '')

    batch_leaf = gen_batch_leaf(args.batch_criteria,
                                str(template_stem),
                                args.scenario)

    return regen_from_exp(args.sierra_root,
                          args.project,
                          batch_leaf,
                          args.controller)


def parse_batch_leaf(root: str) -> tp.Tuple[str, str, tp.List[str]]:
    """Parse a batch root (dirpath leaf).

    Parsed into (template input file basename, scenario, batch criteria list)
    string components as they would have been specified on the cmdline.

    """
    template_stem = ''.join(root.split('-')[0])
    scenario_and_bc = root.split('-')[1].split('+')
    scenario = scenario_and_bc[0]
    bc = scenario_and_bc[1:]  # type: tp.Union[tp.List[str],str]

    if not isinstance(bc, list):  # Univariate batch criteria
        bc = [bc]

    return (template_stem, scenario, bc)


def gen_batch_leaf(criteria: tp.List[str],
                   template_stem: str,
                   scenario: str) -> str:
    leaf = template_stem + '-' + scenario + '+' + '+'.join(criteria)
    logging.debug("Generated batch leaf %s", leaf)

    return leaf


def regen_from_exp(sierra_rpath: str,
                   project: str,
                   batch_leaf: str,
                   controller: str) -> tp.Dict[str, pathlib.Path]:
    """Regenerate directory paths from a previously created batch experiment.

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
    template_stem, scenario, bc = parse_batch_leaf(batch_leaf)

    root = gen_batch_root(sierra_rpath,
                          project,
                          bc,
                          scenario,
                          controller,
                          template_stem)
    logging.info('Generated batch root %s', root)
    return {
        'batch_root': root,
        'batch_input_root': _gen_input_root(root),
        'batch_output_root': _gen_output_root(root),
        'batch_graph_root': _gen_graph_root(root),
        'batch_model_root': _gen_model_root(root),
        'batch_stat_root': _gen_statistics_root(root),
        'batch_imagize_root': _gen_imagize_root(root),
        'batch_video_root': _gen_video_root(root),
        'batch_stat_collate_root': _gen_stat_collate_root(root),
        'batch_graph_collate_root': _gen_graph_collate_root(root),
        'batch_scratch_root': _gen_scratch_root(root)
    }


def gen_batch_root(root: str,
                   project: str,
                   criteria: tp.List[str],
                   scenario: str,
                   controller: str,
                   template_stem: str) -> pathlib.Path:
    """Generate the directory path for the batch root directory.

    The directory path depends on all of the input arguments to this function,
    and if ANY of the arguments change, so will the generated path.

    Batch root is:
    <sierra_root>/<project>/<template_basename>-<scenario>+<criteria0>+<criteria1>

    Arguments:

        root: The path to the root directory where SIERRA should store
              everything.

        project: The name of the project plugin used.

        criteria: List of strings from the cmdline specification of the batch
                  criteria.

        scenario: The cmdline specification of ``--scenario``

        batch_root: The name of the directory that will be the root of the batch
                    experiment (not including its parent).

        controller: The name of the controller used.

    """
    batch_leaf = gen_batch_leaf(criteria, template_stem, scenario)
    sierra_root = pathlib.Path(root).resolve()
    return sierra_root / project / controller / batch_leaf


def _gen_output_root(root: pathlib.Path) -> pathlib.Path:
    return root / "exp-outputs"


def _gen_input_root(root: pathlib.Path) -> pathlib.Path:
    return root / "exp-inputs"


def _gen_graph_root(root: pathlib.Path) -> pathlib.Path:
    return root / "graphs"


def _gen_model_root(root: pathlib.Path) -> pathlib.Path:
    return root / "models"


def _gen_statistics_root(root: pathlib.Path) -> pathlib.Path:
    return root / "statistics"


def _gen_scratch_root(root: pathlib.Path) -> pathlib.Path:
    return root / "scratch"


def _gen_imagize_root(root: pathlib.Path) -> pathlib.Path:
    return root / "imagize"


def _gen_video_root(root: pathlib.Path) -> pathlib.Path:
    return root / "videos"


def _gen_stat_collate_root(root: pathlib.Path) -> pathlib.Path:
    return root / "statistics" / "collated"


def _gen_graph_collate_root(root: pathlib.Path) -> pathlib.Path:
    return root / "graphs" / "collated"


__api__ = [
    'from_cmdline',
    'regen_from_exp',
    'parse_batch_leaf',
    'gen_batch_root'
]
