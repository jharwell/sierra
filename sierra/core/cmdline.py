# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Core command line parsing and validation classes."""

# Core packages
import argparse
import sys
import typing as tp

# 3rd party packages
import psutil

# Project packages
import sierra.version
from sierra.core import utils

VERSION_MSG = (
    "reSearch pIpEline for Reproducibility, Reusability and "
    f"Automation (SIERRA) v{sierra.version.__version__}.\n"
    "License: MIT.\n"
    "This is free software: you are free to change and redistribute it.\n"
    "SIERRA comes with no warranty.\n\n"
    "See the documentation at "
    "https://sierra.readthedocs.io/en/master/,\n"
    "or 'man sierra' for details.\n"
)


class ArgumentParser(argparse.ArgumentParser):
    """SIERRA's argument parser overriding default argparse behavior.

    Delivers a custom help message without listing options, as the options which
    SIERRA accepts differs dramatically depending on loaded plugins.

    """

    HELP_MSG = (
        "Usage:\n\nsierra-cli [-v | --version] [OPTION]...\n\n"
        "What command line options SIERRA accepts depends on the loaded\n"
        "plugin set. 'man sierra-cli' will give you the full set of options\n"
        "that comes with SIERRA.\n\n"
    )

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout

        file.write(self.HELP_MSG + "\n")


class BaseCmdline:
    """
    The base cmdline definition class for SIERRA for reusability.

    """

    def __init__(self) -> None:
        self.multistage_desc = (
            "Multi-stage options",
            "Options which are used in multiple pipeline stages",
        )
        self.stage1_desc = "Stage 1 options", "Options for generating experiments"
        self.stage2_desc = "Stage 2 options", "Options for running experiments"
        self.stage3_desc = (
            "Stage 3 options",
            "Options for processing experiment results",
        )
        self.stage4_desc = "Stage 4 options", "Options for generating products"
        self.stage5_desc = "Stage 5 options", "Options for product comparison"

    @staticmethod
    def stage_usage_doc(stages: list[int], omitted: str = "If omitted: N/A.") -> str:
        lst = ",".join(map(str, stages))
        return "\n.. TIP:: Used by stage {}; can be omitted otherwise. {}\n".format(
            lst, omitted
        )

    @staticmethod
    def bc_applicable_doc(criteria: list[str]) -> str:
        lst = "".join("   - " + bc + "\n" for bc in criteria)
        return f"\n.. TIP:: Applicable batch criteria:\n\n{lst}\n"

    @staticmethod
    def graphs_applicable_doc(graphs: list[str]) -> str:
        lst = "".join("   - " + utils.sphinx_ref(graph) + "\n" for graph in graphs)
        return f"\n.. TIP:: Applicable graphs:\n\n{lst}\n"


