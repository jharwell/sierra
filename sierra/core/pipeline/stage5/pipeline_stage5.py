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

"""Stage 5 of the experimental pipeline: comparing deliverables.

"""

# Core packages
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage5 import intra_scenario_comparator as intrasc
from sierra.core.pipeline.stage5 import inter_scenario_comparator as intersc
import sierra.core.root_dirpath_generator as rdg
from sierra.core import types, utils, config


class PipelineStage5:
    """Compare controllers within or across scenarios.

    This can be either:

    #. Compare a set of controllers within the same scenario using performance
       measures specified in YAML configuration.

    #. Compare a single controller across a set ofscenarios using performance
       measures specified in YAML configuration.

    This stage is idempotent.

    Attributes:

        cmdopts: Dictionary of parsed cmdline parameters.

        controllers: List of controllers to compare.

        main_config: Dictionary of parsed main YAML configuration.

        stage5_config: Dictionary of parsed stage5 YAML configuration.

        output_roots: Dictionary containing output directories for intra- and
                      inter-scenario graph generation.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config

        path = pathlib.Path(self.cmdopts['project_config_root'],
                            config.kYAML.stage5)

        with utils.utf8open(path) as f:
            self.stage5_config = yaml.load(f, yaml.FullLoader)

        self.logger = logging.getLogger(__name__)

        if self.cmdopts['controllers_list'] is not None:
            self.controllers = self.cmdopts['controllers_list'].split(',')
            self.output_roots = {
                # We add the controller list to the directory path for the .csv
                # and graph directories so that multiple runs of stage5 with
                # different controller sets do not overwrite each other
                # (i.e. make stage5 more idempotent).
                'graphs': pathlib.Path(self.cmdopts['sierra_root'],
                                       self.cmdopts['project'],
                                       '+'.join(self.controllers) + "-cc-graphs"),
                'csvs': pathlib.Path(self.cmdopts['sierra_root'],
                                     self.cmdopts['project'],
                                     '+'.join(self.controllers) + "-cc-csvs"),
            }

        else:
            self.controllers = []

        if self.cmdopts['scenarios_list'] is not None:
            self.scenarios = self.cmdopts['scenarios_list'].split(',')
            self.output_roots = {
                # We add the scenario list to the directory path for the .csv
                # and graph directories so that multiple runs of stage5 with
                # different scenario sets do not overwrite each other (i.e. make
                # stage5 idempotent).
                'graphs': pathlib.Path(self.cmdopts['sierra_root'],
                                       self.cmdopts['project'],
                                       '+'.join(self.scenarios) + "-sc-graphs"),
                'csvs': pathlib.Path(self.cmdopts['sierra_root'],
                                     self.cmdopts['project'],
                                     '+'.join(self.scenarios) + "-sc-csvs"),
                'models': pathlib.Path(self.cmdopts['sierra_root'],
                                       self.cmdopts['project'],
                                       '+'.join(self.scenarios) + "-sc-models"),
            }

        else:
            self.scenarios = []

        self.project_root = pathlib.Path(self.cmdopts['sierra_root'],
                                         self.cmdopts['project'])

    def run(self, cli_args) -> None:
        """Run stage 5 of the experimental pipeline.

        If ``--controller-comparison`` was passed:

        #. :class:`~sierra.core.pipeline.stage5.intra_scenario_comparator.UnivarIntraScenarioComparator`
            or
            :class:`~sierra.core.pipeline.stage5.intra_scenario_comparator.BivarIntraScenarioComparator`
            as appropriate, depending on which type of
            :class:`~sierra.core.variables.batch_criteria.BatchCriteria` was
            selected on the cmdline.

        If ``--scenario-comparison`` was passed:

        #. :class:`~sierra.core.pipeline.stage5.inter_scenario_comparator.UnivarInterScenarioComparator`
            (only valid for univariate batch criteria currently).

        """
        # Create directories for .csv files and graphs
        for v in self.output_roots.values():
            utils.dir_create_checked(v, True)

        if self.cmdopts['controller_comparison']:
            self._run_cc(cli_args)
        elif self.cmdopts['scenario_comparison']:
            self._run_sc(cli_args)

    def _run_cc(self, cli_args):
        # Use nice controller names on graph legends if configured
        if self.cmdopts['controllers_legend'] is not None:
            legend = self.cmdopts['controllers_legend'].split(',')
        else:
            legend = self.controllers

        self._verify_comparability(self.controllers, cli_args)

        self.logger.info(
            "Inter-batch controller comparison of %s...", self.controllers)

        if cli_args.bc_univar:
            univar = intrasc.UnivarIntraScenarioComparator(self.controllers,
                                                           self.output_roots['csvs'],
                                                           self.output_roots['graphs'],
                                                           self.cmdopts,
                                                           cli_args,
                                                           self.main_config)
            univar(graphs=self.stage5_config['intra_scenario']['graphs'],
                   legend=legend,
                   comp_type=self.cmdopts['comparison_type'])
        else:
            bivar = intrasc.BivarIntraScenarioComparator(self.controllers,
                                                         self.output_roots['csvs'],
                                                         self.output_roots['graphs'],
                                                         self.cmdopts,
                                                         cli_args,
                                                         self.main_config)
            bivar(graphs=self.stage5_config['intra_scenario']['graphs'],
                  legend=legend,
                  comp_type=self.cmdopts['comparison_type'])

        self.logger.info("Inter-batch controller comparison complete")

    def _run_sc(self, cli_args):
        # Use nice scenario names on graph legends if configured
        if self.cmdopts['scenarios_legend'] is not None:
            legend = self.cmdopts['scenarios_legend'].split(',')
        else:
            legend = self.scenarios

        self.logger.info("Inter-batch  comparison of %s across %s...",
                         self.cmdopts['controller'],
                         self.scenarios)

        assert cli_args.bc_univar,\
            "inter-scenario controller comparison only valid for univariate batch criteria"

        roots = {k: self.output_roots[k] for k in ('csvs', 'graphs', 'models')}
        comparator = intersc.UnivarInterScenarioComparator(self.cmdopts['controller'],
                                                           self.scenarios,
                                                           roots,
                                                           self.cmdopts,
                                                           cli_args,
                                                           self.main_config)

        comparator(graphs=self.stage5_config['inter_scenario']['graphs'],
                   legend=legend)

        self.logger.info("Inter-batch  comparison of %s across %s complete",
                         self.cmdopts['controller'],
                         self.scenarios)

    def _verify_comparability(self, controllers, cli_args):
        """Check if the specified controllers can be compared.

        Comparable controllers have all been run on the same set of batch
        experiments. If they have not, it is not `necessarily` an error, but
        probably should be looked at, so it is only a warning, not fatal.

        """
        for t1 in controllers:
            for item in (self.project_root / t1).iterdir():
                template_stem, scenario, _ = rdg.parse_batch_leaf(item.name)
                batch_leaf = rdg.gen_batch_leaf(cli_args.batch_criteria,
                                                template_stem,
                                                scenario)

                for t2 in controllers:
                    opts1 = rdg.regen_from_exp(sierra_rpath=self.cmdopts['sierra_root'],
                                               project=self.cmdopts['project'],
                                               batch_leaf=batch_leaf,
                                               controller=t1)
                    opts2 = rdg.regen_from_exp(sierra_rpath=self.cmdopts['sierra_root'],
                                               project=self.cmdopts['project'],
                                               batch_leaf=batch_leaf,
                                               controller=t2)
                    collate_root1 = opts1['batch_stat_collate_root']
                    collate_root2 = opts2['batch_stat_collate_root']

                    if scenario in str(collate_root1) and scenario not in str(collate_root2):
                        self.logger.warning("%s does not exist in %s",
                                            scenario,
                                            collate_root2)
                    if scenario in str(collate_root2) and scenario not in str(collate_root1):
                        self.logger.warning("%s does not exist in %s",
                                            scenario,
                                            collate_root1)


__api__ = [
    'PipelineStage5'
]
