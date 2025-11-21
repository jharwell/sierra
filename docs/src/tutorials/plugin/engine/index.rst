.. _tutorials/plugin/engine:

============================
Creating a New Engine Plugin
============================

.. IMPORTANT:: There is an example of defining a engine plugin in the
               :xref:`sample project repo<SIERRA_SAMPLE_PROJECT` for a fictional
               JSON-based simulator. It is all but functional, because there is
               no such JSON-based simulator available :-). This can be used in
               tandem with this guide to build your own engine plugin.

For the purposes of this tutorial, I will assume you are creating a new
:term:`Engine` :term:`Plugin` ``matrix``, and the code for that plugin lives
in ``$HOME/git/plugins/engine/matrix``.

Before beginning, see the :ref:`plugins/devguide` for a general overview of
creating a new plugin.

If you are creating a new engine, you have two options.

#. Create a stand-alone engine, providing your own definitions for all of the
   necessary functions/classes below.

#. Derive from an existing engine by simply calling the "parent" engine's
   functions/calling in your derived definitions except when you need to
   actually extend them (e.g., to add support for a new HPC plugin which is a
   specialization of an existing one).


Before beginning, create the following filesystem structure in
``$HOME/git/plugins/engine/matrix``.

- ``plugin.py`` - This file is required, and is where most of the bits for the
  plugin will go. You don't *have* to call it this; if you want to use a
  different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new engine doesn't need any
  additional cmdline arguments, you can skip it.

- ``generators/engine.py`` - This file is required, and containing bits for
  generating experiments pertaining to this engine.


These files will be populated as you go through the rest of the tutorial.

.. NOTE:: For all things that are optional, if you try to use a part of SIERRA
          requiring functionality you didn't define, you *might* get an obvious
          error, or you might get a crash later on, depending. Please help
          improve this aspect of SIERRA!


Creating The Cmdline Interface
==============================

#. Create additional cmdline arguments for the new engine by following
   :ref:`plugins/devguide/cmdline` for engines.

#. Defining any additional configuration/argument checking beyond what is
   possible in argparse via ``cmdline_postparse_configure()`` in your
   ``plugin.py``. If your new engine doesn't need any new arguments, you can
   skip this step.

   .. code-block:: python

      def cmdline_postparse_configure(argparse.Namespace) -> argparse.Namespace:
          """
          Additional configuration and/or validation of the passed cmdline
          arguments pertaining to this engine.  Validation should be performed
          with assert(), and the parsed argument object should be returned with
          any modifications/additions.
          """

.. _tutorials/plugin/engine/config:

Configuring The Experimental Environment
========================================

Define the ``ExpConfigurer`` class in ``plugin.py`` to configure
:term:`Experiments<Experiment>` in engine-specific ways.  This class is
required. It should conform to
:class:`~sierra.core.experiment.bindings.IExpConfigurer`. It is used in stage 1
*after* experiment generation, in case configuration depends on the contents of
the experiment. E.g.:

- Creating directories not created automatically by the simulator/project code.

- Copying files which :term:`Project` or :term:`Engine` code expects to be found
  next to the main input file for each :term:`Experiment` or :term:`Experimental
  Run`.

It is also used in stage {1,2} to tell SIERRA the type of execution parallelism
that your :term:`Engine` wants to use via the ``parallelism_paradigm()``
function.

.. IMPORTANT:: :py:func:`~sierra.core.experiment.bindings.IExpConfigurer.parallelism_paradigm()`
               is one of the most important parts of your :term:`Engine`
               definition, and will *dramatically* affect how experiments will
               be executed during stage 2.  Engines can even select different
               paradigms depending on other configuration if they wish.

Some guidance on selecting parallelism.:

