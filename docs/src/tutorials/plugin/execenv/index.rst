.. _tutorials/plugin/execenv:

===========================================
Creating a New Execution Environment Plugin
===========================================

Preliminaries
=============

For the purposes of this tutorial, I will assume you are creating a new HPC
:term:`Plugin` ``HAL``, and the code for that plugin lives in
``$HOME/git/plugins/hpc/HAL``.

If you are creating a new plugin for an existing engine that comes with SIERRA
(e.g., :term:`ARGoS`) you have two options:

#. Following :ref:`tutorials/plugin/engine` to create a new engine
   to add support for your execution environment within the existing engine.

#. Open a pull request for SIERRA with your created plugin to get it into the
   main repo. This should be the preferred option, as most execution environment
   plugins have utility beyond whatever group initially wrote them.

If you are creating a new execution environment plugin for a new engine, then
you can ignore the above.  Before beginning, see the :ref:`plugins/devguide` for
a general overview of creating a new plugin.

Create the following filesystem structure in ``$HOME/git/plugins/hpc/HAL``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new engine doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

.. NOTE:: For all things that are optional, if you try to use a part of SIERRA
          requiring functionality you didn't define, you *might* get an obvious
          error, or you might get a crash later on, depending. Please help
          improve this aspect of SIERRA!


Creating The Cmdline Interface
==============================

#. Create additional cmdline arguments for the new execution environment by
   following :ref:`plugins/devguide/cmdline`.

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


   Used in stages 1-4.

Configuring The Experimental Environment
========================================

Currently, there is no mechanism for including per-execution environment changes
to experiment definitions; this may change in the future.

Generating Experiments
======================

Currently, there is no mechanism for including per-execution environment changes
to experiment definitions; this may change in the future.

Running Experiments
===================

#. In ``plugin.py``, you may define the following classes which are used
   in stages {1, 2} to generate the shell cmd(s) to execute
   :term:`Experiments<Experiment>` and :term:`Experimental Runs<Experimental
   Run>`. SIERRA essentially tries to mimic running experiments using a given
   engine as close as possible to running them on the cmdline directly; thus,
   configuring experiments for engine typically involves putting the needed
   shell commands into a "language" that SIERRA understands.

   .. tabs::

      .. tab:: ExpRunShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.

         It is used in stage 1 to generate (not execute) the shell commands
         per-experimental run for this execution environment. These are sets of
         cmds which:

         - Need to be run before an experimental run.

         - Need to be run to actually execute an experimental run.

         - Need to executed post experimental run to cleanup before the next run
           is started. The generated cmds are written to a text file that GNU
           parallel (or some other engine of your choice) will run in stage 2.

      .. tab:: ExpShellCmdsGenerator

         This class is optional. If it is defined, it should conform to
         :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

         It is used in stage 2 to execute (not generate) shell commands
         per-experiment previously written to a text file using GNU parallel (or
         some other engine of your choice). This includes sets of cmds for:

         - Pre-experiment cmds executed prior to any experimental run being
           executed.

         - Cmds to execute the experiment for each experimental run.

         - Post-experiment cleanup cmds before the next experiment is executed.

#. In ``plugin.py``, you may define ``exec_env_check()`` to check the software
   environment (envvars, PATH, etc.) for this execution environment plugin prior
   to running anything in stage 2. Since stage 2 can be run in a different
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


A Full Skeleton
===============

.. tabs::

   .. tab:: ``plugin.py``

      .. literalinclude:: plugin.py
         :language: python


Finally--Connect to SIERRA!
===========================

After going through all the sections above and creating your plugin, tell SIERRA
about it by putting ``$HOME/git/plugins`` on your
:envvar:`SIERRA_PLUGIN_PATH`. Then your plugin can be selected as
``--execenv=hpc.HAL``. Note that if you change what directory you put on the
plugin path, how you selected your engine will change. E.g., if you put
``$HOME/git/`` on :envvar:`SIERRA_PLUGIN_PATH`, then your new plugin will be
accessible via ``plugins.engine.HAL`` instead.

Additional Notes
================

All execution-environment-specific outputs should be logged to
``<batchroot>/scratch``. This keeps them separate from experimental
inputs/outputs, and makes the :ref:`usage/run-time-tree` much more modular at
all levels.
