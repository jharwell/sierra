..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/devguide:

========================
Plugin Development Guide
========================

The page details some general guidelines that all SIERRA plugins should follow
for maximum compatibility and usability.

Naming
======

All plugins should have names which don't conflict with those in the SIERRA
core. This is in line with the Principle of Least Surprise. If you need/want to
override some aspect of functionality for a built-in SIERRA plugin, create a new
plugin with a new name, and use that.

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
     ``plugin.py`` file.

   - Within the ``__init__.py`` in that directory there is a
     ``sierra_plugin_type()`` function which returns one of the following
     strings:

     - ``"pipeline"``

     - ``"project"``

     - ``"model"``

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


Configurability
===============

Some plugins require configuration. Plugins can provide configurability via
cmdline arguments, YAML config, or some combination thereof. If a configuration
item is present in *both* cmdline arguments and YAML config, it is up to the
plugin to decide which takes precedence if both are present. This is to enable
multiple use cases.

Plugins should respect all core SIERRA cmdline arguments, as well as all
general-purpose arguments for all stages the plugin can be used in.
