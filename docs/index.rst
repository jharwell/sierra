.. _main:

===========================================================================
SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)
===========================================================================

SIERRA is a command line tool and plugin framework for:

- Automating scientific research, providing faculties for seamless experiment
  generation, execution, and results processing.

- Accelerating R&D cycles by allowing researchers/developers to focus on the
  “science” aspects: developing new things and designing experiments to test
  them, rather than the engineering aspects (writing scripts, configuring
  environments, etc).

- Maximizing the reproducibility of scientific research, particularly in AI; it
  is designed so that *no* copy-pasting of code/configuration between projects
  is needed.

- Managing the full experiment lifecycle: experiment definition, parameter
  expansion, execution, data collection, post-processing, and artifact
  generation.

It supports a wide range of execution engines/environments, experiment
input/output formats, and generatable products (e.g., graphs) via
plugins. SIERRA supports mix-and-match between all plugin types, subject to
restrictions within the plugins themselves. This is THE most powerful feature of
SIERRA, and makes it very easy to run experiments on different hardware,
targeting different simulators, generating different outputs, etc., all with
little to no configuration changes by the user.

Typical use cases include robotics simulation studies, ML hyperparameter sweeps,
large parameter studies in scientific computing, and automated benchmarking
pipelines. See :ref:`getting-started/why-sierra` for concrete examples.

.. admonition:: New to SIERRA?

   Start with :ref:`concepts/index` to understand the core model, then try the
   :ref:`getting-started/trial` to see it in action — no plugin setup required.

Pipeline Overview
-----------------

SIERRA experiments pass through a five-stage pipeline. Each stage is
independently re-runnable, so you can re-generate graphs without re-running
experiments, and each stage is extensible through the SIERRA plugin system.

.. code-block:: text

   Stage 1 │ Batch Experiment Definition & Instantiation
           │
   Stage 2 │ Experiment Execution
           │
   Stage 3 │ Data Post-Processing
           │
   Stage 4 │ Artifact Production (graphs, videos, reports)
           │
   Stage 5 │ Cross-Batch Comparison

See :ref:`concepts/pipeline` for a detailed walkthrough.

.. dropdown:: Architecture Diagram
   :icon: image

   .. figure:: figures/architecture.png

      SIERRA architecture, organised by pipeline stage (left to right).
      High-level inputs/outputs and active plugins are shown for each stage.
      "..." indicates areas of further extensibility via new plugins.
      "Host machine" indicates the machine SIERRA was invoked on.

Get Started
-----------

.. grid:: 2
   :gutter: 2
   :margin: 4 4 0 0

   .. grid-item-card:: 💡 Key Concepts
      :link: concepts/index
      :link-type: doc
      :class-card: sd-border-1

      Understand experiments, batch criteria, the pipeline, and the runtime
      tree before diving in.

   .. grid-item-card:: 🚀 5-Minute Trial
      :link: getting-started/trial
      :link-type: ref
      :class-card: sd-border-1

      Try SIERRA with a pre-built sample project. No plugin setup required.

   .. grid-item-card:: 📖 Installation & Setup
      :link: getting-started/installation
      :link-type: ref
      :class-card: sd-border-1

      Install SIERRA and integrate it with your own code and experiments.

   .. grid-item-card:: 🔌 Plugins Overview
      :link: plugins/overview
      :link-type: ref
      :class-card: sd-border-1

      Engines, execution environments, storage formats, and more.

.. toctree::
   :hidden:
   :caption: Getting Started

   src/getting-started/index
   src/getting-started/installation
   src/getting-started/quickstart
   src/getting-started/trial
   src/getting-started/why-sierra

.. toctree::
   :caption: Concepts
   :hidden:

   src/concepts/experimental-design
   src/concepts/batch-criteria
   src/concepts/dataflow
   src/concepts/pipeline
   src/concepts/run-time-tree

.. toctree::
   :hidden:
   :caption: User Guide

   src/user-guide/index
   src/user-guide/examples
   src/user-guide/variables
   src/user-guide/running-experiments
   src/user-guide/postprocessing

.. toctree::
   :hidden:
   :caption: Configuring SIERRA Projects

   src/tutorials/project/project.rst
   src/tutorials/project/config/index.rst
   src/tutorials/project/generators.rst
   src/tutorials/project/new-bc.rst
   src/tutorials/project/hooks.rst

.. toctree::
   :hidden:
   :caption: Extending SIERRA With New Plugins

   src/tutorials/plugin/engine/index.rst
   src/tutorials/plugin/execenv/index.rst
   src/tutorials/plugin/storage/index.rst
   src/tutorials/plugin/expdef/index.rst
   src/tutorials/plugin/proc/index.rst
   src/tutorials/plugin/prod/index.rst
   src/tutorials/plugin/compare/index.rst

.. toctree::
   :hidden:
   :caption: Plugins

   src/plugins/overview
   src/plugins/engine/index
   src/plugins/execenv/index
   src/plugins/proc/index
   src/plugins/prod/index
   src/plugins/storage/index
   src/plugins/expdef/index
   src/plugins/compare/index
   src/plugins/developer-guide

.. toctree::
   :caption: Architecture
   :hidden:

   src/architecture/execution-model
   src/architecture/plugin-system
   src/architecture/deep-dive

.. toctree::
   :hidden:
   :caption: Reference

   src/reference/cli
   src/reference/glossary
   src/reference/faq
   src/reference/subprograms
   src/reference/environment
   /autoapi/index

.. toctree::
   :hidden:
   :caption: Project

   src/reference/contributing
   src/reference/roadmap
   src/reference/philosophy
   src/reference/citing

SIERRA In The Wild
==================

SIERRA has been used across a range of published research in swarm robotics,
multi-robot systems, and ODE-based modeling — demonstrating its flexibility
across simulation platforms, scale, and experimental designs.

Papers
------

**Swarm Robotics & Collective Behaviour**

- :xref:`Harwell2021a-metrics` — Introduces performance metrics for swarm
  robotics evaluated across population sizes using SIERRA's batch pipeline.

- :xref:`Harwell2020a-demystify` — Applies SIERRA to demystify emergent
  collective behaviours in foraging swarms.

- :xref:`Harwell2019a-metrics` — Early application of the pipeline to
  scalability and flexibility metrics in multi-robot systems.

- :xref:`White2019-social` — Uses SIERRA to investigate social learning in
  robot swarms.

**Modelling & Task Allocation**

- :xref:`Harwell2022b-ode` — Uses SIERRA to run large-scale ODE-based model
  comparisons against empirical swarm data.

- :xref:`Chen2019-battery` — Employs SIERRA to study battery-aware task
  allocation across experiment batches.

Demos
-----

- :xref:`2022-aamas-demo` — Live demonstration of SIERRA's end-to-end pipeline
  at AAMAS 2022, showing experiment generation through camera-ready graph output.

.. note::

   Using SIERRA in your research? See :ref:`reference/citing` for BibTeX
   entries and version-specific DOI badges for reproducibility.
