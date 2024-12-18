.. _tutorials/plugin/platform:

==============================
Creating a New Platform Plugin
==============================

.. IMPORTANT:: There is an example of defining a platform plugin in the
               :xref:`sample project repo<SIERRA_SAMPLE_PROJECT` for a fictional
               JSON-based simulator. It is all but functional, because there is
               no such JSON-based simulator available :_). This can be used in
               tandem with this guide to build your own platform plugin.

For the purposes of this tutorial, I will assume you are creating a new
:term:`Platform` :term:`Plugin` ``matrix``, and the code for that plugin lives
in ``$HOME/git/plugins/platform/matrix``.

If you are creating a new platform, you have two options.

#. Create a stand-alone platform, providing your own definitions for all of the
   necessary functions/classes below.

#. Derive from an existing platform by simply calling the "parent" platform's
   functions/calling in your derived definitions except when you need to
   actually extend them (e.g., to add support for a new HPC plugin which is a
   specialization of an existing one).


Before beginning, create the following filesystem structure in
``$HOME/git/plugins/platform/matrix``.

- ``plugin.py`` - This file is required, and is where most of the bits for the
  plugin will go.

- ``cmdline.py`` This file is optional. If your new platform doesn't need any
  additional cmdline arguments, you can skip it.

- ``generators/platform.py`` - This file is required, and containing bits for
  generating experiments pertaining to this platform.


These files will be populated as you go through the rest of the tutorial.

.. NOTE:: For all things that are optional, if you try to use a part of SIERRA
          requiring functionality you didn't define, you *might* get an obvious
          error, or you might get a crash later on, depending. Please help
          improve this aspect of SIERRA!


Creating The Cmdline Interface
==============================

#. Create additional cmdline arguments for the new platform by following
   :ref:`tutorials/misc/cmdline` for platforms. If your new platform doesn't need
   any new arguments, you can skip this step.

#. Connect your new platform cmdline into SIERRA via defining
   ``cmdline_parser()`` in your ``plugin.py`` as shown below. If your new
   platform doesn't need any new arguments, you can skip this step.

   .. code-block:: python

       def cmdline_parser() -> argparse.Parser:
           """
           Get a cmdline parser supporting the platform. The returned parser
           should extend :class:`~sierra.core.cmdline.BaseCmdline`.

           This example extends :class:`~sierra.core.cmdline.BaseCmdline` with:

           - :class:`~sierra.core.hpc.cmdline.HPCCmdline` (HPC common)
           - :class:`~cmd.PlatformCmdline` (platform specifics)

           assuming this platform can run on HPC environments.
           """
           # Initialize all stages and return the initialized
           # parser to SIERRA for use.
           parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
           return cmd.PlatformCmdline(parents=[parser],
                                      stages=[-1, 1, 2, 3, 4, 5]).parser

#. Defining any additional configuration/argument checking beyond what is
   possible in argparse via ``cmdline_postparse_configure()`` in your
   ``plugin.py``. If your new platform doesn't need any new arguments, you can
   skip this step.

   .. code-block:: python

      def cmdline_postparse_configure(argparse.Namespace) -> argparse.Namespace:
          """
          Additional configuration and/or validation of the passed cmdline
          arguments pertaining to this platform.  Validation should be performed
          with assert(), and the parsed argument object should be returned with
          any modifications/additions.
          """

Configuring The Experimental Environment
========================================

#. Define the ``ExpConfigurer`` class in ``plugin.py`` to configure
   :term:`Experiments<Experiment>` in platform-specific ways.
   This class is required. It should conform to
   :class:`~sierra.core.experiment.bindings.IExpConfigurer`. It is used in
   stage 1 *after* experiment generation, in case configuration depends on
   the contents of the experiment.

   Some example use cases:

   - Creating directories not created automatically by the simulator/project
     code.

   - Copying files which :term:`Project` or :term:`Platform` code expects to be
     found next to the main input file for each :term:`Experiment` or
     :term:`Experimental Run`.

Generating Experiments
======================

In ``generators/platform.py``, you may define the following functions:

