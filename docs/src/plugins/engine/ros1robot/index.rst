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
:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` to gather data from
robots (see below). This is helpful in some situations (e.g., simple robots
which can't manage network mounted filesystems).

Requirements
============

#. All data from multiple robots somehow ends up accessible through the
   filesystem on the host machine SIERRA is invoked on, as if the same
   experimental run was locally with a simulator. There are several ways to
   accomplish this:

   - Use SIERRA's ability to configure a "master" node on the host machine, and
     then setup streaming of robot data via ROS messages to this master
     node. Received data is processed as appropriate and then written out to the
     local filesystem so that it is ready for statistics generation during
     stage 3.

     .. IMPORTANT:: If you use this method, then you will need to handle robots
                    starting execution at slightly different times in your code
                    via (a) a start barrier triggered from the master node, or
                    else timestamp the data from robots and marshal it on the
                    master node in some fashion. The :ref:`SIERRA ROSBridge
                    <packages/rosbridge>` provides some support for (a).

   - Mount a shared directory on each robot where it can write its data, and
     then after execution finishes but before your code exits you process the
     per-robot data if needed so it is ready for statistics generation during
     stage 3.

   - Record some/all messages sent and received via one or more ROSbag files,
     and then post-process these files into a set of dataframes which are
     written out to the local filesystem.

   - Record some/all messages sent and received via one or more ROSbag files,
     and use these files directly as a "database" to query during stage 3. This
     would require writing a SIERRA storage plugin (see
     :ref:`tutorials/plugins/storage`).

     .. IMPORTANT:: This method requires that whatever is recorded into the
                    ROSbag file is per-run, not per-robot; that is, if a given
                    data source somehow built from messages sent from multiple
                    robots, those messages need to be processed/averaged/etc and
                    then sent to a dedicated topic to be recorded.

#. :envvar:`ROS_PACKAGE_PATH` is set up properly prior to invoking SIERRA on the
   local machine AND all robots are setup such that it is populated on login
   (e.g., an appropriate ``setup.bash`` is sourced in ``.bashrc``).

#. All robots have :envvar:`ROS_IP` or :envvar:`ROS_HOSTNAME` populated, or
   otherwise can correctly report their address to the ROS master. You can
   verify this by trying to launch a ROS master on each robot: if it launches
   without errors, then these values are setup properly.

Real Robot Considerations
=========================

SIERRA makes the following assumptions about the robots it is allocated each
invocation:

- No robots will die/run out of battery during an :term:`Experimental Run`.

- Password-less ssh is setup to each robot SIERRA is handed to use (can be as a
  different user than the one which is invoking SIERRA on the host machine).

- The robots have static IP addresses, or are always allocated an IP from a
  known set so you can pass the set of IPs to SIERRA to use. This set of IP
  address/hostnames can be explicitly passed to SIERRA via
  :ref:`--nodefile<src/reference/cli:sierra-cli---nodefile>` or implicitly
  passed via :envvar:`SIERRA_NODEFILE`.

- The ROS environment is setup either in the ``.bashrc`` for the robot login
  user.

- ROS1 does not provide a way to say "Run this experiment for X seconds", so
  SIERRA inserts its own timekeeper node into each robot which will exit after X
  seconds and take the roslaunch process with it on each robot and/or the master
  node.

.. _plugins/engine/ros1robot/packages:

OS Packages
===========

.. tab-set::

   .. tab-item:: Ubuntu

      .. code-block::

         apt-get install pssh iputils-ping

   .. tab-item:: OSX

      .. code-block::

         brew install pssh

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

.. sphinx_argparse_cli::
   :module: sierra.plugins.engine.ros1robot.cmdline
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
experiment once generated; you can override with
:ref:`--no-preserve-seeds<src/reference/cli:sierra-cli---preserve-seeds>`.
