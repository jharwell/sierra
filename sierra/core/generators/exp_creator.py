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
Experiment creation classes, taking an experiment definition `generated` by
classes in ``exp_generators.py`` and writing the experiment to the filesystem.

"""

# Core packages
import os
import random
import typing as tp
import copy
import logging  # type: tp.Any
import time

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import config, utils, types, platform, xml
import sierra.core.plugin_manager as pm
from sierra.core.generators.exp_generators import BatchExpDefGenerator
from sierra.core.experiment import bindings


class ExpCreator:
    """Instantiate a generated experiment from an experiment definition.

    Takes generated :term:`Experiment` definitions and writes them to the
    filesystem.

    Attributes:

        template_input_file: Path(relative to current dir or absolute) to the
                             template XML configuration file.

        exp_input_root: Absolute path to experiment directory where generated
                         XML input files for this experiment should be written.

        exp_output_root: Absolute path to root directory for run outputs
                         for this experiment (sort of a scratch directory).

        cmdopts: Dictionary containing parsed cmdline options.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 template_input_file: str,
                 exp_input_root: str,
                 exp_output_root: str,
                 exp_num: int) -> None:

        # Will get the main name and extension of the config file (without the
        # full absolute path)
        self.main_input_name, self.main_input_extension = os.path.splitext(
            os.path.basename(os.path.abspath(template_input_file)))

        # where the generated config and command files should be stored
        self.exp_input_root = os.path.abspath(exp_input_root)

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.cmdopts = cmdopts
        self.criteria = criteria
        self.exp_num = exp_num
        self.logger = logging.getLogger(__name__)

        # If random seeds where previously generated, use them if configured
        self.seeds_fpath = os.path.join(self.exp_input_root,
                                        config.kRandomSeedsLeaf)
        self.preserve_seeds = not self.cmdopts['no_preserve_seeds']
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
                self.logger.warn(("Experiment definition changed: # random "
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
        self.commands_fpath = os.path.join(self.exp_input_root,
                                           config.kGNUParallel['cmdfile_stem'])

    def from_def(self, exp_def: xml.XMLLuigi):
        """
        Given a :class:`~sierra.core.xml.XMLLuigi` object containing all changes
        that should be made to all runs in the experiment, create additional
        changes to create a set of unique runs from which distributions of swarm
        behavior can be meaningfully computed post-hoc.

        Writes out all experiment input files to the filesystem.

        """
        # Clear out commands file if it exists
        configurer = platform.ExpConfigurer(self.cmdopts)
        commands_fpath = self.commands_fpath + \
            config.kGNUParallel['cmdfile_ext']
        if configurer.cmdfile_paradigm() == 'per-exp' and utils.path_exists(commands_fpath):
            os.remove(commands_fpath)

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
            self._create_exp_run(per_run, generator, run_num, self.random_seeds)

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
                        run_exp_def: xml.XMLLuigi,
                        cmds_generator: bindings.IExpShellCmdsGenerator,
                        run_num: int,
                        seeds: tp.List[int]) -> None:
        run_output_dir = "{0}_{1}_output".format(self.main_input_name,
                                                 run_num)

        # If the project defined per-run configuration, apply
        # it. Otherwise, just apply the configuration in the SIERRA core.
        per_run = pm.module_load_tiered(project=self.cmdopts['project'],
                                        path='generators.exp_generators')

        run_output_root = os.path.join(self.exp_output_root,
                                       run_output_dir)
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

        if configurer.cmdfile_paradigm() == 'per-exp':
            # Update GNU Parallel commands file with the command for the
            # configured experimental run.
            fpath = f"{self.commands_fpath}{config.kGNUParallel['cmdfile_ext']}"
            with open(fpath, 'a') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-exp',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'slave')
        elif configurer.cmdfile_paradigm() == 'per-run':
            # Write new GNU Parallel commands file with the commends for the
            # experimental run.
            ext = config.kGNUParallel['cmdfile_ext']
            master_fpath = f"{self.commands_fpath}_run{run_num}_master{ext}"
            slave_fpath = f"{self.commands_fpath}_run{run_num}_slave{ext}"

            self.logger.trace("Updating slave cmdfile %s", slave_fpath)
            with open(slave_fpath, 'w') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-run',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'slave')

            self.logger.trace("Updating master cmdfile %s", master_fpath)
            with open(master_fpath, 'w') as cmds_file:
                self._update_cmds_file(cmds_file,
                                       cmds_generator,
                                       'per-run',
                                       run_num,
                                       self._get_launch_file_stempath(run_num),
                                       'master')

    def _get_launch_file_stempath(self, run_num: int) -> str:
        """
        File is named as ``<template input file stem>_run<run_num>`` in the
        experiment generation root. Individual :term:`platforms <Platform>` can
        extend this path/add extensions as needed.
        """
        return os.path.join(self.exp_input_root,
                            "{0}_run{1}".format(self.main_input_name,
                                                run_num))

    def _update_cmds_file(self,
                          cmds_file,
                          cmds_generator: bindings.IExpRunShellCmdsGenerator,
                          paradigm: str,
                          run_num: int,
                          launch_stem_path: str,
                          for_host: str) -> None:
        """
        Adds the command to launch a particular experimental run to the command
        file.
        """
        pre_specs = cmds_generator.pre_run_cmds(for_host,
                                                launch_stem_path,
                                                run_num)
        assert all([spec['shell'] for spec in pre_specs]),\
            "All pre-exp commands are run in a shell"
        pre_cmds = [spec['cmd'] for spec in pre_specs]
        self.logger.trace("Pre-experiment cmds: %s", pre_cmds)

        exec_specs = cmds_generator.exec_run_cmds(for_host,
                                                  launch_stem_path,
                                                  run_num)
        assert all([spec['shell'] for spec in exec_specs]),\
            "All exec-exp commands are run in a shell"
        exec_cmds = [spec['cmd'] for spec in exec_specs]
        self.logger.trace("Exec-experiment cmds: %s", exec_cmds)

        post_specs = cmds_generator.post_run_cmds(for_host)
        assert all([spec['shell'] for spec in post_specs]),\
            "All post-exp commands are run in a shell"
        post_cmds = [spec['cmd'] for spec in post_specs]
        self.logger.trace("Post-experiment cmds: %s", post_cmds)

        if len(pre_cmds + exec_cmds + post_cmds) == 0:
            self.logger.debug(f"Skipping writing {for_host} cmds file: no cmds")
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
            assert False, f"Bad paradigm {paradigm}"


class BatchExpCreator:
    """Instantiate a :term:`Batch Experiment`.

    Calls :class:`~sierra.core.generators.exp_creator.ExpCreator` on each
    experimental definition in the batch

    Attributes:

        batch_config_template: Path (relative to current dir or absolute) to the
                               root template XML configuration file.

        batch_input_root: Root directory for all generated XML input files all
                          experiments should be stored (relative to current dir
                          or absolute). Each experiment will get a directory
                          within this root to store the xml input files for the
                          experimental runs comprising an experiment; directory
                          name determined by the batch criteria used.

        batch_output_root: Root directory for all experiment outputs (relative
                           to current dir or absolute). Each experiment will get
                           a directory 'exp<n>' in this directory for its
                           outputs.

        criteria: :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  derived object instance created from cmdline definition.

    """

    def __init__(self,
                 criteria: bc.BatchCriteria,
                 cmdopts: types.Cmdopts) -> None:

        self.batch_config_template = cmdopts['template_input_file']
        self.batch_input_root = cmdopts['batch_input_root']
        self.batch_output_root = cmdopts['batch_output_root']
        self.criteria = criteria
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def create(self, generator: BatchExpDefGenerator) -> None:
        utils.dir_create_checked(self.batch_input_root,
                                 self.cmdopts['exp_overwrite'])

        # Scaffold the batch experiment, creating experiment directories and
        # writing template XML input files for each experiment in the batch with
        # changes from the batch criteria added.
        exp_def = xml.XMLLuigi(input_fpath=self.batch_config_template,
                               write_config=xml.XMLWriterConfig({'.': ''}))

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
            exp_output_root = os.path.join(self.batch_output_root,
                                           self.criteria.gen_exp_dirnames(self.cmdopts)[i])
            exp_input_root = os.path.join(self.batch_input_root,
                                          self.criteria.gen_exp_dirnames(self.cmdopts)[i])

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
