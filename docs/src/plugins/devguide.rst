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

Configurability
===============

Some plugins require configuration. Plugins can provide configurability via
cmdline arguments, YAML config, or some combination thereof. If a configuration
item is present in *both* cmdline arguments and YAML config, it is up to the
plugin to decide which takes precedence if both are present. This is to enable
multiple use cases.
