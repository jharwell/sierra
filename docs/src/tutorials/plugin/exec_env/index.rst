.. _ln-sierra-tutorials-plugin-exec-env:

===========================================
Creating a New Execution Environment Plugin
===========================================

For the purposes of this tutorial, I will assume you are creating a new HPC
:term:`Plugin` ``HAL``, and the code for that plugin lives in
``$HOME/git/plugins/hpc/HAL``.

If you are creating a new HPC plugin for an existing platform that comes with
SIERRA (e.g., :term:`ARGoS`) you have two options:

#. Following :ref:`ln-sierra-tutorials-plugin-platform` to create a new platform
   to add support for your execution environment within the existing platform.

#. Open a pull request for SIERRA with your created HPC plugin to get it into
   the main repo. This should be the preferred option, as most execution
   environment plugins have utility beyond whatever group initially wrote them.

In either case, the steps to actually create the code are below.

Create The Code
===============

Create the following filesystem structure and content in
``$HOME/git/plugins/hpc/HAL``. Each file is required; any number of
additional files can be included.

.. tabs::

   .. tab:: ``plugin.py``

      .. include:: plugin.rst


Connect to SIERRA
=================

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--exec-env=hpc.HAL``.

.. NOTE:: Execution environment plugin names have the same constraints as python
   package names (e.g., no dots).