class BootstrapCmdline(BaseCmdline):
    """
    Defines the arguments that are used to bootstrap SIERRA/load plugins.
    """

    def __init__(self) -> None:
        super().__init__()

        self.parser = ArgumentParser(add_help=True, allow_abbrev=False)

        bootstrap = self.parser.add_argument_group(
            "Bootstrap options", "Bare-bones options for bootstrapping SIERRA"
        )

        bootstrap.add_argument(
            "--project",
            help="""
                 Specify which :term:`Project` to load.
                 """
            + self.stage_usage_doc([1, 2, 3, 4, 5]),
        )

        bootstrap.add_argument(
            "--version",
            "-v",
            help="""
                 Display SIERRA version information on stdout and then exit.
                 """,
            action="store_true",
        )

        bootstrap.add_argument(
            "--log-level",
            choices=["ERROR", "INFO", "WARNING", "DEBUG", "TRACE"],
            help="""
                 The level of logging to use when running SIERRA.
                 """
            + self.stage_usage_doc([1, 2, 3, 4, 5]),
            default="INFO",
        )

        bootstrap.add_argument(
            "--engine",
            help="""
                 This argument defines the :term:`Engine` you want to run
                 experiments on.

                 The value of this argument determines the execution environment
                 for experiments; different engines (e.g., simulator, real
                 robots) will have different configuration options.

                 Valid values can be any folder name inside a folder on the
                 :envvar:`SIERRA_PLUGIN_PATH` (with ``/`` replaced with ``.`` as
                 you would expect for using path names to address python
                 packages).  The engines which come with SIERRA are:

                     - ``engine.argos`` - This directs SIERRA to run experiments
                       using the :term:`ARGoS` simulator.  Selecting this engine
                       assumes your code has been developed and configured for
                       ARGoS.

                     - ``engine.ros1gazebo`` - This directs SIERRA to run
                       experiments using the :term:`Gazebo` simulator and
                       :term:`ROS1`.  Selecting this engine assumes your code
                       has been developed and configured for Gazebo and ROS1.

                     - ``engine.ros1robot`` - This directs SIERRA to run
                       experiments using :term:`ROS1` on a real robot of your
                       choosing.  Selecting this engine assumes your code has
                       been developed and configured for ROS1.
                 """,
            default="engine.argos",
        )

        bootstrap.add_argument(
            "--skip-pkg-checks",
            help="""
                 Skip the usual startup package checks.  Only do this if you are
                 SURE you will never use the SIERRA functionality which requires
                 packages you don't have installed/can't install.
                 """,
            action="store_true",
        )

        bootstrap.add_argument(
            "--execenv",
            help="""
                 This argument defines `how` experiments are going to be run,
                 using the ``--engine`` you have selected.

                 Valid values can be any folder name inside a folder on the
                 :envvar:`SIERRA_PLUGIN_PATH` (with ``/`` replaced with ``.`` as
                 you would expect for using path names to address python
                 packages).  The execution environments which come with SIERRA
                 are:

                     - ``hpc.local`` - This directs SIERRA to run experiments on
                       the local machine.  See :ref:`plugins/execenv/hpc/local`
                       for a detailed description.

                     - ``hpc.pbs`` - The directs SIERRA to run experiments
                       spread across multiple allocated nodes in an HPC
                       computing environment managed by TORQUE-PBS.  See
                       :ref:`plugins/execenv/hpc/pbs` for a detailed
                       description.

                     - ``hpc.slurm`` - The directs SIERRA to run experiments
                       spread across multiple allocated nodes in an HPC
                       computing environment managed by SLURM.  See
                       :ref:`plugins/execenv/hpc/slurm` for a detailed
                       description.

                     - ``hpc.adhoc`` - This will direct SIERRA to run
                       experiments on an ad-hoc network of computers.  See
                       :ref:`plugins/execenv/hpc/adhoc` for a detailed
                       description.

                     - ``prefectserver.local`` - This will direct SIERRA to run
                       experiments locally using a spun-up :term:`Prefect` job
                       scheduler/server.  See
                       :ref:`plugins/execenv/prefectserver/local` for a
                       detailed description.

                     - ``prefectserver.dockerremote`` - This will direct SIERRA
                       to run experiments remote using a :term:`Prefect` job
                       scheduler/server in docker containers.  See
                       :ref:`plugins/execenv/prefectserver/dockerremote` for a
                       detailed description.

                     - ``robot.turtlebot3`` - This will direct SIERRA to run
                       experiments on real Turtlebots.

                 Not all engines support all execution environments.
                 """
            + self.stage_usage_doc([1, 2]),
            default="hpc.local",
        )

        bootstrap.add_argument(
            "--expdef",
            help="""
                 Specify the experiment definition format, so that SIERRA can
                 select an appropriate plugin to read/write files of that
                 format, and manipulate in-memory representations to create
                 runnable experiments.  Any plugin on
                 :envvar:`SIERRA_PLUGIN_PATH` can be used, but the ones that
                 come with SIERRA are:

                     - ``expdef.xml`` - Experimental definitions are created
                       from XML files.  This causes ``--expdef-template`` to be
                       parsed as XML.

                     - ``expdef.json`` - Experimental definitions are created
                       from json files.  This causes ``--expdef-template`` to be
                       parsed as JSON.
                 """
            + self.stage_usage_doc([1, 4, 5]),
            default="expdef.xml",
        )
        bootstrap.add_argument(
            "--storage",
            help="""
                 Specify the storage medium for :term:`Experimental Run`
                 outputs, so that SIERRA can select an appropriate plugin to
                 read them.  Any plugin on :envvar:`SIERRA_PLUGIN_PATH`, but the
                 ones that come with SIERRA are:

                     - ``storage.csv`` - Experimental run outputs are stored in
                       a per-run directory as one or more CSV files.

                     - ``storage.arrow`` - Experimental run outputs are stored
                       in a per-run directory as one or more apache arrow files.

                 Regardless of the value of this option, SIERRA always generates
                 CSV files as it runs and averages outputs, generates graphs,
                 etc.
                 """
            + self.stage_usage_doc([3]),
            default="storage.csv",
        )

        bootstrap.add_argument(
            "--proc",
            help="""
                 Specify the set of plugins to run during stage 3 for data
                 processing.  The plugins are executed IN ORDER of appearance,
                 so make sure to handle dependencies.  Any plugin on
                 :envvar:`SIERRA_PLUGIN_PATH` can be used, but the ones that
                 come with SIERRA are:

                     - ``proc.statistics`` - Generate statistics from all
                       :term:`Raw Output Data` files.

                     - ``proc.imagize`` - :term:`Imagize` :term:`Raw Output
                       Data` files.

                     - ``proc.collate`` - Performs :term:`Data Collation` on
                       :term:`Raw Output Data` files.

                     - ``proc.compress`` - Performs data compression on all
                       :term:`Raw Output Data` files.

                     - ``proc.decompress`` - Performs data decompression on all
                       :term:`Raw Output Data` files previously compresed with
                       ``proc.compress``.
                 """
            + self.stage_usage_doc([3]),
            nargs="+",
            default=["proc.statistics", "proc.collate"],
        )

        bootstrap.add_argument(
            "--prod",
            help="""
                 Specify the set of plugins to run during stage 4 for
                 product/deliverable generation.  The plugins are executed IN
                 ORDER of appearance, so make sure to handle dependencies.  Any
                 plugin on :envvar:`SIERRA_PLUGIN_PATH` can be used, but the
                 ones that come with SIERRA are:

                     - ``prod.graphs`` - Generate graphs :term:`Processed Output
                       Data` files.

                     - ``prod.render`` - Render previously :term:`imagized
                       <Imagize>` files into videos.
                 """
            + self.stage_usage_doc([4]),
            nargs="+",
            default=["prod.graphs"],
        )

        bootstrap.add_argument(
            "--compare",
            help="""
                 Specify the set of plugins to run during stage 5 for
                 product/deliverable comparison.  The plugins are executed IN
                 ORDER of appearance, so make sure to handle dependencies.  Any
                 plugin on :envvar:`SIERRA_PLUGIN_PATH` can be used, but the
                 ones that come with SIERRA are:

                     - ``compare.graphs`` - Combine previously generated graphs
                       onto a single plot.
                 """
            + self.stage_usage_doc([5]),
            nargs="+",
            default=["compare.graphs"],
        )
        bootstrap.add_argument(
            "--rcfile",
            help="""
                 Specify the rcfile SIERRA should read additional cmdline
                 arguments from.  Any rcfile arguments overriden by cmdline
                 args, if both are present.  See also :envvar:`SIERRA_RCFILE`.
                 """
            + self.stage_usage_doc([1, 2, 3, 4, 5]),
        )