``per-batch`` parallelism is appropriate if:

    - Your engine is a simulator of some kind, and is single threaded.  In this
      case, there is no advantage to restricting parallelism to the level of
      :term:`Experiments <Experiment>`, and executing all runs in parallel (up
      to the level supported by ``--execenv`` and available computational
      resources) is desirable for speed.

    - You submit executable code directly in your ``--execenv``.  That is,
      instead of a "classic" HPC approach where you submit a job script which
      when run will run your code, you submit e.g., executable python code to
      the scheduler which it will directly run.

    - You aren't concerned about hogging/using too many computational resources
      w.r.t. whatever you are running on/in.

``per-exp`` parallelism is appropriate if:

    - Your ``--execenv`` is a "classic" HPC environment, and the scheduler
      gives you exclusive control over a set of resources dedicated to you when
      requested, and then you have to run SIERRA within that job with the
      allocated resources.

    - You are worried about hogging/using too many computational resources
      simultaneously.

    - Your engine is a simulator of some kind, and is multi-threaded.  In this
      case, using per-exp parallelism can allow you to maximize the number of
      threads/simulation and thus handle larger workloads.

``per-run`` parallelism is appropriate if:

    - Your engine plugin targets real hardware such as robots.  In this case,
      each experimental run requires multiple remote sub-processes to execute,
      one per agent, since you can't have single physical agent/robot be part of
      multiple experimental runs simultaneously.

.. _tutorials/plugin/engine/exp:

Generating Experiments
======================

In ``generators/engine.py``, you may define the following functions:

.. tabs::

   .. tab:: ``for_all_exp()``

      This function is required. It is used to generate expdef
      changes common to all :term:`Experiment Runs<Experimental Run>` in an
      :term:`Experiment` for your engine.

      .. NOTE:: If your engine supports nested configuration files, this is
                the place to call ``flatten()`` using the selected expdef
                plugin. See code sample below for suggested implementation.

      .. code-block:: python

         import pathlib

         from sierra.core.experiment import definition, spec
         from sierra.core import types
         from sierra.core import plugin_manager as pm

         def for_all_exp(spec: spec.ExperimentSpec,
                         controller: str,
                         cmdopts: types.Cmdopts,
                         expdef_template_fpath: pathlib.Path) -> definition.BaseExpDef:
             """
             Create an experiment definition from the
             ``--expdef-template`` and generate expdef changes to input files
             that are common to all experiments on the engine. All projects
             using this engine should derive from this class for `their`
             project-specific changes for the engine.

             Arguments:

                 spec: The spec for the experimental run.

                 controller: The controller used for the experiment, as passed
                             via ``--controller``.

                 expdef_template_fpath: The path to ``--expdef-template``.
             """
             # Optional, only needed if your engine supports nested
             # configuration files. Note that this snippet assumes that you have
             # already created the experiment definition object in a variable
             # called 'expdef'.
             expdef.flatten(["pathstring1", "pathstring2"])

   .. tab:: ``for_single_exp_run()``

      This function is required. It is used to generate expdef changes for a
      single :term:`Experimental Run` for your engine.

      .. code-block:: python

          import pathlib

          from sierra.core.experiment import definition
          from sierra.core import types
          from sierra.core.experiment import spec


          def for_single_exp_run(
               exp_def: definition.BaseExpDef,
               run_num: int,
               run_output_path: pathlib.Path,
               launch_stem_path: pathlib.Path,
               random_seed: int,
               cmdopts: types.Cmdopts) -> definition.BaseExpDef:
               """
               Generate expdef changes unique to a experimental run within an
               experiment for the matrix engine.

               Arguments:
                   exp_def: The experiment definition after ``--engine`` changes
                   common to all experiments have been made.

                   run_num: The run # in the experiment.

                   run_output_path: Path to run output directory within
                                    experiment root (i.e., a leaf).

                   launch_stem_path: Path to launch file in the input directory
                                     for the experimental run, sans extension
                                     or other modifications that the engine
                                     can impose.

                   random_seed: The random seed for the run.

                   cmdopts: Dictionary containing parsed cmdline options.
               """

   .. tab:: ``arena_dims_from_criteria()``

      This function is optional; only needed if the dimensions are not specified
      on the cmdline for a scenario where you want to change the size of the
      arena from what it is in the template file, which can be useful if the
      batch criteria involves changing them; e.g., evaluating behavior with
      different arena shapes. See :ref:`req/exp/arena-size` for more details.

   .. code-block:: python

      import typing as tp

      from sierra.core import batch_criteria as bc

      def arena_dims_from_criteria(criteria: bc.BatchCriteria) -> tp.List[utils.ArenaExtent]:
          """
          Arguments:

             criteria: The batch criteria built from cmdline specification
          """


