.. _plugins:

======================
SIERRA Builtin Plugins
======================

This page details the builtin plugins which currently come with SIERRA.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   platform/index.rst
   exec-env/index.rst
   storage/index.rst
   expdef/index.rst

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

   * - Platform

     - Description

     - Reference

   * - :ref:`ARGoS <plugins/platform/argos>`

     - Simulator for fast simulation of large swarms. Requires ARGoS >=
       3.0.0-beta59.

     - `ARGoS <https://www.argos-sim.info/index.php>`_

   * - :ref:`ROS1+Gazebo <plugins/platform/ros1gazebo>`

     - Using ROS1 with the Gazebo simulator. Requires Gazebo >= 11.9.0, ROS1
       Noetic or later.

     - `ROS1 <https://ros.org>`_ + `Gazebo <https://github.com/gazebosim/gz-sim>`_

   * - :ref:`ROS1+Robot <plugins/platform/ros1robot>`

     - Using ROS1 with a real robot platform of your choice. ROS1 Noetic or
       later is required.

     - `ROS1+Robot <https://ros.org>`_

Execution Environments
======================

SIERRA supports multiple HPC environments for execution of experiments in on HPC
hardware (see :ref:`plugins/exec-env/hpc`) and on real hardware such as robots
(see :ref:`plugins/exec-env/realrobot`). If your desired execution environment
is not listed, see the :ref:`tutorials/plugin/exec-env` for how to add it.

.. list-table::
   :header-rows: 1

   * - Execution Environment

     - Description

     - Reference

   * - :ref:`SLURM <plugins/exec-env/hpc/slurm>`

     - An HPC cluster managed by the SLURM scheduler

     - `SLURM <https://slurm.schedmd.com/documentation.html>`_

   * - :ref:`PBS <plugins/exec-env/hpc/pbs>`

     - An HPC cluster managed by the Torque/MOAB scheduler

     - `Torque/MOAB <https://adaptivecomputing.com/cherry-services/torque-resource-manager>`_

   * - :ref:`Adhoc <plugins/exec-env/hpc/adhoc>`

     - Miscellaneous collection of networked HPC compute nodes or random
       servers; not managed by a scheduler

     -

   * - :ref:`HPC Local <plugins/exec-env/hpc/local>`

     - The SIERRA host machine, e.g., a researcher's laptop

     -

   * - :ref:`Turtlebot3 <plugins/exec-env/realrobot/turtlebot3>`

     - Real turtlebot3 robots

     -

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

   * - Format

     - Description

   * - :ref:`XML <plugins/expdef/xml>`

     - Experimental inputs are defined using XML. See the section on XML in
       :ref:`req/expdef` for restrictions on the contents of XML input files.

   * - :ref:`JSON <plugins/expdef/json>`

     - Experimental inputs are defined using JSON. See the section on JSON in
       :ref:`req/expdef` for restrictions on the contents of JSON input files.


Experimental Output Storage
===========================

SIERRA also supports storage formats for experimental outputs. If the format for
your experimental outputs is not listed, see the :ref:`tutorials/plugin/storage`
for how to add it.


.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Format

     - Scope

   * - :ref:`CSV file <plugins/storage/csv>`

     - Data in .csv format.

   * - PNG file

     - Images emitted/captured by the :term:`Project` and/or :term:`Platform`
       which can be stitched together into videos in stages 4/5.
