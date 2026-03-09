.. _plugins/engine:

=================
Engine (--engine)
=================

SIERRA supports a number of :term:`engines <Engine>`, all of which can be
used transparently for running experiments; well, transparent from SIERRA's
point of view; you probably will still have to make code modifications to switch
between engines.

.. toctree::
   :maxdepth: 2

   argos/index
   ros1gazebo/index
   ros1robot/index


Additional engines can be supported via :ref:`tutorials/plugins/engine`.

Common ROS1 Functionality
=========================

.. sphinx_argparse_cli::
   :module: sierra.core.ros1.cmdline
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli
