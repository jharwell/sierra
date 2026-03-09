..
   Copyright 2026 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _arch/plugin-system:

=============
Plugin System
=============

This page covers three aspects of the plugin system not explained elsewhere:
the distinction between infrastructure plugins and the project plugin, why your
available command line flags depend on which plugins you select, and how to use
that as a guide to where changes belong.

For the full list of plugin types and what each does, see :ref:`plugins`. For
which plugins are active in each pipeline stage, see :ref:`usage/pipeline`. For
how to write a plugin, see :ref:`plugins/devguide`.

Infrastructure Plugins vs. the Project Plugin
==============================================

All plugins selected via :ref:`--engine<src/reference/cli:sierra-cli---engine>`,
:ref:`--execenv<src/reference/cli:sierra-cli---execenv>`, :ref:`--expdef<src/reference/cli:sierra-cli---expdef>`,
:ref:`--storage<src/reference/cli:sierra-cli---storage>`, :ref:`--proc<src/reference/cli:sierra-cli---proc>`,
:ref:`--prod<src/reference/cli:sierra-cli---prod>`, and :ref:`--compare<src/reference/cli:sierra-cli---compare>` are
*infrastructure* plugins — they are either built into SIERRA or provided by an
engine vendor, and they are interchangeable in the sense that you can swap one
for another without touching your research code.

The :ref:`--project<src/reference/cli:sierra-cli---project>` plugin is different. It is your code:
batch criteria, controller..  and scenario definitions, graph configuration, and
any processing hooks specific to your output data. Everything that makes your
experiments distinct lives there.

A consequence is that project plugins are not portable across engines. Running
the same research on both ARGoS and ROS1+Gazebo requires two project plugins,
one targeting each engine, though they can share Python code via ordinary
imports. See :ref:`tutorials/project/project` for details.

Why Your Available Flags Depend on Which Plugins You Select
============================================================

SIERRA does not have a fixed set of command line options. Before parsing any
experiment arguments, SIERRA loads the plugins you have selected and each one
contributes its own argument groups to the parser. This is why ``sierra-cli
--help`` output changes depending on what :ref:`--engine<src/reference/cli:sierra-cli---engine>`
and :ref:`--execenv<src/reference/cli:sierra-cli---execenv>` you pass.

At ``--log-level=DEBUG`` you can watch this happen::

  2025-08-16 17:19:40 INFO  sierra.main - Dynamically building cmdline from selected plugins
  2025-08-16 17:19:40 DEBUG sierra.main - Loaded --execenv=hpc.local cmdline
  2025-08-16 17:19:40 DEBUG sierra.main - Loaded --engine=starfleet.enterprise cmdline
  2025-08-16 17:19:40 DEBUG sierra.main - Loaded --proc=proc.statistics cmdline
  2025-08-16 17:19:40 DEBUG sierra.main - Loaded --prod=prod.graphs cmdline

Once all plugins are loaded, the full cmdline is parsed and each plugin's
``to_cmdopts()`` function contributes to a shared ``cmdopts`` dictionary that
is passed through the pipeline::

  2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --engine=starfleet.enterprise
  2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --execenv=hpc.local
  2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --proc=proc.statistics
  2025-08-16 17:19:40 DEBUG sierra.core.pipeline.pipeline - Updating cmdopts from --prod=prod.graphs

The practical implication: if a flag you expect is missing from ``--help``, the
plugin that defines it is not being loaded. Check that the plugin name is spelled
correctly and that its directory is on :envvar:`SIERRA_PLUGIN_PATH`.

Where Changes Belong
====================

Because responsibility is divided clearly across layers, most problems have an
obvious home:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - To change this...
     - ...look here

   * - How :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` files are
       modified to produce per-experiment inputs
     - The engine plugin (:ref:`--engine<src/reference/cli:sierra-cli---engine>`)

   * - How runs are launched — the actual shell command
     - The engine plugin (:ref:`--engine<src/reference/cli:sierra-cli---engine>`)

   * - How many runs execute in parallel and on which machines
     - The execution environment plugin (:ref:`--execenv<src/reference/cli:sierra-cli---execenv>`)

   * - Which environment variables are forwarded into child processes
     - The execution environment plugin
       (:ref:`--execenv<src/reference/cli:sierra-cli---execenv>`); see also :ref:`plugins/execenv`.

   * - Which :ref:`--batch-criteria<src/reference/cli:sierra-cli---batch-criteria>`,
       ``--controller``, and ``--scenario`` values are valid
     - The project plugin (:ref:`--project<src/reference/cli:sierra-cli---project>`)

   * - Which graphs are generated and how they are configured
     - ``graphs.yaml`` in the project plugin
       (:ref:`--project<src/reference/cli:sierra-cli---project>`)

   * - What happens to raw output data in stage 3
     - The active processor plugins (:ref:`--proc<src/reference/cli:sierra-cli---proc>`)

   * - What products are generated in stage 4
     - The active product plugins (:ref:`--prod<src/reference/cli:sierra-cli---prod>`)

   * - The pipeline structure, stage ordering, or filesystem layout
     - These are fixed by the SIERRA core and are not overridable by plugins
