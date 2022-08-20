.. _ln-sierra-platform-plugins-ros1robot:

===================
ROS1+Robot Platform
===================

This platform can be selected via ``--platform=platform.ros1robot``.


This is the platform on which SIERRA will run experiments using :term:`ROS1` on
a real robot of your choice. To use this platform, you must setup the
:ref:`SIERRA ROSBridge <ln-sierra-packages-rosbridge>`.  This is a generic
platform meant to work with most real robots which :term:`ROS1` supports, and as
a starting point to derive more specific platform configuration for a given
robot (if needed). For all execution environments using this platform (see
:ref:`ln-sierra-exec-env-robot` for examples), SIERRA will run experiments
spread across multiple robots using GNU parallel.

SIERRA designates the host machine as the ROS master, and allows you to
(optionally) specify configuration for running one or more nodes on it in the
``--template-input-file`` to gather data from robots (see below). This is
helpful in some situations (e.g., simple robots which can't manage network
mounted filesystems).

.. toctree::

   batch_criteria.rst

Environment Variables
=====================

This platform ignores :envvar:`SIERRA_ARCH`.

Random Seeding For Reproducibility
==================================

ROS do not provide a random number generator manager, but SIERRA provides random
seeds to each :term:`Experimental Run` which :term:`Project` code should use to
manage random number generation, if needed, to maximize reproducability. See
:ref:`ln-sierra-tutorials-project-template-input-file` and
:ref:`ln-sierra-req-exp` for details on the format of the provided seed. By
default SIERRA does not overwrite its generated random seeds for each experiment
once generated; you can override with ``--no-preserve-seeds``.

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
  :ref:`ln-sierra-usage-cli`) or implicitly passed via
  :envvar:`SIERRA_NODEFILE`.

- The ROS environment is setup either in the .bashrc for the robot login user,
  or the necessary bits are in a script which SIERRA sources on login to each
  robot (this is a configuration parameter--see
  :ref:`ln-sierra-tutorials-project-main-config`).

- ROS does not provide a way to say "Run this experiment for X seconds", so
  SIERRA inserts its own timekeeper node into each robot which will exit after X
  seconds and take the roslaunch process with it on each robot and/or the master
  node.

See also :ref:`ln-sierra-req-code-ros1robot`.
