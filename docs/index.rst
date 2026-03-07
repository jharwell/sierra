.. _main:

===========================================================================
SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)
===========================================================================

SIERRA is a framework for automating computational processing and scientific
research. It manages the full lifecycle: experiment definition, parameter
expansion, execution, data collection, post-processing, and artifact generation
— with systematic reproducibility built in throughout.

Typical use cases include robotics simulation studies, ML hyperparameter sweeps,
large parameter studies in scientific computing, and automated benchmarking
pipelines. See :ref:`getting-started/why-sierra` for concrete examples.

.. grid:: 2
   :gutter: 2
   :margin: 4 4 0 0

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

   .. grid-item-card:: 💡 Key Concepts
      :link: concepts/index
      :link-type: doc
      :class-card: sd-border-1

      Experiments, batch criteria, the pipeline, and the runtime tree.

   .. grid-item-card:: 🔌 Plugin Reference
      :link: plugins/index
      :link-type: doc
      :class-card: sd-border-1

      Engines, execution environments, storage formats, and more.

.. dropdown:: Pipeline Overview
   :icon: image

   SIERRA experiments pass through a five-stage pipeline. Each stage is
   independently re-runnable, so you can re-generate graphs without
   re-running experiments.

   .. code-block:: text

      Stage 1 │ Experiment Definition & Batch Expansion
              │
      Stage 2 │ Experiment Execution
              │
      Stage 3 │ Data Post-Processing
              │
      Stage 4 │ Artifact Production (graphs, videos, reports)
              │
      Stage 5 │ Cross-Batch Comparison

   Each stage is extensible through the SIERRA plugin system.
   See :doc:`concepts/pipeline` for details.

.. dropdown:: Architecture Diagram
   :icon: image

   .. figure:: figures/architecture.png

      SIERRA architecture, organised by pipeline stage (left to right).
      High-level inputs/outputs and active plugins are shown for each stage.
      "..." indicates areas of further extensibility via new plugins.
      "Host machine" indicates the machine SIERRA was invoked on.

.. toctree::
   :hidden:
   :caption: Getting Started

   src/getting-started/index
   src/getting-started/installation
   src/getting-started/quickstart
   src/getting-started/trial
   src/getting-started/why-sierra

.. toctree::
   :hidden:
   :caption: Concepts

   concepts/index
   concepts/experiments
   concepts/batch-criteria
   concepts/pipeline
   concepts/runtime-tree

.. toctree::
   :hidden:
   :caption: User Guide

   user-guide/index
   user-guide/cli
   user-guide/configuration
   user-guide/running-experiments
   user-guide/postprocessing

.. toctree::
   :hidden:
   :caption: Plugins

   plugins/index
   plugins/plugin-types
   plugins/engine-plugins
   plugins/processor-plugins
   plugins/producer-plugins
   plugins/storage-plugins
   plugins/expdef-plugins
   plugins/developer-guide

.. toctree::
   :hidden:
   :caption: Architecture

   architecture/index
   architecture/system-overview
   architecture/stage3-dataflow
   architecture/stage4-dataflow
   architecture/stage5-dataflow

.. toctree::
   :hidden:
   :caption: Reference

   reference/cli-reference
   reference/configuration-reference
   reference/glossary
   reference/troubleshooting
   /autoapi/index

.. toctree::
   :hidden:
   :caption: Project

   reference/contributing
   reference/roadmap
   reference/philosophy
   reference/faq

Citing SIERRA
=============

If you use SIERRA and find it helpful, please cite:

.. code-block:: bibtex

   @inproceedings{Harwell2022a-SIERRA,
    author    = {Harwell, John and Lowmanstone, London and Gini, Maria},
    title     = {SIERRA: A Modular Framework for Research Automation},
    year      = {2022},
    isbn      = {9781450392136},
    publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
    address   = {Richland, SC},
    booktitle = {Proceedings of the 21st International Conference on Autonomous Agents
                 and Multiagent Systems},
    pages     = {1905--1907},
    numpages  = {3},
    keywords  = {simulation, real robots, research automation, scientific method},
    location  = {Virtual Event, New Zealand},
    series    = {AAMAS '22}
    }

To cite a specific version of SIERRA for reproducibility:

.. |doi| image:: https://zenodo.org/badge/125774567.svg
         :target: https://zenodo.org/badge/latestdoi/125774567

|doi|

SIERRA In The Wild
==================

Papers and demos that have used SIERRA in published research.

Papers
------

- :xref:`Harwell2021a-metrics` — Introduces performance metrics for swarm
  robotics evaluated across population sizes using SIERRA's batch pipeline.

- :xref:`Harwell2022b-ode` — Uses SIERRA to run large-scale ODE-based model
  comparisons against empirical swarm data.

- :xref:`Harwell2020a-demystify` — Applies SIERRA to demystify emergent
  collective behaviours in foraging swarms.

- :xref:`Harwell2019a-metrics` — Early application of the pipeline to
  scalability and flexibility metrics in multi-robot systems.

- :xref:`White2019-social` — Uses SIERRA to investigate social learning in
  robot swarms.

- :xref:`Chen2019-battery` — Employs SIERRA to study battery-aware task
  allocation across experiment batches.

Demos
-----

- :xref:`2022-aamas-demo` — Live demonstration of SIERRA's end-to-end pipeline
  at AAMAS 2022, showing experiment generation through camera-ready graph output.
