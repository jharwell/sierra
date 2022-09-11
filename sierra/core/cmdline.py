# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
#
"""Core command line parsing and validation classes."""

# Core packages
import argparse
import sys
import typing as tp

# 3rd party packages

# Project packages
import sierra.version
from sierra.core import utils

kVersionMsg = ("reSearch pIpEline for Reproducibility, Reusability and "
               f"Automation (SIERRA) v{sierra.version.__version__}.\n"
               "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>\n"
               "This is free software: you are free to change and redistribute it.\n"
               "SIERRA comes with no warranty.\n\n"

               "See the documentation at "
               "https://sierra.readthedocs.io/en/master/,\n"
               "or 'man sierra' for details.\n")


class ArgumentParser(argparse.ArgumentParser):
    """SIERRA's argument parser overriding default argparse behavior.

    Delivers a custom help message without listing options, as the options which
    SIERRA accepts differs dramatically depending on loaded plugins.

    """

    kHelpMsg = ("Usage:\n\nsierra-cli [-v | --version] [OPTION]...\n\n"
                "What command line options SIERRA accepts depends on the loaded\n"
                "--project, --platform, --exec-env, and project-specific options.\n"
                "'man sierra-cli' will give you the full set of options that\n"
                "comes with SIERRA.\n\n")

    def error(self, message):
        self.print_usage(sys.stderr)
        # self.print_help(sys.stderr)
        self.exit(2, '{0}: error: {1}\n'.format(self.prog, message))

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout

        file.write(self.kHelpMsg + "\n")


class BaseCmdline:
    """
    The base cmdline definition class for SIERRA for reusability.

    """

    @staticmethod
    def stage_usage_doc(stages: tp.List[int],
                        omitted: str = "If omitted: N/A.") -> str:
        lst = ",".join(map(str, stages))
        header = "\n.. TIP:: Used by stage {" + \
            lst + "}; can be omitted otherwise. " + omitted + "\n"
        return header

    @staticmethod
    def bc_applicable_doc(criteria: tp.List[str]) -> str:
        lst = "".join(map(lambda bc: "   - " + bc + "\n", criteria))
        return "\n.. TIP:: Applicable batch criteria:\n\n" + lst + "\n"

    @staticmethod
    def graphs_applicable_doc(graphs: tp.List[str]) -> str:
        lst = "".join(map(lambda graph: "   - " +
                          utils.sphinx_ref(graph) + "\n",
                          graphs))
        return "\n.. TIP:: Applicable graphs:\n\n" + lst + "\n"


class BootstrapCmdline(BaseCmdline):
    """
    Defines the arguments that are used to bootstrap SIERRA/load plugins.
    """

    def __init__(self) -> None:
        self.parser = ArgumentParser(add_help=True,
                                     allow_abbrev=False)

        bootstrap = self.parser.add_argument_group('Bootstrap options',
                                                   'Bare-bones options for bootstrapping SIERRA')

        bootstrap.add_argument("--project",
                               help="""

                                 Specify which :term:`Project` to load.

                               """ + self.stage_usage_doc([1, 2, 3, 4, 5]))

        bootstrap.add_argument("--version", "-v",
                               help="""

                               Display SIERRA version information on stdout and
                               then exit.

                               """,
                               action='store_true')

        bootstrap.add_argument("--log-level",
                               choices=["ERROR",
                                        "INFO",
                                        "WARNING",
                                        "DEBUG",
                                        "TRACE"],
                               help="""

                                 The level of logging to use when running
                                 SIERRA.

                                 """ + self.stage_usage_doc([1, 2, 3, 4, 5]),
                               default="INFO")

        bootstrap.add_argument("--platform",
                               help="""
                               This argument defines the :term:`Platform` you
                               want to run experiments on.

                               The value of this argument determines the
                               execution environment for experiments; different
                               platforms (e.g., simulator, real robots) will
                               have different configuration options.

                               Valid values can be any folder name inside a
                               folder on the :envvar:`SIERRA_PLUGIN_PATH` (with
                               ``/`` replaced with ``.`` as you would expect for
                               using path names to address python packages). The
                               platforms which come with SIERRA are:

                               - ``platform.argos`` - This directs SIERRA to run
                                 experiments using the :term:`ARGoS`
                                 simulator. Selecting this platform assumes your
                                 code has been developed and configured for
                                 ARGoS.

                               - ``platform.ros1gazebo`` - This directs SIERRA to
                                 run experiments using the :term:`Gazebo`
                                 simulator and :term:`ROS1`. Selecting this
                                 platform assumes your code has been developed
                                 and configured for Gazebo and ROS1.

                               """,
                               default='platform.argos')

        bootstrap.add_argument("--skip-pkg-checks",
                               help="""

                               Skip the usual startup package checks. Only do
                               this if you are SURE you will never use the
                               SIERRA functionality which requires packages you
                               don't have installed/can't install.

                               """,
                               action='store_true')

        bootstrap.add_argument("--exec-env",
                               help="""
                               This argument defines `how` experiments are going
                               to be run, using the ``--platform`` you have
                               selected.

                               Valid values can be any folder name inside a
                               folder on the :envvar:`SIERRA_PLUGIN_PATH` (with
                               ``/`` replaced with ``.`` as you would expect for
                               using path names to address python packages). The
                               execution environments which come with SIERRA
                               are:

                               - ``hpc.local`` - This directs SIERRA to run
                                 experiments on the local machine. See
                                 :ref:`ln-sierra-hpc-plugins-local` for a detailed
                                 description.

                               - ``hpc.pbs`` - The directs SIERRA to run
                                 experiments spread across multiple allocated
                                 nodes in an HPC computing environment managed
                                 by TORQUE-PBS. See :ref:`ln-sierra-hpc-plugins-pbs`
                                 for a detailed description.

                               - ``hpc.slurm`` - The directs SIERRA to run
                                 experiments spread across multiple allocated
                                 nodes in an HPC computing environment managed
                                 by SLURM. See
                                 :ref:`ln-sierra-hpc-plugins-slurm` for a
                                 detailed description.

                               - ``hpc.adhoc`` - This will direct SIERRA to run
                                 experiments on an ad-hoc network of
                                 computers. See
                                 :ref:`ln-sierra-hpc-plugins-adhoc` for a
                                 detailed description.

                               - ``robot.turtlebot3`` - This will direct SIERRA
                                 to run experiments on real Turtlebots.

                               Not all platforms support all execution
                               environments.
                               """ + self.stage_usage_doc([1, 2]),
                               default='hpc.local')


