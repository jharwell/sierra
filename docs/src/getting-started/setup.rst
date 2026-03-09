.. _getting-started/setup:

===========================
Setting Up Your Own Project
===========================

This page walks you through connecting SIERRA to your own code. By the end you
will have a working ``sierra-cli`` invocation against your own simulator or
algorithm.

.. note::

   Complete :doc:`installation` and (optionally) the :doc:`trial` before
   starting here. The trial is the fastest way to build intuition for the
   workflow before applying it to your own project.

   Browsing the :doc:`../reference/glossary` first is also worth the few
   minutes it takes — SIERRA uses several terms precisely, and recognising them
   will make the steps below easier to follow.

Step 1: Check Requirements
==========================

Before writing any plugin code, verify your setup meets SIERRA's requirements
for experimental design and output format:

- :ref:`getting-started/installation/os` — supported operating systems.
- :ref:`user-guide/running-experiments` — what SIERRA assumes about how your
  code outputs data and how experimental runs are launched.

If your setup doesn't meet a requirement, the requirements page explains which
plugin to write to accommodate it.

Step 2: Create a Project Plugin
================================

A :term:`Project` plugin is the bridge between your code and SIERRA. It tells
SIERRA how to translate command-line arguments into experiment configuration,
where to find your controller, and how to interpret
``--scenario``.

Follow :ref:`tutorials/project/project` to create your project plugin. The
sample projects at :xref:`SIERRA_SAMPLE_PROJECT` provide working examples for
every built-in engine and are a useful reference alongside that tutorial.

.. note::

   Projects are not portable across :term:`Engines <Engine>`. If you want to
   run the same code on both ARGoS and ROS1+Gazebo, you will need two project
   plugins — but they can share Python code via imports.

Step 3: Invoke SIERRA
=====================

Once your project plugin exists, you are ready to run SIERRA. Every invocation
needs at least four things:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Argument
     - Purpose

   * - :ref:`--engine<src/reference/cli:sierra-cli---engine>`
     - The simulation or robot execution engine to use. See
       :ref:`plugins/engine` for available options.

   * - :ref:`--execenv<src/reference/cli:sierra-cli---execenv>`
     - Where and how to run experiments (local, SLURM, AWS Batch, etc.). See
       :ref:`plugins/execenv` for available plugins.

   * - :ref:`--batch-criteria<src/reference/cli:sierra-cli---batch-criteria>`
     - The independent variable you want to vary across the batch. See
       :ref:`tutorials/project/new-bc` if you need to define a new one.

   * - :ref:`--project<src/reference/cli:sierra-cli---project>`
     - The project plugin to load (the one you created in Step 2).

The remaining required arguments fill in the specifics:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Argument
     - Purpose

   * - :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`
     - The template input file for your experiment. See :ref:`plugins/expdef`
       for supported formats and requirements.

   * - :ref:`--n-runs<src/reference/cli:sierra-cli---n-runs>`
     - How many independent runs to execute per experiment. Used to average
       over stochasticity; set to 1 for deterministic simulations.

   * - ``--controller``
     - The controller or algorithm to run. Project-dependent; see
       :ref:`tutorials/project/config` for how this drives experiment
       generation declaratively.

   * - ``--scenario``
     - Arena size, environment type, and other contextual settings.
       Project-dependent; can also be derived from the batch criteria.

   * - :ref:`--sierra-root<src/reference/cli:sierra-cli---sierra-root>`
     - Root directory where all SIERRA outputs will be written.

.. dropdown:: Environment variables to set before invoking
   :icon: terminal

   Configure the shell you will run ``sierra-cli`` from:

   - ``PYTHONPATH`` — set this if Python cannot find the SIERRA package or your
     project plugin after installation.
   - :envvar:`SIERRA_PLUGIN_PATH` — set this to the directory containing your
     project plugin so SIERRA can find it at runtime.

   Engine-specific variables (e.g., :envvar:`ARGOS_PLUGIN_PATH`,
   :envvar:`ROS_PACKAGE_PATH`) are documented on each engine's plugin page.
   See :ref:`plugins/engine`.

If you pass an obviously incorrect combination of arguments, SIERRA will refuse
to start. For subtler errors it will abort via an assertion before doing
anything substantial.

See :ref:`user-guide/examples` for annotated invocation examples, and
:ref:`reference/faq` if you get stuck.

Step 4: Understand the Output
==============================

SIERRA creates a sizeable directory structure under ``--sierra-root`` during a
run. Read :doc:`../user-guide/running-experiments` before your first real
invocation — understanding the structure upfront will save a lot of filesystem
spelunking later.

The key principle: **SIERRA never deletes your data.** If a directory that
SIERRA needs to create already exists, it will abort during stages 1–2 rather
than risk overwriting experimental results. Pass
:ref:`--exp-overwrite<src/reference/cli:sierra-cli---exp-overwrite>` to override
this when you deliberately want to rerun. See :ref:`conceptsphilosophy` for the
reasoning behind this behaviour.

Next Steps
==========

- **Explore what you can vary** — :doc:`../concepts/batch-criteria` explains
  the batch criteria system in depth.
- **Re-run individual stages** — :doc:`../concepts/pipeline` explains how to
  run only stages {3,4} to regenerate graphs without re-running experiments.
- **Add more batch criteria** — :ref:`tutorials/project/new-bc` shows how to
  define new variables to sweep over.
- **Scale to HPC or cloud** — :ref:`plugins/execenv` covers SLURM, PBS, AWS
  Batch, and ad-hoc cluster configurations.
