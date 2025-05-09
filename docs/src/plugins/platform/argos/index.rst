.. _plugins/platform/argos:

==============
ARGoS Platform
==============

`<https://www.argos-sim.info/index.php>`_. Requires ARGoS >= 3.0.0-beta59.

This platform can be selected via ``--platform=platform.argos``.

This is the default platform on which SIERRA will run experiments, and uses the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.

.. toctree::

   batch_criteria.rst

Environment Variables
=====================

This platform respects :envvar:`SIERRA_ARCH`.

Execution Environments
======================

The # threads per :term:`experimental run <Experimental Run>` is defined with
``--physics-n-engines``, and that option is required for the
``--exec-env=hpc.local`` environment during stage 1.

Random Seeding For Reproducibility
==================================

ARGoS provides its own random seed mechanism under ``<experiment>`` which SIERRA
uses to seed each experiment. :term:`Project` code should use this mechanism or
a similar random seed generator manager seeded by the same value so that
experiments can be reproduced exactly. By default SIERRA does not overwrite its
generated random seeds for each experiment once generated; you can override with
``--no-preserve-seeds``.


Platforms
=========


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
