.. _support-matrix:

================================================
SIERRA Builtin Plugins And Native Support Matrix
================================================

This page details SIERRA's builtin plugins, and how they can/can't be used
together.


Platforms
=========

SIERRA supports multiple :term:`Platforms <Platform>` which researchers can
write code to target, as shown below.  If your desired platform is not listed,
see :ref:`tutorials/plugin/platform` for how to add it.

.. IMPORTANT:: In SIERRA terminology, platform != OS. If a SIERRA platform runs
               on a given OS, then SIERRA supports doing so; if it does not,
               then SIERRA does not. For example, SIERRA does not support
               running ARGoS on windows, because ARGoS does not support windows.


.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Platform

     - Description

   * - `ARGoS <https://www.argos-sim.info/index.php>`_

     - Simulator for fast simulation of large swarms. Requires ARGoS >=
       3.0.0-beta59.

   * - `ROS1 <https://ros.org>`_ + `Gazebo <https://github.com/gazebosim/gz-sim>`_

     - Using ROS1 with the Gazebo simulator. Requires Gazebo >= 11.9.0, ROS1
       Noetic or later.

   * - `ROS1+Robot <https://ros.org>`_

     - Using ROS1 with a real robot platform of your choice. ROS1 Noetic or
       later is required.

Execution Environments
======================

SIERRA supports multiple HPC environments for execution of experiments in on HPC
hardware (see :ref:`plugins/exec-env/hpc`) and on real hardware such as robots
(see :ref:`plugins/exec-env/realrobot`). If your desired execution environment
is not listed, see the :ref:`tutorials/plugin/exec-env` for how to add it via a
plugin.

.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Execution Environment

     - Description

   * - `SLURM <https://slurm.schedmd.com/documentation.html>`_

     - An HPC cluster managed by the SLURM scheduler

   * - `Torque/MOAB <https://adaptivecomputing.com/cherry-services/torque-resource-manager>`_

     - An HPC cluster managed by the Torque/MOAB scheduler

   * - Adhoc

     - Miscellaneous collection of networked HPC compute nodes or random
       servers; not managed by a scheduler

   * - HPC local

     - The SIERRA host machine,e.g., a researcher's laptop

   * - `Turtlebot3 <https://emanual.robotis.com/docs/en/platform/turtlebot3/overview>`_

     - Real turtlebot3 robots

Experiment Definitions
======================

SIERRA also supports multiple formats for experimental inputs, which are used to
define experiments (hence the plugin name). If the format for your experimental
inputs is not listed, see the :ref:`tutorials/plugin/expdef` for how to add it.
Before looking at the specifics below, it will be helpful to be familiar with
the abstract terminology SIERRA uses to describe the different components of the
various markup languages SIERRA supports as inputs, so take a look at
:ref:`tutorials/project/expdef-template/semantics`.

.. list-table::
   :header-rows: 1
   :widths: 10,90

   * - Format

     - Description

   * - XML

     - Experimental inputs are defined using XML. See the section on XML in
       :ref:`req/expdef` for restrictions on the contents of XML input files.

   * - JSON

     - Experimental inputs are defined using JSON. See the section on JSON in
       :ref:`req/expdef` for restrictions on the contents of JSON input files.

Experimental Outputs
====================

SIERRA also supports storage formats for experimental outputs. If the format for
your experimental outputs is not listed, see the :ref:`tutorials/plugin/storage`
for how to add it.


.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Format

     - Scope

   * - CSV file

     - Raw experimental outputs, transforming into heatmap images

   * - PNG file

     - Stitching images together into videos

Native Support Matrix
=====================

SIERRA supports mix-and-match between plugins for platforms, execution
environments, experiment input/output formats, subject to restrictions within
the plugins themselves; that is, from SIERRA's point of view, any plugin from a
given category can be used with any plugin from a different category. In
practice, selection of a given plugin may impose restrictions on the selection
of other plugins. For example, if you select JSON as the experiment definition
format, then you won't functionally be able to use ROS1-based platforms, because
those platforms require XML as input.

This mix-and-match capability is THE most powerful feature of SIERRA (imo), and
makes it very easy to run experiments on different hardware, targeting different
simulators, generating different outputs, etc., all with little to no
configuration changes by the user.


The native support matrix for SIERRA is below; however, it should be *strongly*
emphasized that this matrix only contains end-to-end selections of plugins. The
JSON expdef plugin does not have a matching :term:`Platform` that supports it,
so it doesn't appear here; similarly for some other plugins listed above.

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
