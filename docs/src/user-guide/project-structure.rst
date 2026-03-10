.. SPDX-License-Identifier: MIT

.. _user-guide/project-structure:

=================
Project Structure
=================

A SIERRA project is a directory that SIERRA discovers via
:envvar:`SIERRA_PLUGIN_PATH`. This page describes the expected layout of that
directory and the role of each file. For instructions on creating a project from
scratch, see :ref:`tutorials/project/project`.

.. _user-guide/project-structure/layout:

Directory Layout
================

A complete project looks like this:

.. code-block:: text

   myproject/
   ├── .sierraplugin          # magic cookie — marks this as a project plugin
   ├── __init__.py
   ├── cmdline.py             # required: defines --controller and --scenario
   ├── config/
   │   ├── main.yaml          # required: core SIERRA configuration
   │   ├── controllers.yaml   # required: controller graph/template config
   │   ├── graphs.yaml        # optional: graph generation targets
   │   ├── collate.yaml       # optional: data collation targets
   │   └── models.yaml        # optional: analytical model configuration
   ├── generators/
   │   ├── scenario.py        # required: parses --scenario, generates template changes
   │   └── experiment.py      # optional: per-experiment/per-run customisation
   ├── variables/             # optional: project-specific batch criteria
   │   └── my_variable.py
   └── models/                # optional: analytical model implementations
       └── my_model.py

Nothing outside this directory is required. Experiment templates (the
``--expdef-template`` file) live wherever you like and are passed on the command
line; they are not part of the project directory.

.. _user-guide/project-structure/files:

File and Directory Reference
============================

``.sierraplugin``
   Empty marker file that tells SIERRA this directory is a plugin. Required.

``__init__.py``
   Standard Python package marker. Required.

``cmdline.py``
   Defines the ``--controller`` and ``--scenario`` arguments for this project,
   and any other project-specific command-line options. Required for all
   projects. See :ref:`tutorials/plugins/devguide/cmdline`.

``config/main.yaml``
   Core SIERRA configuration: the ``run_metrics_leaf`` key (the subdirectory
   within each run's working directory where output files appear), optional
   library name for ARGoS, and the path to a performance configuration file.
   Required. See :ref:`tutorials/project/config`.

``config/controllers.yaml``
   Declares which controllers the project defines, what template changes each
   one makes, and which graph categories apply to each. Required when running
   stages 3–5. See :ref:`tutorials/project/config/controllers`.

``config/graphs.yaml``
   Declares what graphs to generate in stage 4 (``intra-exp`` and ``inter-exp``
   sections) and what to imagize (``imagize`` section). Optional, but without
   it stage 4 produces nothing. See :ref:`plugins/prod/graphs`.

``config/collate.yaml``
   Declares which output files and columns to collate across runs within each
   experiment. Used by :ref:`plugins/proc/collate`. Optional.

``config/models.yaml``
   Declares which analytical models to run in stage 3 and what their targets
   are. Used by :ref:`plugins/proc/modelrunner`. Optional.

``generators/scenario.py``
   Parses the ``--scenario`` string and produces the template modifications
   needed to configure each experimental run's context. Required.
   See :ref:`tutorials/project/generators`.

``generators/experiment.py``
   Extends per-experiment and per-run configuration beyond what the scenario
   generator provides. Optional. See :ref:`tutorials/project/generators`.

``variables/``
   Project-specific batch criteria and other variable definitions. Files here
   are importable as ``<project>.variables.<name>`` and can be passed directly
   to ``--batch-criteria``. Optional. See :ref:`tutorials/project/new-bc`.

``models/``
   Analytical model implementations. Must contain a ``.sierraplugin`` marker
   and an ``__init__.py`` exporting a ``sierra_models()`` function.
   Optional. See :ref:`plugins/proc/modelrunner`.

.. _user-guide/project-structure/templates:

Experiment Templates
====================

The ``--expdef-template`` file is *not* inside the project directory. It is a
standalone configuration file (XML, JSON, YAML, or a ROS launch file) that
SIERRA modifies in stage 1 to produce per-experiment inputs. Keep it wherever
is convenient for your workflow — typically alongside other experiment assets in
a separate ``exp/`` directory:

.. code-block:: text

   myrepo/
   ├── exp/
   │   └── template.xml       # passed as --expdef-template
   └── projects/
       └── myproject/         # on SIERRA_PLUGIN_PATH

See :ref:`user-guide/experiment-templates` for what the template must contain
and how SIERRA modifies it.

.. _user-guide/project-structure/outputs:

Where Outputs Go
================

SIERRA writes nothing into the project directory. All outputs — generated
experiment inputs, raw run outputs, statistics, graphs — go under
:ref:`--sierra-root<src/reference/cli:sierra---sierra-root>`, organized by
project, controller, scenario, and batch criteria. See
:ref:`concepts/run-time-tree` for the full output directory structure.

.. plantuml::
   :caption: The three separate filesystem locations SIERRA works with.
             The project directory and template are user-managed inputs;
             sierra-root is entirely SIERRA-managed output.

   !theme cerulean
   skinparam backgroundColor transparent
   skinparam defaultFontSize 16
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold

   skinparam defaultFontName sans-serif
   skinparam defaultFontStyle bold
   skinparam ArrowThickness 3
   skinparam componentBorderThickness 3
   skinparam packageBorderThickness 3

   package "Your repository" {
     component "Project directory\n(on SIERRA_PLUGIN_PATH)\n\ncmdline.py\nconfig/\ngenerators/\nvariables/" as PROJ
     component "Experiment template\n(--expdef-template)\n\ntemplate.xml / .json\n.yaml / .launch" as TMPL
   }

   component "sierra-root\n(--sierra-root)\n\nAll generated inputs,\nraw outputs, statistics,\nand graphs land here.\nSIERRA manages this entirely." as ROOT #d6eaf8

   PROJ --> ROOT : "configures stage 1–5\nbehaviour"
   TMPL --> ROOT : "modified by stage 1\nto produce exp inputs"
