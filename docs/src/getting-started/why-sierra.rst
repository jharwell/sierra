.. SPDX-License-Identifier:  MIT

.. _getting-started/why-sierra:

===============
Why Use SIERRA?
===============

This page describes some of the problems SIERRA was designed to solve. If any
of these scenarios sound familiar, there is a strong chance SIERRA could help
you. See :doc:`installation` to get started.

Use Case #1: Alice The Robotics Researcher
==========================================

Alice is a researcher at a large university who has developed a new distributed
task allocation algorithm :math:`\alpha` for use in a foraging task where robots
must coordinate to find objects of interest in an unknown environment and bring
them to a central location. Alice wants to investigate:

- How well it scales with the number of robots, specifically whether it remains
  efficient with up to 1000 robots across several different scenarios.

- How robust it is with respect to sensor and actuator noise.

- How it compares to two similar state-of-the-art algorithms:
  :math:`\beta` and :math:`\gamma`.

Alice is faced with the following heterogeneity matrix in addition to the
technical challenges of the AI elements themselves:

.. list-table::
   :header-rows: 1
   :widths: 25 25 25

   * - Algorithm
     - Contains stochasticity?
     - Outputs data in?

   * - :math:`\alpha`
     - Yes
     - CSV, rosbag

   * - :math:`\beta`
     - Yes
     - CSV, rosbag

   * - :math:`\gamma`
     - No
     - rosbag

Alice is familiar with ROS and wants to use it with large-scale simulated and
small-scale real-robot experiments with TurtleBots. For real robots she is
unsure what data she will ultimately need, so she wants to capture all ROS
messages to avoid redoing experiments later. She has access to a large
SLURM-managed cluster and prefers to develop code on her laptop.

**How SIERRA helps:** SIERRA's :ref:`plugins/engine` and :ref:`plugins/execenv`
plugins let Alice use the same project plugin and batch criteria definitions
whether she is running on her laptop or the SLURM cluster — she only changes
:ref:`--execenv<src/reference/cli:sierra---execenv>`. The :ref:`plugins/storage` system
handles rosbag and CSV outputs uniformly, and SIERRA's stochastic run management
(:ref:`--n-runs<src/reference/cli:sierra---n-runs>`) handles the multiple seeds needed for
:math:`\alpha` and :math:`\beta` automatically. Stage 5 comparative graphs let
her produce camera-ready :math:`\alpha` vs :math:`\beta` vs :math:`\gamma`
comparisons directly.

Use Case #2: Alice The Contagion Modeler
========================================

Alice has teamed with Bob, a biologist, to model the spread of contagion among
agents in a population and how it affects their individual and collective
abilities to complete tasks. She believes her :math:`\alpha` algorithm can be
reused in this context, but Bob is not convinced. Bob has selected two
multi-agent models from recent papers — :math:`\delta`, originally developed in
NetLogo for modelling disease transmission in animals, and :math:`\epsilon`,
developed in ARGoS to model the effects of radiation on robots — and wants Alice
to compare :math:`\alpha` against them.

.. list-table::
   :header-rows: 1
   :widths: 25 25 25

   * - Algorithm
     - Can run on?
     - Input requirements?

   * - :math:`\alpha`
     - ROS/Gazebo
     - XML

   * - :math:`\delta`
     - NetLogo
     - NetLogo

   * - :math:`\epsilon`
     - ARGoS
     - XML

Bob is interested in how contagion spread varies with agent velocity and
population size. He needs succinct, comprehensive visual representations for a
presentation, including per-algorithm visual comparisons of the model as it
runs. Alice does not have access to HPC resources for this project, but has a
handful of servers in her lab.

**How SIERRA helps:** SIERRA's plugin architecture lets Alice write one set of
batch criteria definitions (population size, agent velocity) and run them
against ARGoS, ROS1+Gazebo, and — once a NetLogo engine plugin exists — NetLogo,
by changing only :ref:`--engine<src/reference/cli:sierra---engine>`. The
:ref:`plugins/execenv` ``hpc.adhoc`` plugin covers Alice's lab servers without
needing a formal scheduler. Stage 4's rendering plugin produces the
per-algorithm visual comparisons Bob needs, all from a single SIERRA invocation.

Use Case #3: Bob The Industry Modeling & Sim Developer
======================================================

Bob works at an industry company extending a custom in-house multi-agent
simulator. The simulator currently takes JSON as input, with a planned migration
to YAML. Simulations are deterministic, and outputs are currently processed with
ad-hoc Python scripts. Management wants automated parameter space exploration
(noise thresholds, speeds, minimum distances) and automated deliverable
generation — but using interactive webplots rather than static graphs.

Some projects are classified, so any integration with open-source tools must
keep the proprietary code strictly separate.

**How SIERRA helps:** SIERRA's :ref:`plugins/expdef` system supports JSON and
YAML natively, so migrating the input format requires only changing
``--expdef``, not rewriting experiment definitions. The :ref:`plugins/prod`
plugin system is extensible: Bob's team can write a custom
:ref:`--prod<src/reference/cli:sierra---prod>` plugin that generates interactive webplots
while the rest of the pipeline remains unchanged. Because SIERRA's project
plugins live in a separate repository from SIERRA itself, classified projects
can be kept entirely private.

Use Case #4: Candace The ML Engineer
=====================================

Candace is an ML engineer training models locally on her laptop but hitting
computational bottlenecks when sweeping parameter and hyperparameter
combinations. Her model is configured via YAML. It is deterministic, but she
wants to explore the effect of randomly dropping elements from the input
dataset. Her company uses AWS for large-scale compute, and like Bob, she works
on classified projects that must stay separate from any open-source tooling.

**How SIERRA helps:** SIERRA treats YAML-configured ML models the same way it
treats simulators. Stage 1 generates a batch of input files varying the
hyperparameters Candace cares about, stage 2 runs them, and stages 3–4 produce
graphs showing how each combination affected the learned model. The
:ref:`plugins/execenv` ``hpc.awsbatch`` plugin handles AWS Batch submission
transparently. And just as with Bob's use case, Candace's project plugin stays
in a private repository, entirely separate from SIERRA's open-source codebase.
