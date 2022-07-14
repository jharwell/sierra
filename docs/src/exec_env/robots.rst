.. _ln-sierra-exec-env-robots:

========================================
Real Robot Execution Environment Plugins
========================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different robots. Supported environments that come with SIERRA are listed on
this page.

These plugins are tested with the following platforms (they may work with other
platforms out of the box too):

- :ref:`ln-sierra-platform-plugins-ros1robot`

.. _ln-sierra-robot-plugins-turtlebot3:

Turtlebot3
==========

This real robot plugin can be selected via ``--exec-env=robots.turtlebot3``.

In this execution environment, SIERRA will run experiments spread across
multiple turtlebots using GNU parallel.

The following environmental variables may be used:

- :envvar:`SIERRA_NODEFILE`
