..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/devguide:

========================
Plugin Development Guide
========================

The page details some general guidelines that all SIERRA plugins should follow
for maximum compatibility and usability, as well as tutorials for developing
plugins common to all types.

Naming
======

All plugins should have names which don't conflict with those in the SIERRA
core. This is in line with the Principle of Least Surprise. If you need/want to
override some aspect of functionality for a built-in SIERRA plugin, create a new
plugin with a new name, and use that.

Furthermore, plugin names have the same constraints as python package
names. E.g., no dots, so ``foo.bar`` is not a valid plugin name.

.. _plugins/devguide/schemas:

Schemas
=======

Schemas define how SIERRA recognizes a plugin as opposed to just a python
package.  All plugins must adhere to one of the schemas below; each plugin
defines the necessary functionality which must be present *within* the plugin
for it to be valid.

.. NOTE:: You can add any number of additional defaulted arguments to callback
          functions; this is particularly useful in reusing code across
          plugins.

The following schemas are supported, and are checked in order:

#.

   - In a directory on :envvar:`SIERRA_PLUGIN_PATH`, there is a
     ``.sierraplugin`` file.

   - In a directory on :envvar:`SIERRA_PLUGIN_PATH`, there is a
     ``plugin.py`` file.

   - Within the ``__init__.py`` in that directory there is a
     ``sierra_plugin_type()`` function which returns one of the following
     strings:

     - ``"pipeline"``

     - ``"project"``

#.
   - In a directory on :envvar:`SIERRA_PLUGIN_PATH`, there is a
     ``.sierraplugin`` file.

   - Within the ``__init__.py`` in that directory there is a
     ``sierra_plugin_type()`` function which returns one of the following
     strings:

     - ``"pipeline"``

     - ``"project"``

     - ``"model"``

   - If the plugin type is ``"pipeline"``, within the ``__init__.py`` there is a
     ``sierra_plugin_module()`` function which returns the name of the python
     file in the directory which contains the plugin functionality, sans the
     ``.py`` extension, which is implied.

   - If the plugin type is ``"model"``, within the ``__init__.py`` there is a
     ``sierra_models()`` function with the following signature::

       import typing as tp

       def sierra_models(model_type: str) -> tp.List[str]:
           """Return a list of model names as python paths for the specified
           "intra" or "inter" experiment model type. See
           :ref:`plugins/proc/modelrunner` for more details about this function.
           """

Configurability
===============

Some plugins require configuration. Plugins can provide configurability via
cmdline arguments, YAML config, or some combination thereof. If a configuration
item is present in *both* cmdline arguments and YAML config, it is up to the
plugin to decide which takes precedence if both are present. This is to enable
multiple use cases.

Plugins should respect all core SIERRA cmdline arguments, as well as all
general-purpose arguments for all stages the plugin can be used in.

.. _plugins/devguide/cmdline:

Extending the SIERRA Cmdline For Your Plugin
============================================

This tutorial covers how add cmdline options for a new plugin of any type to
SIERRA.

#. Create ``cmdline.py`` in your plugin directory alongside your ``plugin.py``
   file (or whatever the main plugin file is called).

#. Create the ``build()`` function, which should return an instance of
   :class:`~sierra.plugins.PluginCmdline`::

      def build(
          parents: tp.List[argparse.ArgumentParser], stages: tp.List[int]
      ) -> PluginCmdline:
          """
          Get a cmdline parser supporting the ``proc.collate`` processing plugin.
          """
          cmdline = PluginCmdline(parents, stages)
          cmdline.multistage.add_argument(
              "--foo-arg",
              help="blah blah blah",
              action="store_true",
          )
          # More arguments
          return cmdline

   There are 6 parser groups available for you to add arguments to:

   - ``multistage`` - Arguments which are used in multiple pipeline stages.

   - ``stage1`` - Arguments only used in stage 1.

   - ``stage2`` - Arguments only used in stage 2.

   - ``stage3`` -  Arguments only used in stage 3.

   - ``stage4`` - Arguments only used in stage 4.

   - ``stage5`` - Arguments only used in stage 5.

   These are provided to give cmdline parsing more structure, and to make
   creating docs directly from ``argparse`` via sphinx easy.

   .. NOTE:: You can also create a cmdline *class* by inheriting from
             :class:`~sierra.plugins.PluginCmdline`. If you do this route, you will
             define ``init_XX()`` functions to populate the parser groups
             described above. All of these functions are optional; see class
             docs for details.

#. Create the ``to_cmdopts()`` function.  This function creates a dictionary
   from the parsed cmdline arguments which SIERRA uses to create an internal
   ``cmdopts`` dictionary used throughout. Keys can have any name, though in
   general it is best to make them the same as the name of the argument
   (principle of least surprise)::

     def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
        return {
            "foo": args.foo_arg,
        }

#. Try out your new cmdline! SIERRA should pick it up automatically. For
   example, if you have created a cmdline for an ``--engine`` plugin available
   as ``starfleet.enterprise``, if you set ``--log-level=DEBUG`` you should see
   something like this in SIERRA's output::

     2025-08-16 17:19:40 INFO sierra.main - Dynamically building cmdline from selected plugins
     2025-08-16 17:19:40 DEBUG sierra.main - Loaded --execenv=hpc.local cmdline
     2025-08-16 17:19:40 DEBUG sierra.main - Loaded --engine=starfleet.enterprise cmdline
     2025-08-16 17:19:40 DEBUG sierra.main - Loaded --proc=proc.statistics cmdline
     2025-08-16 17:19:40 DEBUG sierra.main - Loaded --prod=prod.graphs cmdline

   and then later when SIERRA is building the ``cmdopts`` dictionary::

     2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --engine=starfleet.enterprise
     2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --execenv=hpc.local
     2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --proc=proc.statistics
     2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --prod=prod.graphs

   If you don't see similar lines for your plugin, set ``--log-level=TRACE`` and
   debug from there.

#. Setup documentation generation by adding ``sphinx_cmdline_XX()`` functions,
   where ``XX`` is one of
   ``{stage1,stage2,stage3,stage4,stage5,multistage}``. These are simple hooks
   which will allow you to generate CLI documentation directly from ``argparse``
   configuration via sphinx. So you might have::

     def sphinx_cmdline_multistage():
         return build(None, [3, 4, 5]).parser

   in ``cmdline.py`` for a cmdline that contains arguments for stages
   {3,4,5}. Then, you can do::

     .. argparse::
        :filename: /path/to/plugin/cmdline.py
        :func: sphinx_cmdline_multistage
        :prog: sierra-cli

   in your documentation to generate some nice docs. This step is optional but
   recommended.


Special Cases
-------------

There are some small differences between adding options for say a ``--project``
plugin vs. a ``--engine`` vs. any other plugin type; those are called out below.

.. tabs::

   .. group-tab::  Projects

      Must define the ``--scenario`` and ``--controller`` cmdline arguments to
      interact with the SIERRA core. Note that values for these cannot contain
      ``+``, as that is a reserved character for SIERRA directory paths.

      .. NOTE:: The ``--scenario`` argument can be used to encode the arena
                dimensions used in an experiment; this is one of two ways to
                communicate to SIERRA that size of the experimental arena for
                each :term:`Experiment`. See :ref:`req/exp/arena-size` for more
                details.
