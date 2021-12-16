SIERRA is a plugin framework for automating research driven by the scientific
method generally, and for agent-based research specifically. It supports a wide
range of simulated and real-robot platforms, and its deeply modular architecture
makes it easy to customize for the needs of a specific research project. SIERRA
can be used with executable code written in any language. SIERRA's one
restriction is that experimental inputs must be specified in XML in order to be
usable with SIERRA (see :ref:`ln-req` for details).

Pipeline Summary
================

SIERRA automates the following research pipeline:

1. Generating experiment inputs
-------------------------------

Experiments using the scientific method have an independent variable whose
impact on results are measured through a series of trials. SIERRA allows you to
express this as a research query on the command line, and then parses your query
to make changes to a template input file to generate launch commands and
experimental inputs to operationalize it. Switching from targeting platform A
(e.g., ARGoS) to platform B (e.g., ROS+Gazebo) is as easy as changing a a single
command line argument (assuming your code is setup to handle both ARGoS and ROS
environments!). Similarly for switching from running on the local machine to
running on a HPC cluster. SIERRA handles all the "backend" aspects of running
experiments and allows you to focus on the fun parts--the research itself!

2. Running experiments
----------------------

SIERRA currently supports two types of execution environments: simulators and
real robots, which are handled seamlessly with GNU parallel. For simulators,
SIERRA will run multiple experimental runs (simulations) from each experiment in
parallel (exact concurrency dependent on the limits of the computing hardware
and the nature of the experiment). For real robots, SIERRA will execution 1
experimental run at a time.

SIERRA supports multiple HPC environments for execution of experiments in
simulation; see :ref:`ln-exec-env-hpc` for list.

To add additional HPC environments, see :ref:`ln-tutorials-plugin-exec-env`.

SIERRA supports multiple real robot targets for running experiments with
different kinds of real robots; see :ref:`ln-exec-env-robots` for list.

To add additional real robot targets, see :ref:`ln-tutorials-plugin-exec-env`.

3. Experiment Results Processing
--------------------------------

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data (e.g., the number of robots engaged in a given
task over time) for processing. SIERRA can generate various statistics from the
results such as confidence intervals on observed behavior.

4. Deliverable Generation
-------------------------

SIERRA can generate many deliverables from the processed experimental results
automatically (independent of the platform/execution environment!), thus greatly
simplifying reproduction of previous results if you need to tweak a given graph
(for example). SIERRA currently supports generating the following deliverables:

- Camera-ready linegraphs, heatmaps, 3D surfaces, and scatterplots directly from
  averaged/statistically processed experimental data using matplotlib.

- Videos built from frames captured during simulation or real robot operation.

- Videos built from captured experimental output .csv files.

5. Controller/Scenario Comparison
---------------------------------

SIERRA can take pieces from graphs generated in stage 4 and put them on a
single graph to generate camera-ready comparison graphs. It can generate
comparison graphs for:

- Different robot controllers which have all been run in the same scenario.

- A single robot controller which has been run in multiple scenarios.
