.. _ln-sierra-tutorials-plugin-platform:

==============================
Creating a New Platform Plugin
==============================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Platform` :term:`Plugin` ``matrix``, and the code for that plugin lives
in ``$HOME/git/plugins/platform/matrix``.

If you are creating a new platform, you have two options.

#. Create a stand-alone platform, providing your own definitions for all of the
   necessary functions/classes below.

#. Derive from an existing platform by simply calling the "parent" platform's
   functions/calling in your derived definitions except when you need to
   actually extend them (e.g., to add support for a new HPC plugin)

In either case, the steps to actually create the code are below.

Create the Code
===============

Create the following filesystem structure and content in
``$HOME/git/plugins/platform/matrix``. Each file is required; any number of
additional files can be included.

.. tabs::

   .. tab:: ``plugin.py``

      .. include:: plugin.rst

   .. tab:: ``cmdline.py``

      .. include:: cmdline.rst

   .. tab:: ``generators/platform_generators.py``

      .. include:: generators.rst


Connect to SIERRA
=================

#. Put ``$HOME/git/plugins/platform/matrix`` on your
   :envvar:`SIERRA_PLUGIN_PATH` so that your platform can be selected via
   ``--platform=platform.matrix``.

.. NOTE:: Platform names have the same constraints as python package names
   (e.g., no dots).
