.. _ln-sierra-support-matrix:

=====================
SIERRA Support Matrix
=====================

SIERRA supports multiple HPC environments for execution of experiments in on HPC
hardware (see :doc:`/src/exec_env/hpc`) and on real robots (see
:doc:`/src/exec_env/robots`). If your desired platform or execution environment
is not listed, see the :ref:`ln-sierra-tutorials` for how to add it via a
plugin.

.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Execution Environment

     - Description

   * - `SLURM <https://slurm.schedmd.com/documentation.html>`_

     - A cluster managed by the SLURM scheduler

   * - `Torque/MOAB <https://adaptivecomputing.com/cherry-services/torque-resource-manager>`_

     - A cluster managed by the Torque/MOAB scheduler

   * - Adhoc

     - Miscellaneous collection of networked compute nodes; not managed by a
       scheduler

   * - Local

     - The SIERRA host machine,e.g., a researcher's laptop

   * - `Turtlebot3 <https://emanual.robotis.com/docs/en/platform/turtlebot3/overview>`_

     - Real turtlebot3 robots

.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Platform

     - Description

   * - `ARGoS <https://www.argos-sim.info/index.php>`_

     - Simulator for fast simulation of large swarms. Requires ARGoS >=
       3.0.0-beta59.

   * - `ROS1 <https://ros.org)+[Gazebo](https://www.gazebosim.org>`_

     - Using ROS1 with the Gazebo simulator. Requires Gazebo >= 11.9.0, ROS1
       Noetic or later.

   * - `ROS1+Robot <https://ros.org>`_

     - Using ROS1 with a real robot platform of your choice. ROS1 Noetic or
       later is required.

SIERRA also supports multiple output formats for experimental outputs. If the
format for your experimental outputs is not listed, see the `docs
<https://swarm-robotics-sierra.readthedocs.io/en/master/src/tutorials.html>`_
for how to add it via a plugin. SIERRA currently only supports XML experimental
inputs.

.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Experimental Output Format

     - Scope

   * - CSV file

     - Raw experimental outputs, transforming into heatmap images

   * - PNG file

     - Stitching images together into videos

SIERRA supports (mostly) mix-and-match between platforms, execution
environments, experiment input/output formats as shown in its support matrix
below. This is one of the most powerful features of SIERRA!

.. list-table::
   :header-rows: 1
   :widths: 25,25,25,25

   * - Execution Environment
     - Platform

     - Experimental Input Format

     - Experimental Output Format

   * - SLURM

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - Torque/MOAB

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - ADHOC

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - Local

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - ROS1+Turtlebot3

     - ROS1+Gazebo, ROS1+robot

     - XML

     - CSV, PNG
