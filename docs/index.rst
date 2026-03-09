.. _main:

===========================================================================
SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)
===========================================================================

SIERRA is a command-line framework for running **large-scale, reproducible
computational experiments**.  It automates the full experimental workflow:
generating experiment inputs, executing experiments across heterogeneous
computing environments, collecting results, processing data, and producing
analysis artifacts such as plots, videos, and comparative summaries.

SIERRA emphasizes **reproducibility**, **automation**, and **reuse**, allowing
researchers to focus on experimental design rather than infrastructure,
scripts, and environment management.

Typical use cases include robotics simulation studies, ML hyperparameter
sweeps, large parameter studies in scientific computing, and automated
benchmarking pipelines.

Quick Paths
===========

.. grid:: 4
   :gutter: 2

   .. grid-item-card:: 🚀 Run an Experiment
      :link: getting-started/trial
      :link-type: ref
      :class-card: sd-border-1

      Try SIERRA immediately using the built-in sample project.

   .. grid-item-card:: 💡 Understand the Model
      :link: concepts/overview
      :link-type: ref
      :class-card: sd-border-1

      Learn how experiments, batch criteria, the pipeline, dataflow, and the
      runtime tree work together.

   .. grid-item-card:: 📐 Grok the Architecture
      :link: arch
      :link-type: ref
      :class-card: sd-border-1

      The execution model, plugin system internals, and deep-dive
      design notes.

   .. grid-item-card:: 🔌 Extend SIERRA
      :link: tutorials/plugins/devguide
      :link-type: ref
      :class-card: sd-border-1

      Add new engines, storage formats, processors, and analysis tools.


System Overview
===============

SIERRA organizes experimentation as a **multi-stage pipeline**
(see :ref:`concepts/pipeline`) that transforms experiment templates into
comparable experimental results.

.. figure:: figures/architecture.png
   :align: center
   :width: 100%

   SIERRA architecture organized by pipeline stage (left to right). Each stage
   consumes artifacts produced by the previous stage and generates new artifacts
   that advance the experiment toward final results and comparisons.

SIERRA automates the design, execution, and analysis of large experimental
studies. Rather than manually configuring and running experiments, users define
an **experiment template**, and SIERRA transforms that template into a complete
experimental workflow.

The pipeline begins by **generating experiment inputs** from a user-provided
template. These inputs describe individual experiment instances, typically
expressed as structured configuration files such as XML, JSON, or YAML.  The
exact format is determined by experiment-definition plugins associated with the
selected execution engine.

Next, SIERRA **executes the experiments** using an :ref:`engine plugin
<plugins/engine>`. Engines encapsulate the logic required to run experiments in
a particular environment, such as a simulator, robotics platform, or cluster
environment.  Experiments may run locally, on HPC systems, or on physical
hardware depending on the configured execution environment.

After execution completes, SIERRA **processes raw experimental outputs** into
standardized datasets suitable for analysis and aggregation.  Processor plugins
extract metrics, restructure datasets, and convert data into analysis-ready
representations.

The pipeline then **generates experiment products**, such as plots, videos,
summaries, or structured reports.

Finally, SIERRA can **compare products across experimental configurations**.
Comparator plugins produce comparative graphs and summaries that highlight
differences between experiment conditions and support systematic evaluation of
experimental hypotheses.

Across all stages, SIERRA uses a **plugin architecture** (see
:ref:`plugins`). Engines, input formats, processors, product generators, and
comparators are implemented as interchangeable plugins.  This design allows the
framework to support many different simulation platforms, data formats, and
analysis workflows without modifying the core system.

Each stage also interacts with **computing resources** appropriate to the
task. Input generation and analysis typically run on a host machine, while
experiment execution may use local systems, clusters, or physical robots
depending on the configured engine.

Together, these stages form a flexible experimental pipeline that supports
automated, reproducible experimentation across a wide range of domains.

Getting Started
===============

