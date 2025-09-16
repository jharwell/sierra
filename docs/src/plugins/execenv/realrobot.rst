.. _plugins/execenv/realrobot:

========================================
Real Robot Execution Environment Plugins
========================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different robots. Supported environments that come with SIERRA are listed on
this page.

These plugins are tested with the following engines (they may work with other
engines out of the box too):

- :ref:`plugins/engine/ros1robot`

.. _plugins/execenv/realrobot/turtlebot3:

Turtlebot3
==========

This real robot plugin can be selected via ``--execenv=robot.turtlebot3``.

In this execution environment, SIERRA will run experiments spread across
multiple turtlebots using GNU parallel.

The following environmental variables are used in the turtlebot3 environment:

.. list-table::
   :widths: 25 25 25 25
   :header-rows: 1

   * - Environment variable

     - SIERRA context

     - Command line override

     - Notes

   * - :envvar:`SIERRA_NODEFILE`

     - Contains hostnames/IP address of all robots SIERRA can use. Same
       format as GNU parallel ``--sshloginfile``.

     - ``--nodefile``

     - :envvar:`SIERRA_NODEFILE` must be defined or ``--nodefile`` passed. If
       neither is true, SIERRA will throw an error.
