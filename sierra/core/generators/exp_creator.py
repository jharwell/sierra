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
import pickle
import time

# 3rd party packages

# Project packages
from sierra.core.xml import XMLLuigi, XMLWriterConfig
from sierra.core.variables import batch_criteria as bc
import sierra.core.config as config
import sierra.core.utils
import sierra.core.plugin_manager as pm
from sierra.core import types, platform
from sierra.core.generators.exp_generators import BatchExpDefGenerator
from sierra.core.experiment import bindings


class ExpCreator:
    """
    Instantiate an experiment within a batch from an experiment definition
    generated by
    :class:`~sierra.core.generators.exp_generators.BatchExpDefGenerator` by
    writing out run input files and setting up the necessary directory
    structure.

    Attributes: template_input_file: Path(relative to current dir or absolute)
        to the template XML configuration file.

        exp_input_root: Absolute path to experiment directory where generated
                         XML input files for this experiment should be written.

        exp_output_root: Absolute path to root directory for run outputs
                         for this experiment (sort of a scratch directory).

        cmdopts: Dictionary containing parsed cmdline options.

    """

    def __init__(self,
                 template_input_file: str,
                 exp_input_root: str,
                 exp_output_root: str,
                 exp_num: int,
                 cmdopts: types.Cmdopts,
                 main_config: types.YAMLDict) -> None:

        # Will get the main name and extension of the config file (without the
        # full absolute path)
        self.main_input_name, self.main_input_extension = os.path.splitext(
            os.path.basename(os.path.abspath(template_input_file)))

        # where the generated config and command files should be stored
        self.exp_input_root = os.path.abspath(exp_input_root)

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.exp_num = exp_num
        self.logger = logging.getLogger(__name__)

        # If random seeds where previously generated, use them if configured
        self.seeds_fpath = os.path.join(self.exp_input_root,
                                        config.kRandomSeedsLeaf)
        if os.path.exists(self.seeds_fpath) and not self.cmdopts['no_preserve_seeds']:
            with open(self.seeds_fpath, 'rb') as f:
                self.random_seeds = pickle.load(f)
            self.logger.debug("Using existing random seeds for experiment")
        else:
            self.logger.debug("Generating new random seeds for experiment")
            self.random_seeds = random.sample(range(0, int(time.time())),
                                              self.cmdopts["n_runs"])

        # where the commands file will be stored
        self.commands_fpath = os.path.join(self.exp_input_root,
                                           config.kGNUParallel['cmdfile'])

    def from_def(self, exp_def: XMLLuigi):
        """
        Given a :class:`~sierra.core.xml.XMLLuigi` object containing all changes
        that should be made to all runs in the experiment, create additional
        changes to create a set of unique runs from which distributions of swarm
        behavior can be meaningfully computed post-hoc.

        Writes out all experiment input files to the filesystem.

        """
        # Clear out commands file if it exists
        if sierra.core.utils.path_exists(self.commands_fpath):
            os.remove(self.commands_fpath)

        # Create all experimental runs
        module = pm.SIERRAPluginManager().get_plugin_module(
            self.cmdopts['platform'])
        n_robots = module.population_size_from_def(exp_def,
                                                   self.main_config,
                                                   self.cmdopts)
        generator = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                    n_robots,
                                                    self.exp_num)

        for run_num in range(self.cmdopts['n_runs']):
            per_run = copy.deepcopy(exp_def)
            self._create_exp_run(per_run, generator, run_num, self.random_seeds)

        # Save seeds
        if not os.path.exists(self.seeds_fpath) or self.cmdopts['no_preserve_seeds']:
            with open(self.seeds_fpath, 'ab') as f:
                pickle.dump(self.random_seeds, f)

    def _create_exp_run(self,
                        run_exp_def: XMLLuigi,
                        cmds_generator: bindings.IExpShellCmdsGenerator,
                        run_num: int,
                        seeds: tp.List[int]) -> None:
        run_output_dir = "{0}_{1}_output".format(self.main_input_name,
                                                 run_num)

        # If the project defined per-run configuration, apply
        # it. Otherwise, just apply the configuration in the SIERRA core.
        per_run = pm.module_load_tiered(project=self.cmdopts['project'],
                                        path='generators.exp_generators')

        run_output_path = os.path.join(self.exp_output_root,
                                       run_output_dir)
        stem_path = self._get_launch_file_stempath(run_num)
        per_run.ExpRunDefUniqueGenerator(run_num,
                                         run_output_path,
                                         stem_path,
                                         self.random_seeds[run_num],
                                         self.cmdopts).generate(run_exp_def)

        # Write out the experimental run launch file
        run_exp_def.write(stem_path)

        # Perform any necessary per-run configuration.
        run_output_dir = os.path.join(self.exp_output_root,
                                      run_output_dir)
        platform.ExpRunConfigurer(self.cmdopts)(run_output_dir)

        # Update GNU Parallel commands file with the command for the configured
        # experimental run.
        with open(self.commands_fpath, 'a') as cmds_file:
            self._update_cmds_file(cmds_file,
                                   cmds_generator,
                                   run_num,
                                   self._get_launch_file_stempath(run_num))

    def _get_launch_file_stempath(self, run_num: int) -> str:
        """
        File is named as ``<template input file stem>_<run_num>`` in the
        experiment generation root. Individual :term:`platforms <Platform>` can
        extend this path/add extensions as needed.
        """
        return os.path.join(self.exp_input_root,
                            "{0}_{1}".format(self.main_input_name,
                                             run_num))

    def _update_cmds_file(self,
                          cmds_file,
                          cmds_generator: bindings.IExpRunShellCmdsGenerator,
                          run_num: int,
                          launch_stem_path: str) -> None:
        """
        Adds the command to launch a particular experimental run to the command
        file.
        """

        pre_specs = cmds_generator.pre_run_cmds(launch_stem_path, run_num)
        assert all([spec['shell'] for spec in pre_specs]),\
            "All pre-exp commands are run in a shell"
        pre_cmds = [spec['cmd'] for spec in pre_specs]

        exec_specs = cmds_generator.exec_run_cmds(launch_stem_path, run_num)
        assert all([spec['shell'] for spec in exec_specs]),\
            "All exec-exp commands are run in a shell"
        exec_cmds = [spec['cmd'] for spec in exec_specs]

        post_specs = cmds_generator.post_run_cmds()
        assert all([spec['shell'] for spec in post_specs]),\
            "All post-exp commands are run in a shell"
        post_cmds = [spec['cmd'] for spec in post_specs]

        cmds_file.write(' '.join(pre_cmds + exec_cmds + post_cmds) + '\n')


