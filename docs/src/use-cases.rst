.. SPDX-License-Identifier:  MIT

.. _use-cases:

===============
Why Use SIERRA?
===============

This page details some use cases for which SIERRA was designed; if aspects of
any sound familiar, then there is a strong change SIERRA could help you! See
:ref:`startup` to get going.

Use Case #1: Alice The Robotics Researcher
==========================================

Alice is a researcher at a large university that has developed a new distributed
task allocation algorithm :math:`\alpha` for use in a foraging task where
robots must coordinate to find objects of interest in an unknown environment and
bring them to a central location. Alice wants to implement her algorithm so she
can investigate:

- How well it scales with the number of robots, specifically if it remains
  efficient with up to 1000 robots in several different scenarios.

- How robust it is with respect to sensor and actuator noise.

- How it compares to other similar state of the art algorithms on a foraging
  task: :math:`\beta,\gamma`.

Alice is faced with the following heterogeneity matrix which she has to deal
with to answer her research queries, *in addition to the technical challenges of
the AI elements themselves*:

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

Alice is familiar with ROS, and wants to use it with large scale simulated and
small scale real-robot experiments with TurtleBots. However, for real robots she
is unsure what data she will ultimately need, and wants to capture all ROS
messages, to avoid having to redo experiments later.  She has access to a large
SLURM-managed cluster, and prefers to develop code on her laptop.

Use Case #2: Alice The Contagion Modeler
========================================

Alice has teamed with Bob, a biologist, to model the spread of contagion among
agents in a population, and how that affects their individual and collective
abilities to do tasks. She believes her :math:`\alpha` algorithm can be reused
in this context. However, Bob is not convinced and has selected several
multi-agent models from recent papers: :math:`\delta,\epsilon`, and wants
Alice to compare :math:`\alpha` to them. :math:`\delta` was originally
developed in NetLogo, for modeling disease transmission in
animals. :math:`\epsilon` was originally developed for ARGoS to model the
effects of radiation on robots.

Alice is faced with the following heterogeneity matrix which she must deal with
with to answer her research query, *in addition to the technical challenges of
the AI elements themselves*:

.. list-table::
   :header-rows: 1
   :widths: 25 25 25

   * - Algorithm

     - Can Run On?

     - Input Requirements?

   * - :math:`\alpha`

     - ROS/Gazebo

     - XML

   * - :math:`\delta`

     - NetLogo

     - NetLogo

   * - :math:`\epsilon`

     -  ARGoS

     -  XML

Bob is interested in how the rate of contagion spread varies with agent velocity
and population size. Bob needs to prepare succinct, comprehensive visual
representations of the results of this research queries for a a presentation,
including visual comparisons of the multi-agent model as it runs for each
algorithm. He will give Alice a range of parameter values to test for each
algorithm based on his ecological knowledge, and rely on Alice to perform the
experiments. For this project, Alice does not have access to HPC resources, but
does have a handful of servers in her lab which she can use.

Use Case #3: Bob The Industry Modeling & Sim Developer
======================================================

Bob works at an industry company extending a custom in-house multi-agent
simulator. This simulator takes JSON as input, but the plan eventually is to
migrate to YAML. Simulations do not contain randomness, and outputs are
processed with python scripts in an ad-hoc fashion. There is a strong push from
management to use the metrics generated from processing simulation outputs as a
driver for the software team to determine how they should focus their
development efforts. So, automated exploration of parameter space exploration
for things like noise thresholds, speeds, min distances, etc., is of paramount
importance, along with automated deliverable generation. However, instead of
static graphs, the desired deliverables are interactive webplots.

In addition, some projects that this simulator is used on/will be used on are
classified, so any integrations with any open source software tools need to be
able to be kept separate from the open source tool itself.
