.. _ln-tutorials-plugin-hpc:

=========================
Creating a New HPC Plugin
=========================

For the purposes of this tutorial, I will assume you are creating a new HPC
:term:`Plugin` ``HAL``, and the code for that plugin lives in
``$HOME/git/plugins/hpc/HAL``.

If you are creating a new HPC plugin for an existing platform that comes with
SIERRA (e.g., :term:`ARGoS`) you have two options:

#. Following :ref:`ln-tutorials-plugin-platform` to create a new platform to
   add support for your execution environment within the existing platform.

#. Open a pull request for SIERRA with your created HPC plugin to get it into
   the main platform path. This should be the preferred option, as most
   computational platform definitions have utility beyond whatever group
   initially wrote them.

In either case, the steps to actually create the code are below.

Create The Code
===============

#. Create the following filesystem structure in ``$HOME/git/plugins/hpc/HAL``:

   .. tabs::

      .. code-tab::  python ``plugin.py``

         import typing as tp
         import argparse
         from sierra.core import types
         from sierra.core import plugin_manager as pm

         class CmdoptsConfigurer():
            def __init__(self, platform: str) -> None:
                """
                Arguments:

                    platform: Value of ``--platform``. Used to supported
                              multiple HPC execution environments for the same
                              platform, which may require different
                              configuration.

                """
                pass

            def __call__(self, args: argparse.Namespace) -> None:
                """
                Configure SIERRA for HPC by reading environment variables and
                modifying the parsed cmdline arguments (namespace object) as
                needed.

                """

         class LaunchCmdGenerator():
            def __init__(self, platform: str) -> None:
                """
                Arguments:

                    platform: Value of ``--platform``. Used to supported
                              multiple HPC execution environments for the same
                              platform, which may require different
                              configuration.

                """
                pass

            def __call__(self, input_fpath: str) -> str:
                """
                Generate the command to launch your code within your new
                execution environment, given the path to an experimental run
                input file. Generally, this should just use SIERRA's
                plugin manager to dispatch the generation to the specific
                platform you are targeting via
                ``platform.<target>.launch_cmd_generate()`` you in order
                to avoid having the same generation code copy-pasted for
                multiple execution environments. However, there may be cases
                where you need additional logic, hence this class.


                Depending on your environment, you may want to use SIERRA_ARCH
                (either in this function or your dispatch)to chose a version of
                your simulator compiled for a given architecture for maximum
                performance.
                """
                # As an example
                module = pm.SIERRAPluginManager().get_plugin_module(self.platform)
                return module.launch_cmd_generate('hpc.HAL', input_fpath)

         class GNUParallelCmDGenerator():
            """
            Given a dictionary containing job information, generate the cmd to
            correctly invoke GNU Parallel on the HPC environment. The job
            information dictionary contains:

            - ``jobroot_path`` - The root directory GNU parallel will run in.

            - ``cmdfile_path`` - The absolute path to the file containing the
                                 launch commands to execute.

            - ``joblog_path`` - The absolute path to the log file that GNU
                                 parallel will log job progress to.

            - ``exec-resume`` - Is this invocation resuming a previously
                                 failed/incomplete run?

            - ``n_jobs`` - How many jobs to run in parallel.

            """

            def __call__(self, parallel_opts: tp.Dict[str, tp.Any]) -> str:

        class GNUParallelCmDGenerator():
            """
            Given the parsed cmdline options and the previously generated launch
            cmd for the experimental run, generate additional arguments/wrapper
            cmds/environment variables necessary to invoke the simulator to
            capture visual data (e.g., frames). If your HPC does not support
            this, return the launch cmd unmodified.

            """
            def __call__(self,
                         cmdopts: types.Cmdopts,
                         launch_cmd: str) -> str:


    You can have as many other files of whatever type you want in your plugin
    directory to support the required functionality--they will be ignored by
    SIERRA.

Connect to SIERRA
=================

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--exec-env=hpc.HAL``.