.. tabs::

   .. tab:: ``for_all_exp()``

      This function is required. It is used to generate expdef
      changes common to all :term:`Experiment Runs<Experimental Run>` in an
      :term:`Experiment` for your platform.

      .. code-block:: python

         import pathlib

         from sierra.core.experiment import definition
         from sierra.core import types
         from sierra.experiment import spec

         def for_all_exp(spec: spec.ExperimentSpec,
                         controller: str,
                         cmdopts: types.Cmdopts,
                         expdef_template_path: pathlib.Path) -> definition.BaseExpDef:
             """
             Create an experiment definition from the
             ``--expdef-template`` and generate XML changes to input files
             that are common to all experiments on the platform. All projects
             using this platform should derive from this class for `their`
             project-specific changes for the platform.

             Arguments:

                 spec: The spec for the experimental run.

                 controller: The controller used for the experiment, as passed
                             via ``--controller``.

                 exp_def_template_path: The path to ``--expdef-template``.
             """
             pass


      .. tab:: ``for_single_exp_run()``

         This function is required. It is used to generate expdef changes for a
         single :term:`Experimental Run` for your platform.

      .. code-block:: python

          import pathlib

          from sierra.core.experiment import definition
          from sierra.core import types
          from sierra.experiment import spec


          def for_single_exp_run(
               exp_def: definition.BaseExpDef,
               run_num: int,
               run_output_path: pathlib.Path,
               launch_stem_path: pathlib.Path,
               random_seed: int,
               cmdopts: types.Cmdopts) -> definition.BaseExpDef:
               """
               Generate expdef changes unique to a experimental run within an
               experiment for the matrix platform.

               Arguments:
                   exp_def: The experiment definition after ``--platform`` changes
                   common to all experiments have been made.

                   run_num: The run # in the experiment.

                   run_output_path: Path to run output directory within
                                    experiment root (i.e., a leaf).

                   launch_stem_path: Path to launch file in the input directory
                                     for the experimental run, sans extension
                                     or other modifications that the platform
                                     can impose.

                   random_seed: The random seed for the run.

                   cmdopts: Dictionary containing parsed cmdline options.
               """
               pass

.. NOTE:: Neither of these functions is called directly in the SIERRA core;
          :term:`Project` generators for experiments must currently call them
          directly. This behavior may change in the future, hence these
          functions are required.

Running Experiments
===================

#. In ``plugin.py``, you must define two required functions:

   .. tabs::

      .. tab:: ``population_size_from_def()``

         .. code-block:: python

            def population_size_from_def(exp_def: definition.BaseExpDef,
                                         main_config: types.YAMLDict,
                                         cmdopts: types.Cmdopts) -> int:
                """
                Given an experiment definition, main configuration, and cmdopts,
                get the # agents in the experiment.
                """
                pass

      .. tab:: ``population_size_from_pickle()``

         .. code-block:: python

            def population_size_from_pickle(chgs: tp.Union[definition.AttrChangeSet,
                                            definition.ElementAddList],
                                            main_config: types.YAMLDict,
                                            cmdopts: types.Cmdopts) -> int:
                """
                Given unpickled experimental changes, main configuration, and
                cmdopts, get the # agents used in the pickled experiment.
                """
                pass

   so that SIERRA can extract the # agents used in a given experiment, which
   some platforms need when defining their shell commands for executing an
   experiment (e.g., ROS).