.. NOTE:: Neither of these functions is called directly in the SIERRA core;
          :term:`Project` generators for experiments must currently call them
          directly. This behavior may change in the future, hence these
          functions are required.

#. In ``plugin.py``, you may define the following functions:

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
   some engines need when defining their shell commands for executing an
   experiment (e.g., ROS). These functions are optional. HOWEVER, if neither is
   defined, then:

   - You MUST define ``arena_dims_from_criteria()`` in your engine plugin.

   - All :term:`Batch Criteria` that you use must have the arena dimensions
     extractable when passed to ``arena_dims_from_criteria()``.

   See :ref:`req/exp/arena-size` for more info.


#. In ``plugin.py``, you may define the following classes which are used in
   stages {1, 2} to generate the cmdline to execute
   :term:`Experiments<Experiment>` and :term:`Experimental Runs<Experimental
   Run>`. SIERRA essentially tries to mimic running experiments using a given
   engine as close as possible to running them on the cmdline directly; thus,
   configuring experiments for engine typically involves putting the needed
   shell commands into a "language" that SIERRA understands.

   .. tabs::

      .. tab:: BatchShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IBatchShellCmdsGenerator`.

         It is used in stage 2 to execute (not generate) shell commands
         per-batch previously written to a text file using GNU parallel (or
         some other engine of your choice). This includes sets of cmds for:

         - Pre-batch cmds executed prior to any experiment being executed.

         - Cmds to execute the batch experiment.

         - Post-batch cleanup cmds run after all experiments have been executed.

         This generator corresponds to ``per-batch`` parallelism; see
         :ref:`tutorials/plugin/engine/config` for details.

         .. code-block:: python

            import typing as tp

            import implements

            from sierra.core.experiment import bindings
            from sierra.core import types, utils

            @implements.implements(bindings.IBatchRunShellCmdsGenerator)
            class BatchShellCmdsGenerator():
                def __init__(self,
                             cmdopts: types.Cmdopts,
                             exp_num: int) -> None:
                    pass

                def pre_batch_cmds(self) -> tp.List[types.ShellCmdSpec]:
                    return []

                def post_batch_cmds(self) -> tp.List[types.ShellCmdSpec]:
                    return []

      .. tab:: ExpShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

         It is used in stage 2 to execute (not generate) shell commands
         per-experiment previously written to a text file using GNU parallel (or
         some other engine of your choice). This includes sets of cmds for:

         - Pre-experiment cmds executed prior to any experimental run being
           executed.

         - Post-experiment cleanup cmds before the next experiment is executed.

         .. IMPORTANT:: The result of ``exec_exp_cmds()`` for engines plugins
                        is ignored, because it doesn't make sense: execution
                        environments execute experiments (DUH), so you don't
                        need to define it.

         This generator corresponds to ``per-exp`` parallelism; see
         :ref:`tutorials/plugin/engine/config` for details.

         .. code-block:: python

            import typing as tp

            import implements

            from sierra.core.experiment import bindings
            from sierra.core import types, utils

            @implements.implements(bindings.IExpRunShellCmdsGenerator)
            class ExpShellCmdsGenerator():
                def __init__(self,
                             cmdopts: types.Cmdopts,
                             exp_num: int) -> None:
                    pass

                def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
                    return []

                def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
                    return []



      .. tab:: ExpRunShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.

         It is used in stage 1 to generate (not execute) the shell commands
         per-experimental run for this engine. These are sets of cmds which:

         - Need to be run before an experimental run.

         - Need to be run to actually execute an experimental run.

         - Need to executed post experimental run to cleanup before the next run
           is started. The generated cmds are written to a text file that GNU
           parallel (or some other engine of your choice) will run in stage 2.

         This generator corresponds to ``per-exp`` parallelism; see
         :ref:`tutorials/plugin/engine/config` for details.

         .. code-block:: python

            import typing as tp
            import pathlib

            import implements

            from sierra.core.experiment import bindings
            from sierra.core.variables import batch_criteria as bc
            from sierra.core import types, utils

            @implements.implements(bindings.IExpRunShellCmdsGenerator)
            class ExpRunShellCmdsGenerator():
                def __init__(self,
                     cmdopts: types.Cmdopts,
                     criteria: bc.BatchCriteria,
                     exp_num: int,
                     n_agents: tp.Optional[int]) -> None:
                     pass

                 def pre_run_cmds(self,
                                  host: str,
                                  input_fpath: pathlib.Path,
                                  run_num: int) -> tp.List[types.ShellCmdSpec]:
                     return []

                 def exec_run_cmds(self,
                                   host: str,
                                   input_fpath: pathlib.Path,
                                   run_num: int) -> tp.List[types.ShellCmdSpec]:
                     return []

             def post_run_cmds(
                        self, host: str, run_output_root: pathlib.Path
                        ) -> tp.List[types.ShellCmdSpec]:
                        return []



#. In ``plugin.py``, you may define ``exec_env_check()`` to check the software
   environment (envvars, PATH, etc.) for this engine plugin prior to
   running anything in stage 2. Since stage 2 can be run in a different
   invocation than stage 1, this hook is provided so that the correct
   environment exists prior to executing anything. This function is optional.

   .. code-block:: python

      import os

      from sierra.core import types

      def exec_env_check(cmdopts: types.Cmdopts):
          """
          Check the software environment (envvars, PATH, etc.) for this engine
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

#. In ``plugin.py``, you may define ``expdef_flatten()``, which can be used to
   flatten nested ``--expdef-template`` files before creating experiments, if
   supported by your chosen :ref:`expdef plugin <plugins/expdef>`. This
   function is optional.

   .. code-block:: python

      def expdef_flatten(exp_def: definition.BaseExpDef) -> definition.BaseExpDef:
          """
          Given an experiment definition, perform engine-specific
          flattening of nested configuration files prior to scaffolding
          the batch experiment.
          """
          pass


.. _tutorials/plugin/engine/prod:

Generating Products
===================

#. In ``plugin.py``, you may define ``exp_duration()``, which can be used to
   retrieve the experiment setup information in later pipeline stages for
   providing nicer X-axis labels for graphs, for example. This function is
   optional.

   .. code-block:: python

      def expsetup_from_def(exp_def: definition.BaseExpDef) -> types.SimpleDict:
          """
          Given an experiment definition, compute the experiment setup
          information. Should contain keys:

          - ``duration`` - Duration in seconds.

          - ``n_ticks_per_sec`` - Ticks per second for controllers/sim.
          """
          pass

A Full Skeleton
===============

.. tabs::

   .. tab:: ``cmdline.py``

      .. literalinclude:: ./cmdline-engine.py
         :language: python

   .. tab:: ``plugin.py``

      .. literalinclude:: plugin.py
         :language: python

   .. tab:: ``generators/engine.py``

      .. literalinclude:: generators.py
         :language: python


Finally--Connect to SIERRA!
===========================

After going through all the sections above and creating your plugin, tell SIERRA
about it by putting ``$HOME/git/plugins/`` on your :envvar:`SIERRA_PLUGIN_PATH`
so that your engine can be selected via ``--engine=engine.matrix``.

.. NOTE:: If your engine supports/requires a new execution environment, head
          over to :ref:`tutorials/plugin/execenv`.