class CoreCmdline(BaseCmdline):
    """Defines the core command line arguments for SIERRA using :class:`argparse`."""

    def __init__(
        self, parents: tp.Optional[list[ArgumentParser]], stages: list[int]
    ) -> None:
        super().__init__()

        self.scaffold_cli(parents)
        self.init_cli(stages)

    def scaffold_cli(self, parents: tp.Optional[list[ArgumentParser]]) -> None:
        """
        Scaffold CLI by defining the parser and common argument groups.
        """
        if parents is not None:
            self.parser = ArgumentParser(
                prog="sierra-cli", parents=parents, add_help=False, allow_abbrev=False
            )
        else:
            self.parser = ArgumentParser(
                prog="sierra-cli", add_help=False, allow_abbrev=False
            )

        self.multistage = self.parser.add_argument_group(
            self.multistage_desc[0], self.multistage_desc[1]
        )
        self.stage1 = self.parser.add_argument_group(
            self.stage1_desc[0], self.stage1_desc[1]
        )
        self.stage2 = self.parser.add_argument_group(
            self.stage2_desc[0], self.stage2_desc[1]
        )
        self.stage3 = self.parser.add_argument_group(
            self.stage3_desc[0], self.stage3_desc[1]
        )
        self.stage4 = self.parser.add_argument_group(
            self.stage4_desc[0], self.stage4_desc[1]
        )
        self.stage5 = self.parser.add_argument_group(
            self.stage5_desc[0], self.stage5_desc[1]
        )
        self.shortforms = self.parser.add_argument_group(
            title="Shortform aliases",
            description="""
                        Most cmdline options to SIERRA are longform (i.e.,
                        ``--option``), but some families of options have
                        shortforms (i.e., ``-o`` for ``--option``) as well.
                        Shortform arguments behave the same as their longform
                        counterparts.  If both are passed, the the shortform
                        overrides.
                        """,
        )

    def init_cli(self, stages: list[int]) -> None:
        """Define cmdline arguments for stages 1-5."""
        if -1 in stages:
            self.init_multistage()
            self.init_shortforms()

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

    def init_shortforms(self) -> None:
        """
        Define cmdline shortform arguments for all pipeline stages.
        """
        self.shortforms.add_argument(
            "-p",
            action="append",
            nargs="+",
            help="""
                 Alias of ``--plot-``; any number of ``--plot-XX`` option can be
                 passed with separate ``-p`` arguments .  If the argument to
                 ``-p`` does not map to a valid ``plot-XX`` option it is
                 ignored.

                 .. versionadded:: 1.3.14
                 """,
        )

        self.shortforms.add_argument(
            "-e",
            action="append",
            nargs="+",
            help="""
                 Alias of ``--exp-``; any number of ``--exp-XX`` option can be
                 passed with separate ``-e`` arguments .  If the argument to
                 ``-e`` does not map to a valid ``exp-XX`` option it is ignored.

                 .. versionadded:: 1.3.14
                 """,
        )

        self.shortforms.add_argument(
            "-x",
            action="append",
            nargs="+",
            help="""
                 Alias of ``--exec-``; any number of ``--exec-XX`` option can be
                 passed with separate ``-x`` arguments .  If the argument to
                 ``-x`` does not map to a valid ``exec-XX`` option it is
                 ignored.

                 .. versionadded:: 1.3.14
                 """,
        )

        self.shortforms.add_argument(
            "-s",
            action="append",
            nargs="+",
            help="""
                 Alias of ``--skip``; any number of ``--skip-XX`` option can be
                 passed with separate ``-s`` arguments .  If the argument to
                 ``-s`` does not map to a valid ``skip-XX`` option it is
                 ignored.

                 .. versionadded:: 1.3.14
                 """,
        )

    def init_multistage(self) -> None:
        """
        Define cmdline arguments which are used in multiple pipeline stages.
        """
        self.multistage.add_argument(
            "--expdef-template",
            metavar="filepath",
            help="""
                 The template ``.xml`` input file for the batch experiment.
                 Beyond the requirements for the specific ``--engine``, the
                 content of the file can be anything valid for the format, with
                 the exception of the SIERRA requirements detailed in
                 :ref:`plugins/expdef`.
                 """
            + self.stage_usage_doc([1, 2, 3, 4]),
        )

        self.multistage.add_argument(
            "--exp-overwrite",
            help="""
                 When SIERRA calculates the batch experiment root (or any child
                 path in the batch experiment root) during stage {1, 2}, if the
                 calculated path already exists it is treated as a fatal error
                 and no modifications to the filesystem are performed.  This
                 flag overwrides the default behavior.  Provided to avoid
                 accidentally overwrite input/output files for an experiment,
                 forcing the user to be explicit with potentially dangerous
                 actions.
                 """
            + self.stage_usage_doc([1, 2]),
            action="store_true",
        )

        self.multistage.add_argument(
            "--sierra-root",
            metavar="dirpath",
            help="""
                 Root directory for all SIERRA generated and created files.

                 Subdirectories for controllers, scenarios,
                 experiment/experimental run inputs/outputs will be created in
                 this directory as needed.  Can persist between invocations of
                 SIERRA.
                 """
            + self.stage_usage_doc([1, 2, 3, 4, 5]),
            default="<home directory>/exp",
        )

        self.multistage.add_argument(
            "--batch-criteria",
            "--bc",
            metavar="[<category>.<definition>,...]",
            help="""
                 Definition of criteria(s) to use to define the experiment.

                 Specified as a list of 0 or 1 space separated strings, each
                 with the following general structure:

                 ``<category>.<definition>``

                 ``<category>`` must be a filename from the ``core/variables/``
                 or from a ``--project`` ``<project>/variables/`` directory, and
                 ``<definition>`` must be a parsable namne (according to the
                 requirements of the criteria defined by the parser for
                 ``<category>``).
                 """
            + self.stage_usage_doc([1, 2, 3, 4, 5]),
            nargs="+",
            default=[],
        )

        self.multistage.add_argument(
            "--pipeline",
            help="""
                 Define which stages of the experimental pipeline to run:

                     - Stage1 - Generate the experiment definition from the
                       template input file, batch criteria, and other command
                       line options.  Part of default pipeline.

                     - Stage2 - Run a previously generated experiment.  Part of
                       default pipeline.

                     - Stage3 - Post-process experimental results after running
                       the batch experiment; some parts of this can be done in
                       parallel.  Part of default pipeline.

                     - Stage4 - Perform deliverable/product generation after
                       processing results for a batch experiment, which can
                       include shiny graphs and videos.  Part of default
                       pipeline.

                     - Stage5 - Compare generated products.
                 """,
            type=int,
            nargs="*",
            default=[1, 2, 3, 4],
        )
        self.multistage.add_argument(
            "--exp-range",
            help="""
                 Set the experiment numbers from the batch to run, average,
                 generate intra-experiment graphs from, or generate
                 inter-experiment graphs from (0 based).  Specified in the form
                 ``min_exp_num:max_exp_num`` (closed interval/inclusive).  If
                 omitted, runs, averages, and generates intra-experiment and
                 inter-experiment performance measure graphs for all experiments
                 in the batch (default behavior).

                 This is useful to re-run part of a batch experiment in HPC
                 environments if SIERRA gets killed before it finishes running
                 all experiments in the batch, or to redo a single experiment
                 with real robots which failed for some reason.
                 """
            + self.stage_usage_doc([2, 3, 4]),
        )

        self.multistage.add_argument(
            "--engine-vc",
            help="""
                 For applicable ``--engines``, enable visual capturing of
                 run-time data during stage 2.  This data can be frames (i.e.,
                 .png files), or rendering videos, depending on the engine.  If
                 the captured data was frames, then SIERRA can render the
                 captured frames into videos during stage 4.  If the selected
                 ``--engine`` does not support visual capture, then this option
                 has no effect.  See :ref:`plugins/prod/render` for more
                 details.
                 """
            + self.stage_usage_doc([1, 4]),
            action="store_true",
        )

        self.multistage.add_argument(
            "--processing-parallelism",
            type=int,
            help="""
                 The level of parallelism to use in results processing/graph
                 generation producer-consumer queue.  This value is used to
                 allocate consumers and produces in a 3:1 ratio.  If you are
                 doing a LOT of processing, you may want to oversubscribe your
                 machine by passing a higher than default value to overcome
                 slowdown with high disk I/O.
                 """
            + self.stage_usage_doc([3, 4]),
            default=psutil.cpu_count(),
        )
        self.multistage.add_argument(
            "--exec-parallelism-paradigm",
            choices=["per-batch", "per-exp", "per-run", None],
            default=None,
            help="""
                 The level of parallelism to use when executing experiments in
            stage 2. This should generall be set by
            :py:func:`~sierra.core.experiment.bindings.IExpConfigurer.parallelism_paradigm()`
            in your selected :term:`Engine`; this option is provided as an override.
                 """
            + self.stage_usage_doc([1, 2]),
        )

        self.multistage.add_argument(
            "--n-runs",
            type=int,
            default=1,
            help="""
                 The # of experimental runs that will be executed and their
                 results processed to form the result of a single experiment
                 within a batch.

                 If ``--engine`` is a simulator and ``--execenv`` is something
                 other than ``hpc.local`` then this may be be used to determine
                 the concurrency of experimental runs.
                 """
            + self.stage_usage_doc([1, 2]),
        )

    def init_stage1(self) -> None:
        """
        Define cmdline arguments for stage 1.
        """
        self.stage1.add_argument(
            "--preserve-seeds",
            help="""
                 Preserve previously generated random seeds for experiments (the
                 default).  Useful for regenerating experiments when you change
                 parameters/python code that don't affects experimental outputs
                 (e.g., paths).  Preserving/overwriting random seeds is not
                 affected by ``--exp-overwrite``.
                 """,
            default=True,
        )

        self.stage1.add_argument(
            "--no-preserve-seeds",
            help="""
                 Opposite of ``--preserve-seeds``.
                 """,
            dest="preserve_seeds",
            action="store_false",
        )

    def init_stage2(self) -> None:
        """
        Define cmdline arguments for stage 2.
        """
        self.stage2.add_argument(
            "--nodefile",
            help="""
                 Specify a list of compute nodes which SIERpRA will use to run
                 jobs.  For simulator :term:`Engines <Engine>`, these are HPC
                 resource nodes.  For real robot engines, these are robot
                 hostnames/IP addresses.  This information can also be supplied
                 via the :envvar:`SIERRA_NODEFILE` environment variable; this
                 argument takes priority if both are supplied.
                 """,
        )

    def init_stage3(self) -> None:
        """
        Define cmdline arguments for stage 3.
        """
        self.stage3.add_argument(
            "--df-verify",
            help="""
                 SIERRA generally assumes/relies on all dataframes with the same
                 name having the same # of columns which are of equivalent
                 length across :term:`Experimental Runs <Experimental Run>`
                 (different columns within a dataframe can of course have
                 different lengths).  However this is not checked by default.

                 If passed, then the verification step not be skipped, and will
                 be executed during experimental results processing, and outputs
                 will be averaged directly.

                 If not all the corresponding CSV files in all experiments
                 generated the same # rows, then SIERRA will (probably) crash
                 during experiments exist and/or have the stage4.  Verification
                 can take a long time with large # of runs and/or dataframes per
                 experiment.
                 """
            + self.stage_usage_doc([3]),
            action="store_true",
            default=False,
        )

        self.stage3.add_argument(
            "--processing-mem-limit",
            type=int,
            help="""
                 Specify, as a percent in [0, 100], how much memory SIERRA
                 should try to limit itself to using.  This is useful on systems
                 with limited memory, or on systems which are shared with other
                 users without per-user memory restrictions.
                 """
            + self.stage_usage_doc([3, 4]),
            default=90,
        )

        self.stage3.add_argument(
            "--df-homogenize",
            help="""
                 SIERRA generally assumes/relies on all dataframes with the same
                 name having the same # of columns which are of equivalent
                 length across: term: `Experimental Runs < Experimental Run >`
                 (different columns within a dataframe can of course have
                 different lengths).  This not checked unless ``--df-verify`` is
                 passed.  If strict verification is skipped, then SIERRA
                 provides the following options when processing dataframes
                 during stage {3, 4} to to homogenize them:

                     - ``none`` - Don't do anything.  This may or may not
                       produce crashes during stage 4, depending on what you are
                       doing.

                     - ``pad`` - Project last valid value in columns which are
                       too short down the column to make it match those which
                       are longer.

                 Note that this may result in invalid data/graphs if the filled
                 columns are intervallic, interval average, or cumulative
                 average data.  If the data is a cumulative count of something,
                 then this policy will have no ill effects.

                     - ``zero`` - Same as ``pad``, but always fill with zeroes.

                 Homogenization is performed just before writing dataframes to
                 the specified storage medium.  Useful with real robot
                 experiments if the number of datapoints captured per-robot is
                 slightly different, depending on when they started executing
                 relative to when the experiment started.
                 """,
            default="none",
        )

    def init_stage4(self) -> None:
        """
        Define cmdline arguments for stage 4.
        """

    def init_stage5(self) -> None:
        """
        Define cmdline arguments for stage 5.
        """


def sphinx_cmdline_multistage():
    return CoreCmdline([BootstrapCmdline().parser], [-1]).parser


def sphinx_cmdline_stage1():
    return CoreCmdline([], [1]).parser


def sphinx_cmdline_stage3():
    return CoreCmdline([], [3]).parser


def sphinx_cmdline_stage4():
    return CoreCmdline([], [4]).parser


def sphinx_cmdline_stage5():
    return CoreCmdline([], [5]).parser


__all__ = [
    "ArgumentParser",
    "BaseCmdline",
    "BootstrapCmdline",
    "CoreCmdline",
]
