.. _ln-exec-env-robots:

========================================
Real Robot Execution Environment Plugins
========================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different robots. Supported environments that come with SIERRA are listed on
this page.

These plugins are tested with the following platforms (they may work with other
platforms out of the box too):

- :ref:`ln-platform-plugins-rosrobot`

.. _ln-robot-plugins-rosrobot:

ROS Robot
=========

This is a generic plugin meant to work with most real robots which :term:`ROS`
supports, and as a starting point to derive more specific configuration for a
given robot.

In this execution environment, SIERRA will run experiments spread across
multiple robots using GNU parallel. SIERRA makes the following assumptions about
the robots it is allocated each invocation:

- No robots will die/run out of battery during an :term:`Experimental Run`.