Most users need to integrate their own code with SIERRA before running
experiments, unless the :term:`Engine` they are targeting is already built into
SIERRA (see :ref:`here <plugins/engine>` for list). The typical path is:

.. grid:: 4
   :gutter: 2

   .. grid-item-card:: 1. Verify Installation
      :link: getting-started/trial
      :link-type: ref
      :class-card: sd-border-1

      Run the built-in sample project to confirm everything works.

   .. grid-item-card:: 2. Configure Your Project
      :link: tutorials/project/project
      :link-type: ref
      :class-card: sd-border-1

      Integrate your codebase and experiment definitions with SIERRA.

   .. grid-item-card:: 3. Write Plugins
      :link: tutorials/plugins/devguide
      :link-type: ref
      :class-card: sd-border-1

      Add an engine, storage format, or execution environment.

   .. grid-item-card:: 4. Run Experiments
      :link-type: ref
      :class-card: sd-border-1

      Execute your first real batch experiment and collect results.

SIERRA In The Wild
==================

SIERRA has been used across a range of published research in swarm robotics,
multi-robot systems, and ODE-based modeling — demonstrating its flexibility
across simulation platforms, scale, and experimental designs.

Papers
------

**Swarm Robotics & Collective Behaviour**

- :xref:`Harwell2021a-metrics`
- :xref:`Harwell2020a-demystify`
- :xref:`Harwell2019a-metrics`
- :xref:`White2019-social`

**Modelling & Task Allocation**

- :xref:`Harwell2022b-ode`
- :xref:`Chen2019-battery`

Demos
-----

- :xref:`2022-aamas-demo`

.. note::

   Using SIERRA in your research? See :ref:`reference/citing` for BibTeX
   entries and version-specific DOI badges for reproducibility.


.. toctree::
   :hidden:
   :caption: Getting Started

   src/getting-started/why-sierra
   src/getting-started/installation
   src/getting-started/trial
   src/getting-started/setup

.. toctree::
   :caption: Core Concepts

   src/concepts/overview
   src/concepts/experimental-design
   src/concepts/pipeline
   src/concepts/dataflow
   src/concepts/run-time-tree
   src/concepts/batch-criteria
   src/concepts/philosophy

.. toctree::
   :caption: User Guide

   src/user-guide/project-structure
   src/user-guide/experiment-templates
   src/user-guide/running-experiments
   src/user-guide/postprocessing
   src/user-guide/product-generation
   src/user-guide/comparator-usage
   src/user-guide/examples
   src/user-guide/variables
   src/user-guide/debugging-and-logging

.. toctree::
   :caption: Tutorials: Using SIERRA

   src/tutorials/project/project
   src/tutorials/project/config/index
   src/tutorials/project/generators
   src/tutorials/project/new-bc
   src/tutorials/project/hooks

.. toctree::
   :caption: Tutorials: Extending SIERRA

   src/tutorials/plugins/engine/index
   src/tutorials/plugins/execenv/index
   src/tutorials/plugins/storage/index
   src/tutorials/plugins/expdef/index
   src/tutorials/plugins/proc/index
   src/tutorials/plugins/prod/index
   src/tutorials/plugins/compare/index
   src/tutorials/plugins/devguide
   src/tutorials/plugins/external

.. toctree::
   :caption: Plugins

   src/plugins/index
   src/plugins/engine/index
   src/plugins/execenv/index
   src/plugins/proc/index
   src/plugins/prod/index
   src/plugins/storage/index
   src/plugins/expdef/index
   src/plugins/compare/index

.. toctree::
   :hidden:

   src/architecture/execution-model
   src/architecture/plugin-system
   src/architecture/deep-dive

.. toctree::
   :caption: Reference

   src/reference/cli
   src/reference/glossary
   src/reference/faq
   src/reference/subprograms
   src/reference/environment
   /autoapi/index

.. toctree::
   :caption: Project

   src/reference/contributing
   src/reference/roadmap
   src/reference/citing