class BatchExpCreator:
    """
    Instantiate a batch experiment from a list of experiment definitions, as
    generated by
    :class:`~sierra.core.generators.exp_generators.BatchExpDefGenerator`, by
    invoking :class:`~sierra.core.generators.exp_creator.ExpCreator` on each
    experimental definition.

    Attributes:
        batch_config_template: Path (relative to current dir or
        absolute) to the root template XML configuration file.

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
                 batch_config_template: str,
                 batch_input_root: str,
                 batch_output_root: str,
                 criteria: bc.BatchCriteria,
                 cmdopts: types.Cmdopts) -> None:

        self.batch_config_template = batch_config_template
        self.batch_config_leaf, _ = os.path.splitext(
            os.path.basename(self.batch_config_template))

        self.batch_input_root = batch_input_root
        self.batch_output_root = batch_output_root
        self.criteria = criteria
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def create(self, generator: BatchExpDefGenerator) -> None:
        sierra.core.utils.dir_create_checked(self.batch_input_root,
                                             self.cmdopts['exp_overwrite'])

        # Scaffold the batch experiment, creating experiment directories and
        # writing template XML input files for each experiment in the batch with
        # changes from the batch criteria added.
        exp_def = XMLLuigi(input_fpath=self.batch_config_template,
                           write_config=XMLWriterConfig({'.': ''}))

        self.criteria.scaffold_exps(exp_def,
                                    self.batch_config_leaf,
                                    self.cmdopts)

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

            ExpCreator(self.batch_config_template,
                       exp_input_root,
                       exp_output_root,
                       i,
                       self.cmdopts,
                       self.criteria.main_config).from_def(defi)


__api__ = [
    'ExpCreator',
    'BatchExpCreator',
]
