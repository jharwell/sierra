.. _plugins/engine/ros1robot:

===================
ROS1+Robot Engine
===================


Using ROS1 with a real robot engine of your choice. ROS1 Noetic or
later is required.

This engine can be selected via ``--engine=engine.ros1robot``.

This is the engine on which SIERRA will run experiments using :term:`ROS1` on
a real robot of your choice. To use this engine, you must setup the
:ref:`SIERRA ROSBridge <packages/rosbridge>`.  This is a generic engine meant
to work with most real robots which :term:`ROS1` supports, and as a starting
point to derive more specific engine configuration for a given robot (if
needed). For all execution environments using this engine (see
:ref:`plugins/execenv/realrobot` for examples), SIERRA will run experiments
spread across multiple robots using GNU parallel.

SIERRA designates the host machine as the ROS master, and allows you to
(optionally) specify configuration for running one or more nodes on it in the
``--expdef-template`` to gather data from robots (see below). This is
helpful in some situations (e.g., simple robots which can't manage network
mounted filesystems).

.. _plugins/engine/ros1robot/packages:

OS Packages
===========

.. tabs::

      .. group-tab:: Ubuntu

         Install the following required packages with ``apt install``:

         - ``pssh``
         - ``iputils-ping``

      .. group-tab:: OSX

         Install the following required packages with ``brew install``:

         - ``pssh``

Note that you also have to install ROS1.

.. _plugins/engine/ros1robot/usage:

Usage
=====

Batch Criteria
--------------

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

.. toctree::
   :maxdepth: 1

   bc/population-size.rst

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/engine/ros1robot/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra-cli



Environment Variables
=====================

This engine ignores :envvar:`SIERRA_ARCH`. This engine uses
:envvar:`SIERRA_NODEFILE`.

Random Seeding For Reproducibility
==================================

ROS do not provide a random number generator manager, but SIERRA provides random
seeds to each :term:`Experimental Run` which :term:`Project` code should use to
manage random number generation, if needed, to maximize reproducability.

See:

- :ref:`plugins/expdef`

- :ref:`plugins/engine/ros1gazebo`

for details on the format of the provided seed.

By default SIERRA does not overwrite its generated random seeds for each
experiment once generated; you can override with ``--no-preserve-seeds``.

Real Robot Considerations
=========================

SIERRA makes the following assumptions about the robots it is allocated each
invocation:

- No robots will die/run out of battery during an :term:`Experimental Run`.

- Password-less ssh is setup to each robot SIERRA is handed to use (can be as a
  different user than the one which is invoking SIERRA on the host machine).

- The robots have static IP addresses, or are always allocated an IP from a
  known set so you can pass the set of IPs to SIERRA to use. This set of IP
  address/hostnames can be explicitly passed to SIERRA via cmdline (see
  :ref:`usage/cli`) or implicitly passed via
  :envvar:`SIERRA_NODEFILE`.

- The ROS environment is setup either in the ``.bashrc`` for the robot login
  user.

- ROS does not provide a way to say "Run this experiment for X seconds", so
  SIERRA inserts its own timekeeper node into each robot which will exit after X
  seconds and take the roslaunch process with it on each robot and/or the master
  node.

See also the section on ROS1+robot in :ref:`req/engine`.
