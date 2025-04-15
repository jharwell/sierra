.. _usage/pipeline:

===============
SIERRA Pipeline
===============

This page provides a more detailed overview of its pipeline, expanding on the
architectural diagram shown :ref:`here <main>`, as well as deep-dives for what
happens in each stage. For reference, here is the high-level view of the
pipeline:

.. figure:: /figures/architecture.png

   SIERRA architecture, organized by pipeline stage, left to right. High-level
   inputs/outputs and active plugins and shown for each stage. “...”  indicates
   areas of further extensibility and customization via new plugins. “Host
   machine” indicates the machine SIERRA was invoked on.


Stage 1: Experiment Generation
==============================

Detailed Overview
-----------------

Experiments using the scientific method have an independent variable whose
impact on results are measured through a series of trials. SIERRA allows you to
express this as a research query on the command line, and then parses your query
to make changes to a template input file to generate launch commands and
experimental inputs to operationalize it. Switching from targeting platform A
(e.g., ARGoS) to platform B (e.g., ROS1+Gazebo) is as easy as changing a single
command line argument. SIERRA handles the "backend" aspects of defining
experimental inputs allowing you to focus on their *content*, rather than the
mechanics of how to turn the content into something that can be executed.

The following plugins are active in this stage:

.. list-table::
   :header-rows: 1

   * - Plugin

     - Used for


   * - :ref:`Platform <plugins/platform>`

     - Handling cmdline arguments needed by the selected platform, assisting
       with experimental input generation.

   * - :ref:`Experiment definition <plugins/expdef>`

     - Generating inputs for the selected :term:`Platform` which can be executed
       in stage 2 from the ``--expdef-template`` experiment template file.

   * - :ref:`Execution environment <plugins/exec-env>`

     - Assisting with experimental input generation so experiments can be
       executed during stage 2.

See also:

- :ref:`support-matrix`

- :ref:`usage/cli`

Part of default pipeline. For a deep dive into design and functionality, see
the :ref:`deep dive <usage/deep-dive/stage1>`.

Stage 2: Experiment Execution
=============================

SIERRA runs a previously generated :term:`Batch Experiment`. Exactly which batch
experiment SIERRA runs is determined by:

- ``--controller``
- ``--scenario``
- ``--sierra-root``
- ``--expdef-template``
- ``--batch-criteria``

Thus, these arguments must be the same between stage{1,2} if you want to execute
the experiments you generated.

SIERRA currently supports two types of execution environments: simulators and
real robots, which are handled seamlessly. For simulators, SIERRA will run
multiple experimental runs from each experiment in parallel if possible. Similar
to stage 1, switching between execution environments is as easy as changing a
single command line argument.

The following plugins are active in this stage:

.. list-table::
   :header-rows: 1

   * - Plugin

     - Used for

   * - :ref:`Platform <plugins/platform>`

     - Performing validation of execution environment before running experiments
       in stage 2.

   * - :ref:`Execution environment <plugins/exec-env>`

     - Executing shell commands to run the experiments generated during stage 2.

See also:

- :ref:`support-matrix`

Part of default pipeline.

Stage 3: Experiment Post-Processing
===================================

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data. SIERRA post-processes experimental results
after running the :term:`Batch Experiment` according to the set of active
processing plugins.

The following plugins are active in this stage:

.. list-table::
   :header-rows: 1

   * - Plugin

     - Used for


   * - :ref:`Platform <plugins/platform>`

     - Extracting any information needed from the platform in order to assist
       with processing experimental outputs.

   * - :ref:`Storage <plugins/storage>`

     - Reading/writing raw experimental outputs to/from the filesystem during
       processing.

   * - :ref:`Processors <plugins/proc>`

     - Processing raw experimental outputs into a form suitable for generating
       deliverables in stage 4.

Some parts of this stage are done in parallel by default. Part of default
pipeline.

Stage 4: Deliverable Generation
===============================

SIERRA can generate many deliverables from the processed experimental results
automatically (independent of the platform/execution environment!), thus greatly
simplifying reproduction of previous results if you need to tweak a given graph
(for example).

SIERRA also has a rich model framework allowing you to run arbitrary models,
generate data, and plot it on the same figure as empirical results,
automatically. See :ref:`tutorials/project/models` for details.

The following plugins are active in this stage:

.. list-table::
   :header-rows: 1

   * - Plugin

     - Used for

   * - :ref:`Platform <plugins/platform>`

     - Extracting any information needed from the platform in order to assist
       with generating deliverables, such as the # agents for a given
       :term:`Experimental Run`.

   * - :ref:`Deliverable Generators <plugins/proc>`

     -

        .. TODO:: The hard-corded deliverable generation options below will
                  eventually be replaced by a proper set of plugins. Right now
                  it is plugin-ish, in the since there are various hooks to
                  extend/customize.

        - Camera-ready linegraphs, heatmaps, 3D surfaces, and scatterplots
          directly from averaged/statistically processed experimental data using
          matplotlib.

        - Videos built from frames captured during simulation or real robot
          operation.

        - Videos built from captured experimental output .csv files.

        - Processing raw experimental outputs into a form suitable for
          generating deliverables in stage 4.

For some examples, see the "Generating Deliverables" section of
:xref:`2022-aamas-demo`. See :ref:`usage/rendering` for details about
rendering capabilities.

Part of default pipeline.

Stage 5: Graph Generation for Controller/Scenario Comparison
============================================================

SIERRA can perform additional graph generation *AFTER* graph generation for
batch experiments has been run. This is extremely useful for generating graphs
which can be dropped immediately into academic papers/customer reports without
modification.

The following plugins are active in this stage:

.. list-table::
   :header-rows: 1

   * - Plugin

     - Used for

   * - :ref:`Platform <plugins/platform>`

     - Extracting any information needed from the platform in order to assist
       with generating comparative deliverables, such as the # agents for a
       given :term:`Experimental Run`.

   * - :ref:`Comparative Generators <plugins/comparators>`

     -

        .. TODO:: The hard-corded options for comparative deliverable generation
                  below will eventually be replaced by a proper plugin.

        - Different agent control algorithms which have all been run in the same
          ``--scenario``. See :ref:`usage/stage5/intra-scenario` for details.

        - A single ``--controller`` across multiple scenarios. See
          :ref:`usage/stage5/inter-scenario` for details.



Not part of default pipeline.

Running The Pipeline
====================

When invoked SIERRA will run one or more stages of its execution path, as
specified via ``--pipeline`` on the cmdline. Only the first 4 pipeline stages
will run by default.
