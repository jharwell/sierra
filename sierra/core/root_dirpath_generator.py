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

"""
Functions for generating the directory paths for the root directories for a
single batch experiment.

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

"""
# Core packages
import os
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages


def from_cmdline(args) -> tp.Dict[str, str]:
    """
    Generates the directory paths for the root directories for a single batch experiment directly
    from cmdline arguments.
    """
    template_stem, _ = os.path.splitext(
        os.path.basename(args.template_input_file))

    # Remove all '-' from the template input file stem so we know the only '-' that are in it are
    # ones that we put there.
    template_stem = template_stem.replace('-', '')

    batch_leaf = gen_batch_leaf(
        args.batch_criteria, template_stem, args.scenario)

    return regen_from_exp(args.sierra_root,
                          args.project,
                          batch_leaf,
                          args.controller)


def parse_batch_leaf(root: str) -> tp.Tuple[str, str, tp.List[str]]:
    """
    Parse a batch root into (template input file basename, scenario, batch criteria list) string
    components as they would have been specified on the cmdline.
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
                   controller: str) -> tp.Dict[str, str]:
    """
    Re-generates the directory paths for the root directories for a single batch experiment from a
    previously created batch experiment (i.e. something that was generated with
    :meth:`from_cmdline()`).

    Arguments:
        sierra_rpath: The path to the root directory where SIERRA should store everything.
        project: The name of the project plugin used.
        criteria: List of strings from the cmdline specification of the batch criteria.
        batch_root: The name of the directory that will be the root of the batch experiment (not
                    including its parent).
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
        'batch_input_root': gen_input_root(root),
        'batch_output_root': gen_output_root(root),
        'batch_graph_root': gen_graph_root(root),
        'batch_model_root': gen_model_root(root),
        'batch_stat_root': gen_statistics_root(root),
        'batch_imagize_root': gen_imagize_root(root),
        'batch_video_root': gen_video_root(root),
        'batch_stat_collate_root': gen_stat_collate_root(root),
        'batch_graph_collate_root': gen_graph_collate_root(root),
        'batch_scratch_root': gen_scratch_root(root)
    }


def gen_output_root(root: str) -> str:
    return os.path.join(root, "exp-outputs")


def gen_input_root(root: str) -> str:
    return os.path.join(root, "exp-inputs")


def gen_graph_root(root: str) -> str:
    return os.path.join(root, "graphs")


def gen_model_root(root: str) -> str:
    return os.path.join(root, "models")


def gen_statistics_root(root: str) -> str:
    return os.path.join(root, "statistics")


def gen_scratch_root(root: str) -> str:
    return os.path.join(root, "scratch")


def gen_imagize_root(root: str) -> str:
    return os.path.join(root, "imagize")


def gen_video_root(root: str) -> str:
    return os.path.join(root, "videos")


def gen_stat_collate_root(root: str) -> str:
    return os.path.join(root, "statistics", "collated")


def gen_graph_collate_root(root: str) -> str:
    return os.path.join(root, "graphs", "collated")


def gen_batch_root(sierra_rpath: str,
                   project: str,
                   criteria: tp.List[str],
                   scenario: str,
                   controller: str,
                   template_stem: str) -> str:
    """
    Generate the directory path for the root directory for batch experiments depending on what
    the batch criteria is. The directory path depends on all of the input arguments to this
    function, and if ANY of the arguments change, so should the generated path.

    Arguments:
        sierra_rpath: The path to the root directory where SIERRA should store everything.
        project: The name of the project plugin used.
        criteria: List of strings from the cmdline specification of the batch criteria.
        scenario: The cmdline specification of ``--scenario``
        batch_root: The name of the directory that will be the root of the batch experiment (not
                    including its parent).
        controller: The name of the controller used.

    Batch root is: <sierra root>/<project>/<template_basename>-<scenario>+<criteria0>+<criteria1>
    """
    batch_leaf = gen_batch_leaf(criteria, template_stem, scenario)
    return os.path.join(sierra_rpath,
                        project,
                        controller,
                        batch_leaf)


__api__ = [
    'from_cmdline',
    'regen_from_exp',
    'parse_batch_root'
]