class CoreCmdline(BaseCmdline):
    """Defines the core command line arguments for SIERRA using :class:`argparse`.

    """

    def __init__(self,
                 parents: tp.Optional[tp.List[ArgumentParser]],
                 stages: tp.List[int]) -> None:
        self.scaffold_cli(parents)
        self.init_cli(stages)

    def init_cli(self, stages: tp.List[int]) -> None:
        """Define cmdline arguments for stages 1-5."""
        if -1 in stages:
            self.init_multistage()

        if 1 in stages:
            self.init_stage1()

        if 2 in stages:
            self.init_stage2()

        if 3 in stages:
            self.init_stage3()

        if 4 in stages:
            self.init_stage4()

        if 5 in stages:
            self.init_stage5()

    def scaffold_cli(self,
                     parents: tp.Optional[tp.List[ArgumentParser]]) -> None:
        """
        Scaffold CLI by defining the parser and common argument groups.
        """
        if parents is not None:
            self.parser = ArgumentParser(parents=parents,
                                         add_help=False,
                                         allow_abbrev=False)
        else:
            self.parser = ArgumentParser(add_help=False,
                                         allow_abbrev=False)

        self.multistage = self.parser.add_argument_group('Multi-stage options',
                                                         'Options which are used in multiple pipeline stages')
        self.stage1 = self.parser.add_argument_group(
            'Stage1: General options for generating experiments')
        self.stage2 = self.parser.add_argument_group(
            'Stage2: General options for running experiments')
        self.stage3 = self.parser.add_argument_group(
            'Stage3: General options for eprocessing experiment results')
        self.stage4 = self.parser.add_argument_group(
            'Stage4: General options for generating graphs')
        self.stage5 = self.parser.add_argument_group(
            'Stage5: General options for controller comparison')

    def init_multistage(self) -> None:
        """
        Define cmdline arguments which are used in multiple pipeline stages.
        """
        self.multistage.add_argument("--template-input-file",
                                     metavar="filepath",
                                     help="""

                                     The template ``.xml`` input file for the
                                     batch experiment. Beyond the requirements
                                     for the specific ``--platform``, the
                                     content of the file can be any valid XML,
                                     with the exception of the SIERRA
                                     requirements detailed in
                                     :ref:`ln-sierra-tutorials-project-template-input-file`.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

        self.multistage.add_argument("--exp-overwrite",
                                     help="""

                                     When SIERRA calculates the batch experiment
                                     root (or any child path in the batch
                                     experiment root) during stage {1, 2}, if
                                     the calculated path already exists it is
                                     treated as a fatal error and no
                                     modifications to the filesystem are
                                     performed. This flag overwrides the default
                                     behavior. Provided to avoid accidentally
                                     overwrite input/output files for an
                                     experiment, forcing the user to be explicit
                                     with potentially dangerous actions.

                                     """ + self.stage_usage_doc([1, 2]),
                                     action='store_true')

        self.multistage.add_argument("--sierra-root",
                                     metavar="dirpath",
                                     help="""

                                     Root directory for all SIERRA generated and
                                     created files.

                                     Subdirectories for controllers, scenarios,
                                     experiment/experimental run inputs/outputs
                                     will be created in this directory as
                                     needed. Can persist between invocations of
                                     SIERRA.

                                 """ + self.stage_usage_doc([1, 2, 3, 4, 5]),
                                     default="<home directory>/exp")

        self.multistage.add_argument("--batch-criteria",
                                     metavar="[<category>.<definition>,...]",
                                     help="""

                                     Definition of criteria(s) to use to define
                                     the experiment.

                                     Specified as a list of 0 or 1 space
                                     separated strings, each with the following
                                     general structure:

                                     ``<category>.<definition>``

                                     ``<category>`` must be a filename from the
                                     ``core/variables/`` or from a ``--project``
                                     ``<project>/variables/`` directory, and
                                     ``<definition>`` must be a parsable namne
                                     (according to the requirements of the
                                     criteria defined by the parser for
                                     ``<category>``).

                                 """ + self.stage_usage_doc([1, 2, 3, 4, 5]),
                                     nargs='+',
                                     default=[])

        self.multistage.add_argument("--pipeline",
                                     help="""
                                     Define which stages of the experimental
                                     pipeline to run:

                                     - Stage1 - Generate the experiment
                                       definition from the template input file,
                                       batch criteria, and other command line
                                       options. Part of default pipeline.

                                     - Stage2 - Run a previously generated
                                       experiment. Part of default pipeline.

                                     - Stage3 - Post-process experimental
                                       results after running the batch
                                       experiment; some parts of this can be
                                       done in parallel. Part of default
                                       pipeline.

                                     - Stage4 - Perform deliverable generation
                                       after processing results for a batch
                                       experiment, which can include shiny
                                       graphs and videos. Part of default
                                       pipeline.

                                     - Stage5 - Perform graph generation for
                                       comparing controllers AFTER graph
                                       generation for batch experiments has been
                                       run. Not part of default pipeline.

                                     """,
                                     type=int,
                                     nargs='*',
                                     default=[1, 2, 3, 4]
                                     )
        self.multistage.add_argument("--exp-range",
                                     help="""

                                    Set the experiment numbers from the batch to
                                    run, average, generate intra-experiment
                                    graphs from, or generate inter-experiment
                                    graphs from (0 based). Specified in the form
                                    ``min_exp_num:max_exp_num`` (closed
                                    interval/inclusive). If omitted, runs,
                                    averages, and generates intra-experiment and
                                    inter-experiment performance measure graphs
                                    for all experiments in the batch (default
                                    behavior).

                                    This is useful to re-run part of a batch
                                    experiment in HPC environments if SIERRA
                                    gets killed before it finishes running all
                                    experiments in the batch, or to redo a
                                    single experiment with real robots which
                                    failed for some reason.

                                 """ + self.stage_usage_doc([2, 3, 4]))

        self.multistage.add_argument("--platform-vc",
                                     help="""

                                    For applicable ``--platforms``, enable
                                    visual capturing of run-time data during
                                    stage 2. This data can be frames (i.e., .png
                                    files), or rendering videos, depending on
                                    the platform. If the captured data was
                                    frames, then SIERRA can render the captured
                                    frames into videos during stage 4. If the
                                    selected ``--platform`` does not support
                                    visual capture, then this option has no
                                    effect. See
                                    :ref:`ln-sierra-usage-rendering-platform`
                                    for full details.

                                    """ + self.stage_usage_doc([1, 4]),
                                     action='store_true')

        self.multistage.add_argument("--processing-serial",
                                     help="""

                                    If TRUE, then results processing/graph
                                    generation will be performed serially,
                                    rather than using parallellism where
                                    possible.

                                 """ + self.stage_usage_doc([3, 4]),
                                     action='store_true')

        self.multistage.add_argument("--n-runs",
                                     type=int,
                                     help="""

                                    The # of experimental runs that will be
                                    executed and their results processed to form
                                    the result of a single experiment within a
                                    batch.

                                    If ``--platform`` is a simulator and
                                    ``--exec-env`` is something other than
                                    ``hpc.local`` then this may be be used to
                                    determine the concurrency of experimental
                                    runs.

                                     """ + self.stage_usage_doc([1, 2]))

        self.multistage.add_argument("--skip-collate",
                                     help="""

                                    Specify that no collation of data across
                                    experiments within a batch (stage 4) or
                                    across runs within an experiment (stage 3)
                                    should be performed. Useful if collation
                                    takes a long time and multiple types of
                                    stage 4 outputs are desired. Collation is
                                    generally idempotent unless you change the
                                    stage3 options (YMMV).

                                     """ + self.stage_usage_doc([3, 4]),
                                     action='store_true')
        # Plotting options
        self.multistage.add_argument("--plot-log-xscale",
                                     help="""

                           Place the set of X values used to generate intra- and
                           inter-experiment graphs into the logarithmic
                           space. Mainly useful when the batch criteria involves
                           large system sizes, so that the plots are more
                           readable.

                           """ +

                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`']) +
                                     self.stage_usage_doc([4, 5]),
                                     action='store_true')

        self.multistage.add_argument("--plot-enumerated-xscale",
                                     help="""

                                     Instead of using the values generated by a
                                     given batch criteria for the X values, use
                                     an enumerated list[0, ..., len(X value) -
                                     1]. Mainly useful when the batch criteria
                                     involves large system sizes, so that the
                                     plots are more readable.

                                     """ +

                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`']) +
                                     self.stage_usage_doc([4, 5]),
                                     action='store_true')

        self.multistage.add_argument("--plot-log-yscale",
                                     help="""

                                     Place the set of Y values used to generate
                                     intra - and inter-experiment graphs into
                                     the logarithmic space. Mainly useful when
                                     the batch criteria involves large system
                                     sizes, so that the plots are more readable.

                                     """ +

                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`',
                                                                 ':class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`']) +
                                     self.stage_usage_doc([4, 5]),
                                     action='store_true')

        self.multistage.add_argument("--plot-regression-lines",
                                     help="""

                                     For all 2D generated scatterplots, plot a
                                     linear regression line and the equation of
                                     the line to the legend. """ +

                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`']) +
                                     self.stage_usage_doc([4, 5]))

        self.multistage.add_argument("--plot-primary-axis",
                                     type=int,
                                     help="""


                                     This option allows you to override the
                                     primary axis, which is normally is computed
                                     based on the batch criteria.

                                     For example, in a bivariate batch criteria
                                     composed of

                                    - :ref:`ln-sierra-platform-argos-bc-population-size`
                                      on the X axis (rows)

                                    - Another batch criteria which does not
                                      affect system size (columns)

                                    Metrics will be calculated by `computing`
                                    across .csv rows and `projecting` down the
                                    columns by default, since system size will
                                    only vary within a row. Passing a value of 1
                                    to this option will override this
                                    calculation, which can be useful in
                                    bivariate batch criteria in which you are
                                    interested in the effect of the OTHER
                                    non-size criteria on various performance
                                    measures.

                                    0=criteria of interest varies across `rows`.

                                    1=criteria of interest varies across
                                    `columns`.

                                    This option only affects generating graphs
                                    from bivariate batch criteria.

                                    """
                                     +
                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.heatmap.Heatmap`',
                                                                 ':class:`~sierra.core.graphs.staced_line_graph.StackedLineGraph`']) +
                                     self.stage_usage_doc([4, 5]),
                                     default=None)

        self.multistage.add_argument("--plot-large-text",
                                     help="""

                                    This option specifies that the title, X/Y
                                    axis labels/tick labels should be larger
                                    than the SIERRA default. This is useful when
                                    generating graphs suitable for two column
                                    paper format where the default text size for
                                    rendered graphs will be too small to see
                                    easily. The SIERRA defaults are generally
                                    fine for the one column/journal paper
                                    format.

                                     """ + self.stage_usage_doc([4, 5]),
                                     action='store_true')

        self.multistage.add_argument("--plot-transpose-graphs",
                                     help="""

                                    Transpose the X, Y axes in generated
                                    graphs. Useful as a general way to tweak
                                    graphs for best use of space within a paper.

                                    .. versionchanged:: 1.2.20

                                       Renamed from ``--transpose-graphs`` to
                                       make its relation to other plotting
                                       options clearer.

                                 """ +
                                     self.graphs_applicable_doc([':class:`~sierra.core.graphs.heatmap.Heatmap`']) +
                                     self.stage_usage_doc([4, 5]),
                                     action='store_true')

    def init_stage1(self) -> None:
        """
        Define cmdline arguments for stage 1.
        """
        self.stage1.add_argument("--preserve-seeds",
                                 help="""

                                 Preserve previously generated random seeds for
                                 experiments (the default). Useful for
                                 regenerating experiments when you change
                                 parameters/python code that don't affects
                                 experimental outputs (e.g.,
                                 paths). Preserving/overwriting random seeds is
                                 not affected by ``--exp-overwrite``.

                                 """,
                                 default=True)

        self.stage1.add_argument("--no-preserve-seeds",
                                 help="""

                                 Opposite of ``--preserve-seeds``.

                                 """,
                                 dest='preserve_seeds',
                                 action='store_false')

    def init_stage2(self) -> None:
        """
        Define cmdline arguments for stage 2.
        """
        self.stage2.add_argument("--nodefile",
                                 help="""

                                 Specify a list of compute nodes which SIERpRA
                                 will use to run jobs. For simulator
                                 :term:`Platforms <Platform>`, these are HPC
                                 resource nodes. For real robot platforms, these
                                 are robot hostnames/IP addresses. This
                                 information can also be supplied via the
                                 :envvar:`SIERRA_NODEFILE` environment
                                 variable; this argument takes priority if both
                                 are supplied.

                                 """)

    def init_stage3(self) -> None:
        """
        Define cmdline arguments for stage 3.
        """

        self.stage3.add_argument('--df-skip-verify',
                                 help="""

                                 SIERRA generally assumes/relies on all
                                 dataframes with the same name having the same #
                                 of columns which are of equivalent length
                                 across :term:`Experimental Runs <Experimental
                                 Run>` (different columns within a dataframe can
                                 of course have different lengths). This is
                                 strictly verified during stage 3 by default.

                                 If passed, then the verification step will be
                                 skipped during experimental results processing,
                                 and outputs will be averaged directly.

                                 If not all the corresponding CSV files in all
                                 experiments generated the same # rows, then
                                 SIERRA will (probably) crash during experiments
                                 exist and/or have the stage4. Verification can
                                 take a long time with large # of runs and/or
                                 dataframes per experiment.

                                 """ + self.stage_usage_doc([3]),
                                 action='store_true',
                                 default=False)

        self.stage3.add_argument("--storage-medium", choices=['storage.csv'],
                                 help="""

                                 Specify the storage medium for
                                 :term:`Experimental Run` outputs, so that
                                 SIERRA can select an appropriate plugin to read
                                 them. Any plugin under ``plugins/storage`` can
                                 be used, but the ones that come with SIERRA
                                 are:

                                 - ``storage.csv`` - Experimental run outputs
                                   are stored in a per-run directory as one or
                                   more CSV files.


                                 Regardless of the value of this option, SIERRA
                                 always generates CSV files as it runs and
                                 averages outputs, generates graphs, etc.
                                 """ + self.stage_usage_doc([3]),
                                 default='storage.csv')

        self.stage3.add_argument("--dist-stats",
                                 choices=['none', 'all', 'conf95', 'bw'],
                                 help="""

                                 Specify what kinds of statistics, if any,
                                 should be calculated on the distribution of
                                 experimental data during stage 3 for inclusion
                                 on graphs during stage 4:

                                 - ``none`` - Only calculate and show raw mean
                                   on graphs.

                                 - ``conf95`` - Calculate standard deviation of
                                   experimental distribution and show 95%%
                                   confidence interval on relevant graphs.

                                 - ``bw`` - Calculate statistics necessary to
                                   show box and whisker plots around each point
                                   in the graph. """ +

                                 utils.sphinx_ref(':class: `~sierra.core.graphs.summary_line_graph.SummaryLineGraph`') +

                                 """ only).

                                 - ``all`` - Generate all possible statistics,
                                   and plot all possible statistics on graphs.
                                   """
                                 +
                                 self.graphs_applicable_doc([':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`',
                                                             ':class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`'])
                                 + self.stage_usage_doc([3, 4]),
                                 default='none')

        self.stage3.add_argument("--processing-mem-limit",
                                 type=int,
                                 help="""


                                 Specify, as a percent in [0, 100], how much
                                 memory SIERRA should try to limit itself to
                                 using. This is useful on systems with limited
                                 memory, or on systems which are shared with
                                 other users without per-user memory
                                 restrictions.

                                 """ + self.stage_usage_doc([3, 4]),
                                 default=90)

        self.stage3.add_argument("--df-homogenize",
                                 help="""

                                 SIERRA generally assumes/relies on all
                                 dataframes with the same name having the same #
                                 of columns which are of equivalent length
                                 across: term: `Experimental Runs < Experimental
                                 Run >` (different columns within a dataframe
                                 can of course have different lengths). This is
                                 checked during stage 3 unless
                                 ``--df-skip-verify`` is passed. If strict
                                 verification is skipped, then SIERRA provides
                                 the following options when processing
                                 dataframes during stage {3, 4} to to homogenize
                                 them:

                                 - ``none`` - Don't do anything. This may or may
                                   not produce crashes during stage 4, depending
                                   on what you are doing.

                                 - ``pad`` - Project last valid value in columns
                                   which are too short down the column to make
                                   it match those which are longer.

                                   Note that this may result in invalid
                                   data/graphs if the filled columns are
                                   intervallic, interval average, or cumulative
                                   average data. If the data is a cumulative
                                   count of something, then this policy will
                                   have no ill effects.

                                 - ``zero`` - Same as ``pad``, but always fill
                                   with zeroes.

                                 Homogenization is performed just before writing
                                 dataframes to the specified storage
                                 medium. Useful with real robot experiments if
                                 the number of datapoints captured per-robot is
                                 slightly different, depending on when they
                                 started executing relative to when the
                                 experiment started.

                                 """,
                                 default='none')

    def init_stage4(self) -> None:
        """
        Define cmdline arguments for stage 4.
        """
        self.stage4.add_argument("--exp-graphs",
                                 choices=['intra', 'inter', 'all', 'none'],
                                 help="""

                                 Specify which types of graphs should be
                                 generated from experimental results:

                                 - ``intra`` - Generate intra-experiment graphs
                                   from the results of a single experiment
                                   within a batch, for each experiment in the
                                   batch(this can take a long time with large
                                   batch experiments). If any intra-experiment
                                   models are defined and enabled, those are run
                                   and the results placed on appropriate graphs.

                                 - ``inter`` - Generate inter-experiment graphs
                                   _across_ the results of all experiments in a
                                   batch. These are very fast to generate,
                                   regardless of batch experiment size. If any
                                   inter-experiment models are defined and
                                   enabled, those are run and the results placed
                                   on appropriate graphs.

                                 - ``all`` - Generate all types of graphs.

                                 - ``none`` - Skip graph generation; provided to
                                   skip graph generation if only video outputs
                                   are desired.

                                 """ + self.stage_usage_doc([4]),
                                 default='all')

        self.stage4.add_argument("--project-no-LN",
                                 help="""

                                 Specify that the intra-experiment and
                                 inter-experiment linegraphs defined in project
                                 YAML configuration should not be
                                 generated. Useful if you are working on
                                 something which results in the generation of
                                 other types of graphs, and the generation of
                                 those linegraphs is not currently needed only
                                 slows down your development cycle.

                                 Model linegraphs are still generated, if
                                 applicable.

                                 """,
                                 action='store_true')

        self.stage4.add_argument("--project-no-HM",
                                 help="""

                                 Specify that the intra-experiment heatmaps
                                 defined in project YAML configuration should
                                 not be generated. Useful if:

                                 - You are working on something which results in
                                   the generation of other types of graphs, and
                                   the generation of heatmaps only slows down
                                   your development cycle.

                                 - You are working on stage5 comparison graphs
                                   for bivariate batch criteria, and
                                   re-generating many heatmaps during stage4 is
                                   taking too long.

                                 Model heatmaps are still generated, if
                                 applicable.

                                 .. versionadded:: 1.2.20

                                 """,
                                 action='store_true')

        # Model options
        models = self.parser.add_argument_group('Models')
        models.add_argument('--models-enable',
                            help="""

                            Enable running of all models; otherwise, no models
                            are run, even if they appear in the project config
                            file. The logic behind having models disabled by
                            default is that most users won't have them.

                            """,
                            action="store_true")

        # Rendering options
        rendering = self.parser.add_argument_group(
            'Stage4: Rendering (see also stage1 rendering options)')

        rendering.add_argument("--render-cmd-opts",
                               help="""

                               Specify the: program: `ffmpeg` options to appear
                               between the specification of the input image
                               files and the specification of the output
                               file. The default is suitable for use with ARGoS
                               frame grabbing set to a frames size of 1600x1200
                               to output a reasonable quality video.

                               """ + self.stage_usage_doc([4]),
                               default="-r 10 -s:v 800x600 -c:v libx264 -crf 25 -filter:v scale=-2:956 -pix_fmt yuv420p")

        rendering.add_argument("--project-imagizing",
                               help="""

                               Enable generation of image files from CSV files
                               captured during stage 2 and averaged during stage
                               3 for each experiment. See
                               :ref:`ln-sierra-usage-rendering-project` for
                               details and restrictions.

                               """ + self.stage_usage_doc([3, 4]),
                               action='store_true')

        rendering.add_argument("--project-rendering",
                               help="""

                               Enable generation of videos from imagized CSV
                               files created as a result of
                               ``--project-imagizing``. See
                               :ref:`ln-sierra-usage-rendering-project` for
                               details.

                               """ + self.stage_usage_doc([4]),
                               action='store_true')

        rendering.add_argument("--bc-rendering",
                               help="""

                               Enable generation of videos from generated
                               graphs, such as heatmaps. Bivariate batch
                               criteria only.

                               .. versionadded: 1.2.20

                               """ + self.stage_usage_doc([4]),
                               action='store_true')

    def init_stage5(self) -> None:
        """
        Define cmdline arguments for stage 5.
        """
        self.stage5.add_argument("--controllers-list",
                                 help="""

                                 Comma separated list of controllers to compare
                                 within ``--sierra-root``.

                                 The first controller in this list will be used
                                 for as the controller of primary interest if ``--comparison-type`` is passed.

                                 """ + self.stage_usage_doc([5]))

        self.stage5.add_argument("--controllers-legend",
                                 help="""

                                 Comma separated list of names to use on the
                                 legend for the generated comparison graphs,
                                 specified in the same order as the
                                 ``--controllers-list``.

                                 """ + self.stage_usage_doc([5],
                                                            "If omitted: the raw controller names will be used."))

        self.stage5.add_argument("--scenarios-list",
                                 help="""

                                 Comma separated list of scenarios to compare
                                 ``--controller`` across within
                                 ``--sierra-root``.

                                 """ + self.stage_usage_doc([5]))

        self.stage5.add_argument("--scenarios-legend",
                                 help="""

                                 Comma separated list of names to use on the
                                 legend for the generated inter-scenario
                                 controller comparison graphs(if applicable),
                                 specified in the same order as the
                                 ``--scenarios-list``.

                                 """ + self.stage_usage_doc([5],
                                                            "If omitted: the raw scenario names will be used."))
        self.stage5.add_argument("--scenario-comparison", help="""

                                 Perform a comparison of ``--controller`` across
                                 ``--scenarios-list`` (univariate batch criteria
                                 only).  """
                                 + self.stage_usage_doc([5],
                                                        """Either ``--scenario-comparison`` or ``--controller-comparison`` must be
                                 passed."""), action='store_true')

        self.stage5.add_argument("--controller-comparison",
                                 help="""

                                 Perform a comparison of ``--controllers-list``
                                 across all scenarios at least one controller
                                 has been run on.  """ + self.stage_usage_doc([5],
                                                                              "Either ``--scenario-comparison`` or ``--controller-comparison`` must be passed."),
                                 action='store_true')

        self.stage5.add_argument("--comparison-type",
                                 choices=['LNraw',
                                          'HMraw', 'HMdiff', 'HMscale',
                                          'SUraw', 'SUscale', 'SUdiff'],
                                 help="""

                                 Specify how controller comparisons should be
                                 performed.

                                 If the batch criteria is univariate, the
                                 options are:

                                 - ``LNraw`` - Output raw 1D performance
                                   measures using a single """ +

                                 utils.sphinx_ref(':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`') +

                                 """ for each measure, with all ``--controllers-list`` controllers shown on the
                                   same graph.

                                 If the batch criteria is bivariate, the options
                                 are:

                                 - ``LNraw`` - Output raw performance measures
                                   as a set of """ +

                                 utils.sphinx_ref(':class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`') +

                                 r"""s, where each
                                   line graph is constructed from the i-th
                                   row/column for the 2D dataframe for the
                                   performance results for all controllers.

                                   .. NOTE:: SIERRA cannot currently plot
                                      statistics on the linegraphs built from
                                      slices of the 2D CSVs/heatmaps generated
                                      during stage4, because statistics
                                      generation is limited to stage3. This
                                      limitation may be removed in a future
                                      release.

                                 - ``HMraw`` - Output raw 2D performance
                                   measures as a set of dual heatmaps comparing
                                   all controllers against the controller of
                                   primary interest(one per pair).

                                 - ``HMdiff`` - Subtract the performance measure
                                   of the controller of primary interest against
                                   all other controllers, pairwise, outputting
                                   one 2D heatmap per comparison.

                                 - ``HMscale`` - Scale controller performance
                                   measures against those of the controller of
                                   primary interest by dividing, outputing one
                                   2D heatmap per comparison.

                                 - ``SUraw`` - Output raw 3D performance
                                   measures as a single, stacked 3D surface
                                   plots comparing all controllers(identical
                                   plots, but viewed from different angles).

                                 - ``SUscale`` - Scale controller performance
                                   measures against those of the controller of
                                   primary interest by dividing. This results in
                                   a single stacked 3D surface plots comparing
                                   all controllers(identical plots, but viewed
                                   from different angles).

                                 - ``SUdiff`` - Subtract the performance measure
                                   of the controller of primary interest from
                                   each controller(including the primary). This
                                   results in a set single stacked 3D surface
                                   plots comparing all controllers(identical
                                   plots, but viewed from different angles), in
                                   which the controller of primary interest
                                   forms an(X, Y) plane at Z=0.


                                 For all comparison types,
                                 ``--controllers-legend`` is used if passed for
                                 legend.

                                 """ + self.stage_usage_doc([5]))

        self.stage5.add_argument("--bc-univar",
                                 help="""

                                 Specify that the batch criteria is
                                 univariate. This cannot be deduced from the
                                 command line ``--batch-criteria`` argument in
                                 all cases because we are comparing controllers
                                 `across` scenarios, and each scenario
                                 (potentially) has a different batch criteria
                                 definition, which will result in (potentially)
                                 erroneous comparisons if we don't re-generate
                                 the batch criteria for each scenaro we compare
                                 controllers within.

                                 """ + self.stage_usage_doc([5]),
                                 action='store_true')

        self.stage5.add_argument("--bc-bivar",
                                 help="""

                                 Specify that the batch criteria is
                                 bivariate. This cannot be deduced from the
                                 command line ``--batch-criteria`` argument in
                                 all cases because we are comparing controllers
                                 `across` scenarios, and each
                                 scenario(potentially) has a different batch
                                 criteria definition, which will result in
                                 (potentially) erroneous comparisons if we don't
                                 re-generate the batch criteria for each scenaro
                                 we compare controllers in .

                                 """ + self.stage_usage_doc([5]),
                                 action='store_true')


class CoreCmdlineValidator():
    """Validate the core command line arguments.

    This ensures that the pipeline will work properly in all stages, given the
    options that were passed.

    """

    def __call__(self, args: argparse.Namespace) -> None:
        self._check_bc(args)
        self._check_pipeline(args)

        assert args.sierra_root is not None,\
            '--sierra-root is required for all stages'

    def _check_bc(self, args: argparse.Namespace) -> None:
        assert len(args.batch_criteria) <= 2,\
            "Too many batch criteria passed"

        if len(args.batch_criteria) == 2:
            assert args.batch_criteria[0] != args.batch_criteria[1], \
                "Duplicate batch criteria passed"

            assert isinstance(args.batch_criteria, list), \
                'Batch criteria not passed as list on cmdline'

    def _check_pipeline(self, args: argparse.Namespace) -> None:
        if any(stage in args.pipeline for stage in [1]) in args.pipeline:
            assert args.n_runs is not None,\
                '--n-runs is required for running stage 1'
            assert args.template_input_file is not None,\
                '--template-input-file is required for running stage 1'
            assert args.scenario is not None, \
                '--scenario is required for running stage 1'

        assert all(stage in [1, 2, 3, 4, 5] for stage in args.pipeline),\
            'Only 1-5 are valid pipeline stages'

        if any(stage in args.pipeline for stage in [1, 2, 3, 4]):
            assert len(args.batch_criteria) > 0,\
                '--batch-criteria is required for running stages 1-4'
            assert args.controller is not None,\
                '--controller is required for running stages 1-4'

        if 5 in args.pipeline:
            assert args.bc_univar or args.bc_bivar, \
                '--bc-univar or --bc-bivar is required for stage 5'
            assert args.scenario_comparison or args.controller_comparison,\
                '--scenario-comparison or --controller-comparison required for stage 5'
            if args.scenario_comparison:
                assert args.controller is not None,\
                    '--controller is required for --scenario-comparison'


def sphinx_cmdline_multistage():
    return CoreCmdline([BootstrapCmdline().parser], [-1]).parser


def sphinx_cmdline_stage3():
    return CoreCmdline(None, [3]).parser


def sphinx_cmdline_stage4():
    return CoreCmdline(None, [4]).parser


def sphinx_cmdline_stage5():
    return CoreCmdline(None, [5]).parser


__api__ = [
    'ArgumentParser',
    'BaseCmdline',
    'BootstrapCmdline',
    'CoreCmdline',
]
