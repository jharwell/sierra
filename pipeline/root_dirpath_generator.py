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
Functions for generating the directory paths for the root directories for a single batched
experiment.

- The batch experiment root. ALL files (inputs and outputs) are written to this directory, which
  will be under ``--sierra-root``. Named using a combination of ``--scenario`` (block
  distribution + arena dimensions) and ``--batch-criteria`` in order to guarantee uniqueness
  among batch roots anytime the batch criteria or scenario change.

- The batch generation root. All input files will be generated under this root
  directory. Named ``<batch experiment root>/exp-inputs``.

- The batch output root. All output files will accrue under this root
  directory. Each experiment will get their own directory in this root for its outputs to
  accrue into. Named ``<batch experiment root>/exp-outputs``.

- The batch graph root. All generated graphs will acrrue under this root directory. Each
  experiment will get their own directory in this root for their graphs to accrue
  into. Named ``<batch experiment root>/graphs``.
"""
import os
import logging
import typing as tp


def from_cmdline(args):
    """
    Generates the directory paths for the root directories for a single batched experiment directly
    from cmdline arguments.
    """
    template_stem, _ = os.path.splitext(os.path.basename(args.template_input_file))

    # Remove all '-' from the template input file stem so we know the only '-' that are in it are
    # ones that we put there.
    return regen_from_exp(args.sierra_root,
                          args.batch_criteria,
                          template_stem.replace('-', '') + '-' + args.scenario,
                          args.controller)


def parse_batch_root(root: str):
    """
    Parse a batch root into (template input file basename, scenario) components.
    """
    template_basename = ''.join(root.split('-')[:-1])
    scenario = ''.join(root.split('-')[1:])

    return (template_basename, scenario)


def regen_from_exp(sierra_root: str,
                   batch_criteria: tp.List[str],
                   batch_root: str,
                   controller: str):
    """
    Re-generates the directory paths for the root directories for a single batched experiment from a
    previously created batch experiment (i.e. something that was generated with
    :meth:`from_cmdline()`).
    """
    template_basename, scenario = parse_batch_root(batch_root)
    root = __gen_batch_root(sierra_root,
                            batch_criteria,
                            scenario,
                            controller,
                            template_basename)
    logging.info('Generated batch root %s', root)
    return {
        'generation_root': os.path.join(root, "exp-inputs"),
        'output_root': os.path.join(root, "exp-outputs"),
        'graph_root': os.path.join(root, "graphs")
    }


def __gen_batch_root(sierra_root: str,
                     batch_criteria: tp.List[str],
                     scenario: str,
                     controller: str,
                     template_basename: str):
    """
    Generate the directory path for the root directory for batch experiments depending on what
    the batch criteria is. The default is to use the block distribution type + arena size to
    differentiate between batched experiments, for some batch criteria, those will be the same
    and so you need to use the batch criteria definition itself to uniquely identify in all
    cases.
    """

    problematica = ['temporal_variance', 'constant_density']
    for p in problematica:
        for b in batch_criteria:
            if p in b:
                # use dash instead of dot in the criteria string to not confuse external
                # programs that rely on file extensions.
                scenario = scenario + '+' + b.replace('-', '')

    return os.path.join(sierra_root,
                        controller,
                        template_basename + '-' + scenario)
