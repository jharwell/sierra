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
"""Experiment creation classes.

Experiment creation takes an experiment definition `generated` by classes in
``exp_generators.py`` and writes the experiment to the filesystem.

"""

# Core packages
import os
import random
import copy
import logging
import time
import pickle
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import config, utils, types, platform
import sierra.core.plugin_manager as pm
from sierra.core.generators.exp_generators import BatchExpDefGenerator
from sierra.core.experiment import bindings, definition


class ExpCreator:
    """Instantiate a generated experiment from an experiment definition.

    Takes generated :term:`Experiment` definitions and writes them to the
    filesystem.

    Attributes:

        template_ipath: Absolute path to the template XML configuration file.

        exp_input_root: Absolute path to experiment directory where generated
                         XML input files for this experiment should be written.

        exp_output_root: Absolute path to root directory for run outputs
                         for this experiment.

        cmdopts: Dictionary containing parsed cmdline options.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 template_ipath: pathlib.Path,
                 exp_input_root: pathlib.Path,
                 exp_output_root: pathlib.Path,
                 exp_num: int) -> None:

        # filename of template file, sans extension and parent directory path
        self.template_stem = template_ipath.resolve().stem

        # where the generated config and command files should be stored
        self.exp_input_root = exp_input_root

        # where experimental outputs should be stored
        self.exp_output_root = exp_output_root

        self.cmdopts = cmdopts
        self.criteria = criteria
        self.exp_num = exp_num
        self.logger = logging.getLogger(__name__)

        # If random seeds where previously generated, use them if configured
        self.seeds_fpath = self.exp_input_root / config.kRandomSeedsLeaf
        self.preserve_seeds = self.cmdopts['preserve_seeds']
        self.random_seeds = None

        if self.preserve_seeds:
            if utils.path_exists(self.seeds_fpath):
                with open(self.seeds_fpath, 'rb') as f:
                    self.random_seeds = pickle.load(f)

            if self.random_seeds is not None:
                if len(self.random_seeds) == self.cmdopts['n_runs']:
                    self.logger.debug("Using existing random seeds for experiment")
                elif len(self.random_seeds) != self.cmdopts['n_runs']:
                    # OK to overwrite the saved random seeds--they changed the
                    # experiment definition.
                    self.logger.warning(("Experiment definition changed: # random "
                                         "seeds (% s) != --n-runs (%s): create new "
                                         "seeds"),
                                        len(self.random_seeds),
                                        self.cmdopts['n_runs'])
                    self.preserve_seeds = False

        if not self.preserve_seeds or self.random_seeds is None:
            self.logger.debug("Generating new random seeds for experiment")
            self.random_seeds = random.sample(range(0, int(time.time())),
                                              self.cmdopts["n_runs"])

        # where the commands file will be stored
        self.commands_fpath = self.exp_input_root / \
            config.kGNUParallel['cmdfile_stem']

    def from_def(self, exp_def: definition.XMLExpDef):
        """Create all experimental runs by writing input files to filesystem.

        The passed :class:`~sierra.core.experiment.definition.XMLExpDef` object
        contains all changes that should be made to all runs in the
        experiment. Additional changes to create a set of unique runs from which
        distributions of system behavior can be meaningfully computed post-hoc
        are added.

        """
        # Clear out commands file if it exists
        configurer = platform.ExpConfigurer(self.cmdopts)
        commands_fpath = self.commands_fpath.with_suffix(
            config.kGNUParallel['cmdfile_ext'])
        if configurer.cmdfile_paradigm() == 'per-exp' and utils.path_exists(commands_fpath):
            commands_fpath.unlink()

        n_robots = utils.get_n_robots(self.criteria.main_config,
                                      self.cmdopts,
                                      self.exp_input_root,
                                      exp_def)
        generator = platform.ExpRunShellCmdsGenerator(self.cmdopts,
                                                      self.criteria,
                                                      n_robots,
                                                      self.exp_num)

        # Create all experimental runs
        for run_num in range(self.cmdopts['n_runs']):
            per_run = copy.deepcopy(exp_def)
            self._create_exp_run(per_run, generator, run_num)

        # Perform experiment level configuration AFTER all runs have been
        # generated in the experiment, in case the configuration depends on the
        # generated launch files.
        platform.ExpConfigurer(self.cmdopts).for_exp(self.exp_input_root)

        # Save seeds
        if not utils.path_exists(self.seeds_fpath) or not self.preserve_seeds:
            if utils.path_exists(self.seeds_fpath):
                os.remove(self.seeds_fpath)
            with open(self.seeds_fpath, 'ab') as f:
                utils.pickle_dump(self.random_seeds, f)

    def _create_exp_run(self,
                        run_exp_def: definition.XMLExpDef,
                        cmds_generator,
                        run_num: int) -> None:
        run_output_dir = "{0}_{1}_output".format(self.template_stem, run_num)

        # If the project defined per-run configuration, apply
        # it. Otherwise, just apply the configuration in the SIERRA core.
        per_run = pm.module_load_tiered(project=self.cmdopts['project'],
                                        path='generators.exp_generators')

        run_output_root = self.exp_output_root / run_output_dir
        stem_path = self._get_launch_file_stempath(run_num)

        per_run.ExpRunDefUniqueGenerator(run_num,
                                         run_output_root,
                                         stem_path,
                                         self.random_seeds[run_num],
                                         self.cmdopts).generate(run_exp_def)

        # Write out the experimental run launch file
        run_exp_def.write(stem_path)

        # Perform any necessary programmatic (i.e., stuff you can do in python
        # and don't need a shell for) per-run configuration.
        configurer = platform.ExpConfigurer(self.cmdopts)
        configurer.for_exp_run(self.exp_input_root, run_output_root)

        ext = config.kGNUParallel['cmdfile_ext']
        if configurer.cmdfile_paradigm() == 'per-exp':
            # Update GNU Parallel commands file with the command for the
            # configured experimental run.
            fpath = f"{self.commands_fpath}{ext}"
            with utils.utf8open(fpath, 'a') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-exp',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'slave')
        elif configurer.cmdfile_paradigm() == 'per-run':
            # Write new GNU Parallel commands file with the commends for the
            # experimental run.
            master_fpath = f"{self.commands_fpath}_run{run_num}_master{ext}"
            slave_fpath = f"{self.commands_fpath}_run{run_num}_slave{ext}"

            self.logger.trace("Updating slave cmdfile %s",   # type: ignore
                              slave_fpath)
            with utils.utf8open(slave_fpath, 'w') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-run',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'slave')

            self.logger.trace("Updating master cmdfile %s",   # type: ignore
                              master_fpath)
            with utils.utf8open(master_fpath, 'w') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-run',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'master')

    def _get_launch_file_stempath(self, run_num: int) -> pathlib.Path:
        """File is named as ``<template input file stem>_run<run_num>``.
        """
        leaf = "{0}_run{1}".format(self.template_stem, run_num)
        return self.exp_input_root / leaf

    def _update_cmds_file(self,
                          cmds_file,
                          cmds_generator: bindings.IExpRunShellCmdsGenerator,
                          paradigm: str,
                          run_num: int,
                          launch_stem_path: pathlib.Path,
                          for_host: str) -> None:
        """Add command to launch a given experimental run to the command file.

        """
        pre_specs = cmds_generator.pre_run_cmds(for_host,
                                                launch_stem_path,
                                                run_num)
        assert all(spec.shell for spec in pre_specs),\
            "All pre-exp commands are run in a shell"
        pre_cmds = [spec.cmd for spec in pre_specs]
        self.logger.trace("Pre-experiment cmds: %s", pre_cmds)   # type: ignore

        exec_specs = cmds_generator.exec_run_cmds(for_host,
                                                  launch_stem_path,
                                                  run_num)
        assert all(spec.shell for spec in exec_specs),\
            "All exec-exp commands are run in a shell"
        exec_cmds = [spec.cmd for spec in exec_specs]
        self.logger.trace("Exec-experiment cmds: %s", exec_cmds)   # type: ignore

        post_specs = cmds_generator.post_run_cmds(for_host)
        assert all(spec.shell for spec in post_specs),\
            "All post-exp commands are run in a shell"
        post_cmds = [spec.cmd for spec in post_specs]
        self.logger.trace("Post-experiment cmds: %s", post_cmds)   # type: ignore

        if len(pre_cmds + exec_cmds + post_cmds) == 0:
            self.logger.debug("Skipping writing %s cmds file: no cmds",
                              for_host)
            return

        # If there is 1 cmdfile per experiment, then the pre- and post-exec cmds
        # need to be prepended and appended to the exec cmds on a per-line
        # basis. If there is 1 cmdfile per experimental run, then its the same
        # thing, BUT we need to break the exec cmds over multiple lines in the
        # cmdfile.
        if paradigm == 'per-exp':
            line = ' '.join(pre_cmds + exec_cmds + post_cmds) + '\n'
            cmds_file.write(line)
        elif paradigm == 'per-run':
            for e in exec_cmds:
                line = ' '.join(pre_cmds + [e] + post_cmds) + '\n'
                cmds_file.write(line)
        else:
            raise ValueError(f"Bad paradigm {paradigm}")


class BatchExpCreator:
    """Instantiate a :term:`Batch Experiment`.

    Calls :class:`~sierra.core.generators.exp_creator.ExpCreator` on each
    experimental definition in the batch

    Attributes:

        batch_config_template: Absolute path to the root template XML
                               configuration file.

        batch_input_root: Root directory for all generated XML input files all
                          experiments should be stored (relative to current dir
                          or absolute). Each experiment will get a directory
                          within this root to store the xml input files for the
                          experimental runs comprising an experiment; directory
                          name determined by the batch criteria used.

        batch_output_root: Root directory for all experiment outputs. Each
                           experiment will get a directory 'exp<n>' in this
                           directory for its outputs.

        criteria: :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  derived object instance created from cmdline definition.

    """

    def __init__(self,
                 criteria: bc.BatchCriteria,
                 cmdopts: types.Cmdopts) -> None:

        self.batch_config_template = pathlib.Path(cmdopts['template_input_file'])
        self.batch_input_root = pathlib.Path(cmdopts['batch_input_root'])
        self.batch_output_root = pathlib.Path(cmdopts['batch_output_root'])
        self.criteria = criteria
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def create(self, generator: BatchExpDefGenerator) -> None:
        utils.dir_create_checked(self.batch_input_root,
                                 self.cmdopts['exp_overwrite'])

        # Scaffold the batch experiment, creating experiment directories and
        # writing template XML input files for each experiment in the batch with
        # changes from the batch criteria added.
        exp_def = definition.XMLExpDef(input_fpath=self.batch_config_template,
                                       write_config=None)

        self.criteria.scaffold_exps(exp_def, self.cmdopts)

        # Pickle experiment definitions in the actual batch experiment
        # directory for later retrieval.
        self.criteria.pickle_exp_defs(self.cmdopts)

        # Run batch experiment generator (must be after scaffolding so the
        # per-experiment template files are in place).
        defs = generator.generate_defs()

        assert len(defs) > 0, "No XML modifications generated?"

        for i, defi in enumerate(defs):
            self.logger.debug(
                "Applying generated scenario+controller changes to exp%s",
                i)
            expi = self.criteria.gen_exp_names(self.cmdopts)[i]
            exp_output_root = self.batch_output_root / expi
            exp_input_root = self.batch_input_root / expi

            ExpCreator(self.cmdopts,
                       self.criteria,
                       self.batch_config_template,
                       exp_input_root,
                       exp_output_root,
                       i).from_def(defi)


__api__ = [
    'ExpCreator',
    'BatchExpCreator',
]
