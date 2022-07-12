SIERRA is a plugin framework for automating research driven by the scientific
method generally, and for agent-based research specifically. It supports a wide
range of platforms, and its deeply modular architecture makes it easy to
customize for the needs of a specific research project. SIERRA can be used with
executable code written in any language. Not sure if SIERRA makes sense for your
use case? See :doc:`/src/requirements`, and an overview of its capabilities
below.

SIERRA Pipeline Automation
==========================

1. Generating Experiment Inputs
-------------------------------

Experiments using the scientific method have an independent variable whose
impact on results are measured through a series of trials. SIERRA allows you to
express this as a research query on the command line, and then parses your query
to make changes to a template input file to generate launch commands and
experimental inputs to operationalize it. Switching from targeting platform A
(e.g., ARGoS) to platform B (e.g., ROS1+Gazebo) is as easy as changing a single
command line argument (assuming your code is setup to handle both ARGoS and ROS
environments!). SIERRA handles the "backend" aspects of defining experimental
inputs allowing you to focus on their *content*, rather than the mechanics of
how to turn the content into something that can be executed.

2. Running Experiments
----------------------

SIERRA currently supports two types of execution environments: simulators and
real robots, which are handled seamlessly with GNU parallel. For simulators,
SIERRA will run multiple experimental runs (simulations) from each experiment in
parallel (exact concurrency dependent on the limits of the computing hardware
and the nature of the experiment). For real robots, SIERRA will execution 1
experimental run at a time. Similar to stage 1, switching between execution
environments is as easy as changing a s single command line argument (assuming
your code is setup to handle the environment you are switching to).

SIERRA supports multiple HPC environments for execution of experiments in
simulation (see :doc:`/src/exec_env/hpc`) and on real robots
(see :doc:`/src/exec_env/robots`):

.. list-table:: Supported Execution Environments
   :widths: 25 75
   :header-rows: 1

   * - Environment

     - Supported Platforms

   * - SLURM: `<https://slurm.schedmd.com/documentation.html>`_

     - ARGoS, ROS1+Gazebo

   * - Torque/MOAB: `<https://adaptivecomputing.com/cherry-services/torque-resource-manager/>`_

     - ARGoS, ROS1+Gazebo

   * - ADHOC (suitable for a miscellaneous collection of networked compute nodes
       for a research group)

     - ARGoS, ROS1+Gazebo

   * - Local machine (for testing)

     - ARGoS, ROS1+Gazebo

   * - ROS1+Turtlebot3: `<https://emanual.robotis.com/docs/en/platform/turtlebot3/overview>`_

     - ROS1+Gazebo, ROS1+robot

To add additional HPC or real robot execution environments, see
:doc:`/src/tutorials/plugin/exec_env_plugin`.

3. Experiment Results Processing
--------------------------------

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data (e.g., the number of robots engaged in a given
task over time) for processing. SIERRA can generate various statistics from the
results such as confidence intervals on observed behavior. What statistics are
generated and for which experimental outputs is configurable via YAML.

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

For some examples, see the "Generating Deliverables" section of
:xref:`2022-aamas-demo`.


5. Deliverable Comparison
-------------------------

SIERRA can take pieces from graphs generated in stage 4 and put them on a single
graph to generate camera ready comparison graphs. It can generate comparison
graphs for:

- Different agent control algorithms which have all been run in the same
  scenario.

- A single agent control algorithm which has been run in multiple scenarios.
