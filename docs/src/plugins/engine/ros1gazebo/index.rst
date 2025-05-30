.. _plugins/engine/ros1gazebo:

====================
ROS1+Gazebo Engine
====================

`ROS1 <https://ros.org>`_ + `Gazebo <https://github.com/gazebosim/gz-sim>`_.

This engine can be selected via ``--engine=engine.ros1gazebo``.

This is the engine on which SIERRA will run experiments using the
:term:`Gazebo` simulator and :term:`ROS1`. It cannot be used to run
experiments on real robots. To use this engine, you must setup the
:ref:`SIERRA ROSBridge <packages/rosbridge>`.

Worlds within ROS1+Gazebo are infinite from the perspective of physics engines,
even though a finite area shows up in rendering. So, to place robots randomly in
the arena at the start of simulation across :term:`Experimental Runs
<Experimental Run>` (if you want to do that) "dimensions" for a given world must
be specified as part of the ``--scenario`` argument. If you don't specify
dimensions as part of the ``--scenario`` argument, then you need to supply a
list of valid robot positions via ``--robot-positions`` which SIERRA will choose
from randomly for each robot.


.. toctree::

   batch_criteria.rst

Environment Variables
=====================

This engine ignores :envvar:`SIERRA_ARCH`.

Random Seeding For Reproducibility
==================================

ROS1+Gazebo do not provide a random number generator manager, but SIERRA
provides random seeds to each :term:`Experimental Run` which :term:`Project`
code should use to manage random number generation, if needed, to maximize
reproducability.  By default SIERRA does not overwrite its generated random seeds
for each experiment once generated; you can override with
``--no-preserve-seeds``.