#. In ``plugin.py``, you may define the following classes which are used in
   stages {1, 2} to generate the cmdline to execute
   :term:`Experiments<Experiment>` and :term:`Experimental Runs<Experimental
   Run>`. SIERRA essentially tries to mimic running experiments using a given
   platform as close as possible to running them on the cmdline directly; thus,
   configuring experiments for platform typically involves putting the needed
   shell commands into a "language" that SIERRA understands.

   .. tabs::

      .. tab:: ExpRunShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.

         It is used in stage 1 to generate (not execute) the shell commands
         per-experimental run for this platform. These are sets of cmds which:

         - Need to be run before an experimental run.

         - Need to be run to actually execute an experimental run.

         - Need to executed post experimental run to cleanup before the next run
           is started. The generated cmds are written to a text file that GNU
           parallel (or some other engine of your choice) will run in stage 2.

         Pay special attention to
         :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator.cmdfile_paradigm()`:
         this is how you tell SIERRA the type of run-time parallelism for your
         platform.

      .. tab:: ExpShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

         It is used in stage 2 to execute (not generate) shell commands
         per-experiment previously written to a text file using GNU parallel (or
         some other engine of your choice). This includes sets of cmds for:

         - Pre-experiment cmds executed prior to any experimental run being
           executed.

         - Post-experiment cleanup cmds before the next experiment is executed.

         .. IMPORTANT:: The result of ``exec_exp_cmds()`` for platforms plugins
                        is ignored, because it doesn't make sense: execution
                        environments execute experiments (DUH).



#. In ``plugin.py``, you may define ``exec_env_check()`` to check the software
   environment (envvars, PATH, etc.) for this platform plugin prior to
   running anything in stage 2. Since stage 2 can be run in a different
   invocation than stage 1, this hook is provided so that the correct
   environment exists prior to executing anything. This function is optional.

   .. code-block:: python

      import os

      from sierra.core import types

      def exec_env_check(cmdopts: types.Cmdopts):
          """
          Check the software environment (envvars, PATH, etc.) for this platform
          plugin prior to running anything in stage 2.
          """
          assert os.environ("MYVAR") != None, "MYVAR must be defined!"

#. In ``plugin.py``, you may define ``pre_exp_diagnostics()``, which can be used
   to emit some useful information via logging at the start of stage 2 before
   starting execution of the :term:`Batch Experiment`. This function is
   optional.

   .. code-block:: python

      import logging

      from sierra.core import types, batchroot

      def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                              pathset: batchroot.PathSet,
                              logger: logging.Logger) -> None:
          """
          Log any INFO-level diagnostics to stdout before a given
          :term:`Experiment` is run. Useful to echo important execution
          environment configuration to the terminal as a sanity check.
          """
          logger.info("Starting batch experiment using MATRIX!")

#. In ``plugin.py``, you may define ``agent_prefix_extract()``, which can be
   used to return the alpha-numeric prefix that will be prepended to each
   agent's numeric ID to create a UUID for the agent. This function is optional.

   .. todo:: is this even used anywhere???

   .. code-block:: python

      def agent_prefix_extract(main_config: types.YAMLDict,
                               cmdopts: types.Cmdopts) -> str:
          """
          Arguments:

              main_config: Parsed dictionary of main YAML configuration.

              cmdopts: Dictionary of parsed command line options.
           """


#. In ``plugin.py``, you may define ``arena_dims_from_criteria()``, which can be
   used get a list of the arena dimensions used in each generated
   experiment. This function is optional; only needed if the dimensions are not
   specified on the cmdline, which can be useful if the batch criteria involves
   changing them; e.g., evaluating behavior with different arena shapes.

   .. code-block:: python

      import typing as tp

      from sierra.core import batch_criteria as bc
      def arena_dims_from_criteria(criteria: bc.BatchCriteria) -> tp.List[utils.ArenaExtent]:
          """
          Arguments:

             criteria: The batch criteria built from cmdline specification
          """


A Full Skeleton
===============

.. tabs::

   .. tab:: ``cmdline.py``

      .. literalinclude:: ../../misc/cmdline-platform.py
         :language: python

   .. tab:: ``plugin.py``

      .. literalinclude:: plugin.py
         :language: python

   .. tab:: ``generators/platform.py``

      .. include:: generators.rst


Finally--Connect to SIERRA!
===========================

After going through all the sections above and creating your plugin, tell SIERRA
about it by putting ``$HOME/git/plugins/`` on your :envvar:`SIERRA_PLUGIN_PATH`
so that your platform can be selected via ``--platform=platform.matrix``. Note
that if you change what directory you put on the plugin path, how you selected
your platform will change. E.g., if you put ``$HOME/git/`` on
:envvar:`SIERRA_PLUGIN_PATH`, then your new plugin will be accessible via
``plugins.platform.matrix`` instead.

.. NOTE:: Platform names have the same constraints as python package names
   (e.g., no dots, so ``matrix.foo`` is not a valid plugin name).

.. NOTE:: If your platform supports/requires a new execution environment, head
          over to :ref:`tutorials/plugin/exec-env`.
