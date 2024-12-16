.. _tutorials/plugin/exec-env:

===========================================
Creating a New Execution Environment Plugin
===========================================

For the purposes of this tutorial, I will assume you are creating a new HPC
:term:`Plugin` ``HAL``, and the code for that plugin lives in
``$HOME/git/plugins/hpc/HAL``.

If you are creating a new HPC plugin for an existing platform that comes with
SIERRA (e.g., :term:`ARGoS`) you have two options:

#. Following :ref:`tutorials/plugin/platform` to create a new platform
   to add support for your execution environment within the existing platform.

#. Open a pull request for SIERRA with your created HPC plugin to get it into
   the main repo. This should be the preferred option, as most execution
   environment plugins have utility beyond whatever group initially wrote them.

In either case, the steps to actually create the code are below.

Before beginning, create the following filesystem structure in
``$HOME/git/plugins/hpc/HAL``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go.

These files will be populated as you go through the rest of the tutorial.

.. NOTE:: For all things that are optional, if you try to use a part of SIERRA
          requiring functionality you didn't define, you *might* get an obvious
          error, or you might get a crash later on, depending. Please help
          improve this aspect of SIERRA!

Creating The Cmdline Interface
==============================

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


   Used in stages 1-5.

Configuring The Experimental Environment
========================================

#. Define the ``ExpConfigurer`` class in ``plugin.py`` to configure
   :term:`Experiments<Experiment>` in execution environment-specific ways.
   This class is required. It should conform to
   :class:`~sierra.core.experiment.bindings.IExpConfigurer`. It is used in
   stage 1 *after* experiment generation, in case configuration depends on
   the contents of the experiment.

Generating Experiments
======================

Currently, there is no mechanism for including per-execution environment changes
to experiment definitions; this may change in the future.

Executing Experiments
=====================

#. In ``plugin.py``, you may define the ``ExpShellCmdsGenerator`` which is used
   in stages {1, 2} to generate the cmdline to execute
   :term:`Experiments<Experiment>` and :term:`Experimental Runs<Experimental
   Run>`. SIERRA essentially tries to mimic running experiments using a given
   platform as close as possible to running them on the cmdline directly; thus,
   configuring experiments for platform typically involves putting the needed
   shell commands into a "language" that SIERRA understands.

   This class is optional. If it is defined, it should conform to
   :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

   It is used in stage 1 to generate shell commands per-experiment. This
   includes cmds to run prior to any experimental run being executed, and any
   post-experiment cleanup cmds before the next experiment is executed for this
   execution environment.

   .. IMPORTANT:: The result of ``exec_exp_cmds()`` for execution environment
                  plugins is ignored, because it doesn't make sense: platforms
                  execute experiments.

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


Finally--Connect to SIERRA!
===========================

After going through all the sections above and creating your plugin, tell SIERRA
about it by putting ``$HOME/git/plugins`` on your
:envvar:`SIERRA_PLUGIN_PATH`. Then your plugin can be selected as
``--exec-env=hpc.HAL``.

.. NOTE:: Execution environment plugin names have the same constraints as python
   package names (e.g., no dots, so ``HAL.dave`` is not a valid plugin name).
